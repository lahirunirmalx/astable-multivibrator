#!/usr/bin/env python3
"""Create the v2 single-sided board from the schematic netlist (pcbnew API).

- loads HomeEtch footprints, assigns nets from astable_v2.net, sets symbol paths
- places every part from the PLACEMENT table (hand plan, see docs/v2_home_etching.md)
- rectangular outline, F.Cu rule area (no copper on top: single-sided), B.Cu id text
Run with the system python3 that has pcbnew (KiCad 9):
    /usr/bin/python3 kicad/tools/gen_v2_board.py [--print-pads]
"""
import re
import sys
from pathlib import Path
import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v2_project_rules import apply as write_project_rules

ROOT = Path(__file__).resolve().parents[1]
PRJ = ROOT / "astable_v2_single_layer"
NET = PRJ / "astable_v2.net"
PCB = PRJ / "astable_v2.kicad_pcb"
LIB = ROOT / "lib" / "HomeEtch.pretty"
MM = pcbnew.FromMM
BOARD_W, BOARD_H = 62.0, 72.0

# ref: (x, y, rotation_deg)  -- board origin top-left, y down
PLACEMENT = {
    "J1": (31.0, 4.0, 0),
    "R1": (28.5, 31.08, 270), "R4": (33.5, 31.08, 270),
    "R21": (13.0, 8.5, 270), "R22": (18.0, 8.5, 270), "R23": (23.0, 8.5, 270),
    "R31": (39.0, 8.5, 270), "R32": (44.0, 8.5, 270), "R33": (49.0, 8.5, 270),
    "JR1": (15.46, 20.0, 90), "JR2": (41.46, 20.0, 90),
    "Q1": (18.0, 26.5, 0), "Q2": (44.0, 26.5, 0),
    "JP1": (9.46, 33.0, 90), "JP2": (19.46, 33.0, 90), "JP3": (38.46, 33.0, 90), "JP4": (48.46, 33.0, 90),
    "W1": (16.0, 37.0, 180), "W2": (47.0, 37.0, 0),
    "LED1": (28.5, 41.0, 90), "LED2": (33.5, 41.0, 90),
    "JC1": (20.54, 49.0, 270), "JC2": (46.54, 49.0, 270),
    "C13": (10.0, 59.2, 270), "C12": (18.0, 59.2, 270), "C11": (26.0, 59.2, 270),
    "C23": (38.0, 59.2, 270), "C22": (46.0, 59.2, 270), "C21": (54.0, 59.2, 270),
    "W3": (32.0, 64.3, 270),
}


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def parse_netlist(text):
    comps = {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]+)"\)[\s\S]*?\(tstamps "([^"]+)"\)\)', text):
        comps[m.group(1)] = dict(value=m.group(2), fp=m.group(3), uuid=m.group(4))
    nets = {}
    body = text[text.index("(nets"):]
    for chunk in re.split(r'\(net \(code "\d+"\) ', body)[1:]:
        name = re.match(r'\(name "([^"]+)"\)', chunk).group(1)
        nets[name] = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', chunk)
    return comps, nets


def main():
    comps, nets = parse_netlist(NET.read_text())
    board = pcbnew.BOARD()
    board.SetFileName(str(PCB))
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    # nets
    netinfo = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pad_net = {(ref, pin): name for name, nodes in nets.items() for ref, pin in nodes}
    for ref, c in comps.items():
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(str(LIB), name)
        assert fp, c["fp"]
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        x, y, rot = PLACEMENT[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        if c["uuid"]:
            fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        for pad in fp.Pads():
            n = pad_net.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        board.Add(fp)
    # outline
    for (x0, y0, x1, y1) in ((0, 0, BOARD_W, 0), (BOARD_W, 0, BOARD_W, BOARD_H), (BOARD_W, BOARD_H, 0, BOARD_H), (0, BOARD_H, 0, 0)):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        board.Add(s)
    # rule area: nothing on F.Cu (single-sided)
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    z.SetLayer(pcbnew.F_Cu)
    z.SetZoneName("no_copper_on_top")
    pts = [V(-1, -1), V(BOARD_W + 1, -1), V(BOARD_W + 1, BOARD_H + 1), V(-1, BOARD_H + 1)]
    z.Outline().NewOutline()
    for p in pts:
        z.Outline().Append(p)
    board.Add(z)
    # id text on the copper side (reads correctly when looking at the copper)
    for text, x, y, size in (("ASTABLE V2", 5.5, 2.2, 1.0), ("MIT 2026", 55.5, 2.2, 1.0)):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text); t.SetPosition(V(x, y)); t.SetLayer(pcbnew.B_Cu)
        t.SetTextSize(V(size, size)); t.SetTextThickness(MM(0.35)); t.SetMirrored(True)
        board.Add(t)
    pcbnew.SaveBoard(str(PCB), board)
    write_project_rules()          # SaveBoard rewrites the .kicad_pro with defaults
    print(f"wrote {PCB}: {len(comps)} footprints, {len(nets)} nets")
    if "--print-pads" in sys.argv:
        b = pcbnew.LoadBoard(str(PCB))
        for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
            pads = ", ".join(f"{p.GetNumber()}@({p.GetPosition().x/1e6:.2f},{p.GetPosition().y/1e6:.2f}) {p.GetNetname()}" for p in fp.Pads())
            print(f"{fp.GetReference():5s} {pads}")


if __name__ == "__main__":
    main()
