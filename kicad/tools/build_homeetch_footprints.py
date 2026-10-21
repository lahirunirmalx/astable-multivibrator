#!/usr/bin/env python3
"""Build the single-sided home-etch footprint library kicad/lib/HomeEtch.pretty (pcbnew API).

Design intent: toner-transfer / photoresist etching at home, hand drilling.
  - round or oval pads >= 1.8 mm, drills 0.9 to 1.0 mm (annular ring >= 0.4 mm)
  - 2.54 mm pitch parts keep >= 0.6 mm copper gap between pads
  - pad 1 square on polarised parts
  - THT only, copper on B.Cu (pads are through-hole, so both layers in the lib)
  - KiCad 3D models attached (offset to the base-footprint origin)
Run with the system python3 that has pcbnew (KiCad 9):
    /usr/bin/python3 kicad/tools/build_homeetch_footprints.py
"""
from pathlib import Path
import pcbnew

OUT_LIB = Path(__file__).resolve().parents[1] / "lib" / "HomeEtch.pretty"
MM = pcbnew.FromMM
MODELS = "${KICAD9_3DMODEL_DIR}"


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


BOARD = pcbnew.BOARD()


def new_fp(name, desc, tags):
    fp = pcbnew.FOOTPRINT(BOARD)
    fp.SetFPID(pcbnew.LIB_ID("HomeEtch", name))
    fp.SetLibDescription(desc)
    fp.SetKeywords(tags)
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
    fp.Reference().SetText("REF**")
    fp.Reference().SetPosition(V(0, -4.5))
    fp.Reference().SetTextSize(V(1.2, 1.2))
    fp.Reference().SetTextThickness(MM(0.2))
    fp.Value().SetText(name)
    fp.Value().SetPosition(V(0, 4.5))
    fp.Value().SetLayer(pcbnew.F_Fab)
    return fp


def pad(fp, number, x, y, w, h, drill, square=False):
    p = pcbnew.PAD(fp)
    p.SetNumber(number)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    if square:
        p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        p.SetRoundRectRadiusRatio(0.15)
    elif w == h:
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    else:
        p.SetShape(pcbnew.PAD_SHAPE_OVAL)
    p.SetSize(V(w, h))
    p.SetDrillSize(V(drill, drill))
    p.SetPosition(V(x, y))
    ls = pcbnew.LSET.AllCuMask()
    ls.AddLayer(pcbnew.F_Mask)
    ls.AddLayer(pcbnew.B_Mask)
    p.SetLayerSet(ls)
    fp.Add(p)
    return p


def shape(fp, layer, kind, width=0.15):
    s = pcbnew.PCB_SHAPE(fp)
    s.SetShape(kind)
    s.SetLayer(layer)
    s.SetWidth(MM(width))
    fp.Add(s)
    return s


def line(fp, layer, x0, y0, x1, y1, width=0.15):
    s = shape(fp, layer, pcbnew.SHAPE_T_SEGMENT, width)
    s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1))


def rect(fp, layer, x0, y0, x1, y1, width=0.15):
    s = shape(fp, layer, pcbnew.SHAPE_T_RECT, width)
    s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1))


def circle(fp, layer, cx, cy, r, width=0.15):
    s = shape(fp, layer, pcbnew.SHAPE_T_CIRCLE, width)
    s.SetCenter(V(cx, cy)); s.SetEnd(V(cx + r, cy))


def arc(fp, layer, cx, cy, r, a0, a1, width=0.15):
    import math
    s = shape(fp, layer, pcbnew.SHAPE_T_ARC, width)
    am = (a0 + a1) / 2
    def pt(a):
        return V(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    s.SetArcGeometry(pt(a0), pt(am), pt(a1))


def model(fp, path, dx=0.0, dy=0.0, rot=0.0):
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Offset = pcbnew.VECTOR3D(dx, dy, 0.0)
    m.m_Rotation = pcbnew.VECTOR3D(0.0, 0.0, rot)
    fp.Models().push_back(m)


def courtyard(fp, margin=0.5):
    xs, ys = [], []
    for item in list(fp.GraphicalItems()) + list(fp.Pads()):
        if isinstance(item, pcbnew.PCB_SHAPE):
            if item.GetLayer() not in (pcbnew.F_Fab, pcbnew.F_SilkS):
                continue
        elif not isinstance(item, pcbnew.PAD):
            continue
        b = item.GetBoundingBox()
        xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
    m = MM(margin)
    rect(fp, pcbnew.F_CrtYd, (min(xs) - m) / 1e6, (min(ys) - m) / 1e6, (max(xs) + m) / 1e6, (max(ys) + m) / 1e6, 0.05)


def save(fp):
    OUT_LIB.mkdir(parents=True, exist_ok=True)
    io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    io.FootprintSave(str(OUT_LIB), fp)
    print("saved", fp.GetFPID().GetLibItemName())


def r_axial():
    fp = new_fp("R_Axial_P10.16mm_HomeEtch", "Axial resistor 0207, 10.16 mm pitch, 2.4 mm pads, home etch", "resistor axial home etch")
    pad(fp, "1", -5.08, 0, 2.4, 2.4, 0.9)
    pad(fp, "2", 5.08, 0, 2.4, 2.4, 0.9)
    rect(fp, pcbnew.F_SilkS, -3.3, -1.4, 3.3, 1.4)
    line(fp, pcbnew.F_SilkS, -3.3, 0, -3.6, 0); line(fp, pcbnew.F_SilkS, 3.3, 0, 3.6, 0)
    rect(fp, pcbnew.F_Fab, -3.15, -1.25, 3.15, 1.25, 0.1)
    model(fp, f"{MODELS}/Resistor_THT.3dshapes/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.wrl", -5.08)
    courtyard(fp); save(fp)


def cp_radial():
    fp = new_fp("CP_Radial_D6.3mm_P2.50mm_HomeEtch", "Radial electrolytic up to 6.3 mm dia, 2.5 mm pitch, pad 1 = +, home etch", "capacitor electrolytic radial home etch")
    pad(fp, "1", -1.25, 0, 1.8, 2.6, 0.9, square=True)
    pad(fp, "2", 1.25, 0, 1.8, 2.6, 0.9)
    circle(fp, pcbnew.F_SilkS, 0, 0, 3.35)
    line(fp, pcbnew.F_SilkS, -4.3, -1.6, -4.3, -2.6); line(fp, pcbnew.F_SilkS, -4.8, -2.1, -3.8, -2.1)   # + mark
    circle(fp, pcbnew.F_Fab, 0, 0, 3.15, 0.1)
    model(fp, f"{MODELS}/Capacitor_THT.3dshapes/CP_Radial_D6.3mm_P2.50mm.wrl", -1.25)
    courtyard(fp); save(fp)


def led():
    fp = new_fp("LED_D3.0mm_P2.54mm_HomeEtch", "3 mm LED, 2.54 mm pitch, pad 1 = cathode (square), home etch", "led 3mm home etch")
    pad(fp, "1", -1.27, 0, 1.8, 2.6, 0.9, square=True)
    pad(fp, "2", 1.27, 0, 1.8, 2.6, 0.9)
    arc(fp, pcbnew.F_SilkS, 0, 0, 1.75, -110, 110)       # round side toward the anode
    line(fp, pcbnew.F_SilkS, -0.6, -1.65, -0.6, 1.65)    # flat = cathode
    circle(fp, pcbnew.F_Fab, 0, 0, 1.5, 0.1)
    model(fp, f"{MODELS}/LED_THT.3dshapes/LED_D3.0mm.wrl", -1.27)
    courtyard(fp); save(fp)


def to92():
    fp = new_fp("TO-92_P2.54mm_HomeEtch", "TO-92 inline, 2.54 mm leg pitch, pad 1 = left leg (square), flat face toward the silk line, home etch",
                "transistor to-92 home etch")
    pad(fp, "1", -2.54, 0, 1.8, 2.6, 0.9, square=True)
    pad(fp, "2", 0, 0, 1.8, 2.6, 0.9)
    pad(fp, "3", 2.54, 0, 1.8, 2.6, 0.9)
    arc(fp, pcbnew.F_SilkS, 0, 0, 2.6, 20, 160)           # round back, flat face at the bottom (+y side)
    line(fp, pcbnew.F_SilkS, -2.45, 1.0, 2.45, 1.0)       # flat face
    line(fp, pcbnew.F_SilkS, -2.45, 1.0, -2.45, 0.9); line(fp, pcbnew.F_SilkS, 2.45, 1.0, 2.45, 0.9)
    circle(fp, pcbnew.F_Fab, 0, 0, 2.5, 0.1)
    model(fp, f"{MODELS}/Package_TO_SOT_THT.3dshapes/TO-92_Inline_Wide.wrl", -2.54)
    courtyard(fp); save(fp)


def header(rows, cols):
    name = f"PinHeader_{cols}x{rows:02d}_P2.54mm_HomeEtch"
    fp = new_fp(name, f"{cols}x{rows} pin header 2.54 mm, 1.8 mm pads, pad 1 square, home etch", "pin header home etch")
    n = 1
    for r in range(rows):
        for c in range(cols):
            pad(fp, str(n), c * 2.54, r * 2.54, 1.8, 1.8, 1.0, square=(n == 1))
            n += 1
    w, h = (cols - 1) * 2.54, (rows - 1) * 2.54
    rect(fp, pcbnew.F_SilkS, -1.27 - 0.3, -1.27 - 0.3, w + 1.27 + 0.3, h + 1.27 + 0.3)
    rect(fp, pcbnew.F_Fab, -1.27, -1.27, w + 1.27, h + 1.27, 0.1)
    model(fp, f"{MODELS}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_{cols}x{rows:02d}_P2.54mm_Vertical.wrl")
    courtyard(fp, 0.3); save(fp)


def wire_link(pitch=15.24):
    name = f"WireLink_P{pitch:.2f}mm_HomeEtch"
    fp = new_fp(name, f"Wire link (bare wire on the component side), {pitch} mm pitch; pads are a net tie", "wire link jumper home etch")
    h = pitch / 2
    pad(fp, "1", -h, 0, 2.4, 2.4, 0.9)
    pad(fp, "2", h, 0, 2.4, 2.4, 0.9)
    line(fp, pcbnew.F_SilkS, -h + 1.6, 0, h - 1.6, 0, 0.3)
    line(fp, pcbnew.F_Fab, -h + 1.6, 0, h - 1.6, 0, 0.1)
    courtyard(fp); save(fp)
    # SetNetTiePadGroups is not exposed to python in KiCad 9: patch the saved file
    f = OUT_LIB / f"{name}.kicad_mod"
    t = f.read_text()
    if "net_tie_pad_groups" not in t:
        t = t.replace("\t(attr through_hole)", '\t(attr through_hole)\n\t(net_tie_pad_groups "1,2")', 1)
        f.write_text(t)
        print("patched net_tie_pad_groups into", f.name)


if __name__ == "__main__":
    r_axial(); cp_radial(); led(); to92(); header(2, 1); header(3, 1); header(3, 2); wire_link(15.24); wire_link(12.7); wire_link(7.62)
    print("done ->", OUT_LIB)
