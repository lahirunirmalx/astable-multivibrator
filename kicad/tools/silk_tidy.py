#!/usr/bin/env python3
"""Silk tidy for hybrid boards: move footprint silk that crosses an SMD land to F.Fab,
then pin reference designators to hand-chosen spots (board mm). Run with pcbnew python."""
import sys, pcbnew
REFS = {  # ref: (x, y, angle_deg, size_mm)
    "R1": (4.3, 5.0, 90, 0.8), "R2": (8.5, 5.0, 90, 0.8), "R3": (19.0, 5.0, 90, 0.8), "R4": (23.3, 5.0, 90, 0.8),
    "J1": (12.0, 4.6, 0, 0.8), "C1": (10.8, 6.4, 0, 0.8), "C2": (13.2, 15.6, 0, 0.8),
    "JP1": (2.1, 17.95, 0, 0.8), "JP2": (7.1, 17.95, 0, 0.8), "JP3": (16.9, 17.95, 0, 0.8), "JP4": (21.9, 17.95, 0, 0.8),
    "Q1": (8.2, 13.5, 90, 0.8), "Q2": (15.8, 13.5, 90, 0.8), "LED1": (0.3, 8.5, 90, 0.8), "LED2": (23.7, 8.5, 90, 0.8),
}
def box(bb, m=0):
    return (bb.GetLeft()-m, bb.GetTop()-m, bb.GetRight()+m, bb.GetBottom()+m)
def hit(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])
for p in sys.argv[1:]:
    b = pcbnew.LoadBoard(p); silk = b.GetLayerID("F.SilkS"); fab = b.GetLayerID("F.Fab"); moved = 0
    m = pcbnew.FromMM(0.15)
    for fp in b.GetFootprints():
        pads = [box(pd.GetBoundingBox(), m) for pd in fp.Pads() if pd.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
        for it in list(fp.GraphicalItems()):
            if it.GetLayer() == silk and any(hit(box(it.GetBoundingBox()), pb) for pb in pads):
                it.SetLayer(fab); moved += 1
        r = fp.GetReference()
        if r in REFS:
            x, y, a, s = REFS[r]; t = fp.Reference()
            t.SetVisible(True)
            # copper-only solder jumpers: keep their designators on F.Fab (no room on silk next to the TO-92 outline)
            t.SetLayer(fab if r.startswith("JP") else silk)
            t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
            t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(s), pcbnew.FromMM(s)))
            t.SetTextThickness(pcbnew.FromMM(0.12))
            t.SetTextAngle(pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T))
    pcbnew.SaveBoard(p, b); print(p.split('/')[-1], "silk->fab:", moved, "refs pinned:", sum(1 for fp in b.GetFootprints() if fp.GetReference() in REFS))
