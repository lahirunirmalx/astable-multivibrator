#!/usr/bin/env python3
"""Build hybrid THT+SMD footprints into lib_external/Hybrid.pretty via the pcbnew API.

Rule: every SMD land that shares a pad number with a THT pad physically overlaps
that THT pad's annular ring (KiCad treats same-number pads as one net node; a
disjoint same-number land would be left floating by the router).

Footprints:
  R_Hybrid_0805_P2.54_Vertical   axial 0207 vertical (P2.54) + 0805 land pair above the row
  LED_Hybrid_0805_D3.0mm         3 mm THT LED (P2.54)    + 0805 LED lands above the row
  CP_Hybrid_0805_D5.0mm_P2.50mm  radial 5 mm electrolytic + 0805 ceramic lands above the row
  Q_NPN_Hybrid_TO-92_SOT-23      TO-92 inline (1.27) + SOT-23, 5 pads:
                                   1=E_smd 2=B(shared) 3=C_smd 4=THT left 5=THT right
Run with the system python3 that has pcbnew (KiCad 9).
"""
import sys
from pathlib import Path
import pcbnew

FP_ROOT = Path("/usr/share/kicad/footprints")
OUT_LIB = Path(__file__).resolve().parents[1] / "lib" / "Hybrid.pretty"   # project library, kicad/lib
MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def load(lib, name):
    fp = pcbnew.FootprintLoad(str(FP_ROOT / f"{lib}.pretty"), name)
    assert fp, f"cannot load {lib}:{name}"
    return fp


BOARD = pcbnew.BOARD()


def new_fp(name, desc, tags, attr):
    fp = pcbnew.FOOTPRINT(BOARD)
    fp.SetFPID(pcbnew.LIB_ID("Hybrid", name))
    fp.SetLibDescription(desc)
    fp.SetKeywords(tags)
    fp.SetAttributes(attr)
    fp.Reference().SetText("REF**")
    fp.Reference().SetPosition(V(0, -4.0))
    fp.Value().SetText(name)
    fp.Value().SetPosition(V(0, 4.0))
    fp.Value().SetLayer(pcbnew.F_Fab)
    return fp


def copy_graphics(src, dst, dx, dy, layers=None, scale_courtyard=False):
    """Copy drawings (lines/circles/arcs/polys) from src into dst, shifted (fresh objects)."""
    off = V(dx, dy)
    for item in src.GraphicalItems():
        if not isinstance(item, pcbnew.PCB_SHAPE):
            continue
        if layers and item.GetLayer() not in layers:
            continue
        s = pcbnew.PCB_SHAPE(dst)
        s.SetShape(item.GetShape())
        s.SetLayer(item.GetLayer())
        s.SetWidth(item.GetWidth())
        s.SetFilled(item.IsFilled())
        sh = item.GetShape()
        if sh == pcbnew.SHAPE_T_POLY:
            poly = pcbnew.SHAPE_POLY_SET(item.GetPolyShape())
            poly.Move(off)
            s.SetPolyShape(poly)
        elif sh == pcbnew.SHAPE_T_ARC:
            s.SetArcGeometry(item.GetStart() + off, item.GetArcMid() + off, item.GetEnd() + off)
        else:
            s.SetStart(item.GetStart() + off)
            s.SetEnd(item.GetEnd() + off)
            if sh == pcbnew.SHAPE_T_CIRCLE:
                s.SetCenter(item.GetCenter() + off)
                s.SetRadius(item.GetRadius())
        dst.Add(s)


def copy_pads(src, dst, dx, dy, renumber=None, keep=None):
    off = V(dx, dy)
    for p in src.Pads():
        n = p.GetNumber()
        if keep and n not in keep:
            continue
        q = pcbnew.PAD(dst)
        q.SetNumber(renumber.get(n, n) if renumber else n)
        q.SetAttribute(p.GetAttribute())
        q.SetShape(p.GetShape())
        if p.GetShape() == pcbnew.PAD_SHAPE_ROUNDRECT:
            q.SetRoundRectRadiusRatio(p.GetRoundRectRadiusRatio())
        q.SetSize(p.GetSize())
        q.SetDrillSize(p.GetDrillSize())
        q.SetDrillShape(p.GetDrillShape())
        q.SetLayerSet(p.GetLayerSet())
        q.SetPosition(p.GetPosition() + off)
        dst.Add(q)


def add_smd_pad(fp, number, x, y, w, h, rr=0.25):
    p = pcbnew.PAD(fp)
    p.SetNumber(number)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
    p.SetRoundRectRadiusRatio(rr)
    p.SetSize(V(w, h))
    p.SetPosition(V(x, y))
    p.SetLayerSet(_smd_layers())
    fp.Add(p)
    return p


def _smd_layers():
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.F_Paste)
    ls.AddLayer(pcbnew.F_Mask)
    return ls


def add_tht_pad(fp, number, x, y, w, h, drill, shape=pcbnew.PAD_SHAPE_CIRCLE, offset=(0, 0)):
    p = pcbnew.PAD(fp)
    p.SetNumber(number)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetShape(shape)
    p.SetSize(V(w, h))
    p.SetDrillSize(V(drill, drill))
    p.SetPosition(V(x, y))
    if offset != (0, 0):
        p.SetOffset(V(*offset))
    ls = pcbnew.LSET.AllCuMask()
    ls.AddLayer(pcbnew.F_Mask)
    ls.AddLayer(pcbnew.B_Mask)
    p.SetLayerSet(ls)
    fp.Add(p)
    return p


def add_rect(fp, layer, x0, y0, x1, y1, width):
    s = pcbnew.PCB_SHAPE(fp)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(V(x0, y0))
    s.SetEnd(V(x1, y1))
    s.SetLayer(layer)
    s.SetWidth(MM(width))
    fp.Add(s)


def add_line(fp, layer, x0, y0, x1, y1, width):
    s = pcbnew.PCB_SHAPE(fp)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x0, y0))
    s.SetEnd(V(x1, y1))
    s.SetLayer(layer)
    s.SetWidth(MM(width))
    fp.Add(s)


def courtyard_bbox(fp):
    """Replace courtyard with bbox of all copper + fab items + 0.25 mm margin."""
    for item in list(fp.GraphicalItems()):
        if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() == pcbnew.F_CrtYd:
            fp.Remove(item)
    xs, ys = [], []
    for item in list(fp.GraphicalItems()) + list(fp.Pads()):
        if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() not in (pcbnew.F_Fab, pcbnew.F_SilkS):
            continue
        b = item.GetBoundingBox()
        xs += [b.GetLeft(), b.GetRight()]
        ys += [b.GetTop(), b.GetBottom()]
    m = MM(0.25)
    add_rect(fp, pcbnew.F_CrtYd,
             (min(xs) - m) / 1e6, (min(ys) - m) / 1e6,
             (max(xs) + m) / 1e6, (max(ys) + m) / 1e6, 0.05)


def save(fp):
    OUT_LIB.mkdir(parents=True, exist_ok=True)
    io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    io.FootprintSave(str(OUT_LIB), fp)
    print("saved", fp.GetFPID().GetLibItemName())


# ---------------------------------------------------------------- R hybrid
def build_r():
    base = load("Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical")
    smd = load("Resistor_SMD", "R_0805_2012Metric")
    fp = new_fp("R_Hybrid_0805_P2.54_Vertical",
                "Hybrid resistor: axial DIN0207 vertical P2.54 THT OR 0805 chip; same pad numbers, lands overlap rings",
                "resistor hybrid 0805 axial vertical", pcbnew.FP_THROUGH_HOLE)
    copy_pads(base, fp, -1.27, 0)                          # THT rings at +-1.27
    copy_graphics(base, fp, -1.27, 0, layers=(pcbnew.F_SilkS, pcbnew.F_Fab))
    copy_pads(smd, fp, 0, 1.15)                            # 0805 lands shifted up, overlap ring tops
    add_rect(fp, pcbnew.F_Fab, -1.0, 0.525, 1.0, 1.775, 0.1)       # 0805 body outline
    add_line(fp, pcbnew.F_SilkS, -0.3, 2.05, 0.3, 2.05, 0.12)      # tick below chip
    courtyard_bbox(fp)
    save(fp)


# ---------------------------------------------------------------- LED hybrid
def build_led():
    base = load("LED_THT", "LED_D3.0mm")
    smd = load("LED_SMD", "LED_0805_2012Metric")
    fp = new_fp("LED_Hybrid_0805_D3.0mm",
                "Hybrid LED: 3 mm THT (P2.54, pad1=K square) OR 0805 LED (pad1=K); lands overlap rings",
                "led hybrid 0805 3mm", pcbnew.FP_THROUGH_HOLE)
    copy_pads(base, fp, -1.27, 0)
    copy_graphics(base, fp, -1.27, 0, layers=(pcbnew.F_SilkS, pcbnew.F_Fab))
    copy_pads(smd, fp, 0, 1.2)
    add_rect(fp, pcbnew.F_Fab, -1.0, 0.575, 1.0, 1.825, 0.1)
    add_line(fp, pcbnew.F_SilkS, -1.0, 2.1, -1.0, 2.35, 0.12)     # K mark at pad 1 side of chip
    courtyard_bbox(fp)
    save(fp)


# ---------------------------------------------------------------- CP hybrid
def build_cp():
    base = load("Capacitor_THT", "CP_Radial_D5.0mm_P2.50mm")
    smd = load("Capacitor_SMD", "C_0805_2012Metric")
    fp = new_fp("CP_Hybrid_0805_D5.0mm_P2.50mm",
                "Hybrid capacitor: radial 5 mm electrolytic P2.5 (pad1=+) OR 0805 ceramic; lands overlap rings",
                "capacitor hybrid 0805 radial electrolytic", pcbnew.FP_THROUGH_HOLE)
    copy_pads(base, fp, -1.25, 0)
    copy_graphics(base, fp, -1.25, 0, layers=(pcbnew.F_SilkS, pcbnew.F_Fab))
    copy_pads(smd, fp, 0, 1.2)
    add_rect(fp, pcbnew.F_Fab, -1.0, 0.575, 1.0, 1.825, 0.1)
    courtyard_bbox(fp)
    save(fp)


# ---------------------------------------------------------------- Q hybrid
def build_q():
    tht = load("Package_TO_SOT_THT", "TO-92_Inline")
    sot = load("Package_TO_SOT_SMD", "SOT-23")
    fp = new_fp("Q_NPN_Hybrid_TO-92_SOT-23",
                "Hybrid NPN: TO-92 inline (legs L-B-R, pads 4-2-5) OR SOT-23 (1=E 2=B 3=C). "
                "Outer TO-92 legs route through solder jumpers to E/C so EBC and CBE parts both fit",
                "transistor hybrid TO-92 SOT-23 jumper", pcbnew.FP_THROUGH_HOLE)
    # THT: left leg -> 4, centre (B) -> 2 with ring elongated upward, right leg -> 5
    copy_pads(tht, fp, -1.27, 0, renumber={"1": "4", "2": "2", "3": "5"})
    for p in fp.Pads():
        if p.GetNumber() == "2":
            p.SetShape(pcbnew.PAD_SHAPE_OVAL)
            p.SetSize(V(1.05, 2.6))
            p.SetOffset(V(0, -0.55))
    copy_graphics(tht, fp, -1.27, 0, layers=(pcbnew.F_SilkS, pcbnew.F_Fab))
    # SOT-23 rotated: pads 1(B),2(E) on a row at y=-1.75; pad 3(C) above
    add_smd_pad(fp, "2", 0.0, -1.75, 0.6, 1.475)    # B land overlaps THT B ring (y -1.85..0.75)
    add_smd_pad(fp, "1", 1.9, -1.75, 0.6, 1.475)    # E
    add_smd_pad(fp, "3", 0.95, -3.625, 1.475, 0.6)  # C
    # SOT-23 body (1.3 x 2.9 rotated -> 2.9 wide? no: body 2.9 long along the 1-2 axis, 1.3 wide)
    add_rect(fp, pcbnew.F_Fab, 0.95 - 1.45, -2.6875 - 0.65, 0.95 + 1.45, -2.6875 + 0.65, 0.1)
    add_line(fp, pcbnew.F_SilkS, -0.65, -4.1, 2.55, -4.1, 0.12)    # silk bar on pad-3 (C) side
    add_line(fp, pcbnew.F_SilkS, 2.6, -2.4, 2.6, -1.0, 0.12)       # silk at E side
    courtyard_bbox(fp)
    save(fp)


if __name__ == "__main__":
    build_r(); build_led(); build_cp(); build_q()
    print("done ->", OUT_LIB)
