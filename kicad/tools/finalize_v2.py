#!/usr/bin/env python3
"""Adopt the Freerouting result as the v2 board and add the bottom GND pour.

    /usr/bin/python3 kicad/tools/finalize_v2.py
Copies astable_v2_routed.kicad_pcb over astable_v2.kicad_pcb, adds a B.Cu GND zone
(0.8 mm clearance, 1.0 mm minimum width, thermal reliefs, islands removed), fills it, saves.
"""
import shutil
import sys
from pathlib import Path
import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v2_project_rules import apply as write_project_rules

PRJ = Path(__file__).resolve().parents[1] / "astable_v2_single_layer"
ROUTED, PCB = PRJ / "astable_v2_routed.kicad_pcb", PRJ / "astable_v2.kicad_pcb"
MM = pcbnew.FromMM

shutil.copy(ROUTED, PCB)
b = pcbnew.LoadBoard(str(PCB))
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z)
bb = b.GetBoardEdgesBoundingBox()
z = pcbnew.ZONE(b)
z.SetLayer(pcbnew.B_Cu)
z.SetNet(b.FindNet("GND"))
z.SetZoneName("GND_pour")
z.SetLocalClearance(MM(0.8))
z.SetMinThickness(MM(1.0))
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
z.SetThermalReliefGap(MM(0.8))
z.SetThermalReliefSpokeWidth(MM(1.0))
z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
z.Outline().NewOutline()
for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
    z.Outline().Append(pcbnew.VECTOR2I(x, y))
b.Add(z)
# reference designators where they can be read on the assembly drawing (silk is not etched, it is the build sheet)
REF_TEXT = {
    "R21": (15.5, 8.5, 90), "R22": (20.5, 8.5, 90), "R23": (25.5, 8.5, 90),
    "R31": (41.5, 8.5, 90), "R32": (46.5, 8.5, 90), "R33": (51.5, 8.5, 90),
    "R1": (26.3, 31.08, 90), "R4": (35.7, 31.08, 90),
    "LED1": (28.5, 44.7, 0), "LED2": (33.5, 44.7, 0),
    "Q1": (18.0, 22.4, 0), "Q2": (44.0, 22.4, 0),
    "JR1": (12.4, 18.7, 90), "JR2": (38.4, 18.7, 90),
    "JP1": (12.0, 30.6, 0), "JP2": (22.0, 30.6, 0), "JP3": (41.0, 30.6, 0), "JP4": (51.0, 30.6, 0),
    "W1": (16.0, 38.9, 0), "W2": (47.0, 38.9, 0), "W3": (34.2, 64.3, 90),
    "JC1": (12.4, 50.3, 90), "JC2": (38.4, 50.3, 90),
    "C13": (10.0, 63.7, 0), "C12": (18.0, 63.7, 0), "C11": (26.0, 63.7, 0),
    "C23": (38.0, 63.7, 0), "C22": (46.0, 63.7, 0), "C21": (54.0, 63.7, 0),
    "J1": (34.2, 5.3, 0),
}
for fp in b.GetFootprints():
    pos = REF_TEXT.get(fp.GetReference())
    if pos:
        r = fp.Reference()
        r.SetPosition(pcbnew.VECTOR2I(MM(pos[0]), MM(pos[1])))
        r.SetTextAngleDegrees(pos[2])
        r.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2)))
        r.SetTextThickness(MM(0.2))
# values on F.Fab: on the body for R and C, hidden where the designator says it all
HIDE_VALUE = {"J1", "Q1", "Q2", "LED1", "LED2", "JR1", "JR2", "JC1", "JC2", "JP1", "JP2", "JP3", "JP4", "W1", "W2", "W3"}
for fp in b.GetFootprints():
    ref, v = fp.GetReference(), fp.Value()
    v.SetLayer(pcbnew.F_Fab)
    v.SetTextSize(pcbnew.VECTOR2I(MM(0.9), MM(0.9)))
    v.SetTextThickness(MM(0.15))
    if ref in HIDE_VALUE:
        v.SetVisible(False)
        continue
    x, y = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetTextAngleDegrees(90 if ref.startswith("R") else 0)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
pcbnew.SaveBoard(str(PCB), b)
write_project_rules()              # SaveBoard rewrites the .kicad_pro with defaults
print("board finalized:", PCB.name, "zones:", len(list(b.Zones())))
