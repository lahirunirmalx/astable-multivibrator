#!/usr/bin/env python3
"""Attach KiCad-library 3D models (THT variant) to the Hybrid footprints.

Applied to both the project library (kicad/lib/Hybrid.pretty) and the footprint
instances on the routed board, and fixes the board footprints' missing "Hybrid:"
library nickname. The THT pads in the hybrid footprints were shifted from the
base KiCad footprint origin (see build_hybrid_footprints.py), so each model gets
the same X offset.

Run with the system python3 that has pcbnew (KiCad 9):
    /usr/bin/python3 kicad/tools/add_3d_models.py
"""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "lib" / "Hybrid.pretty"
BOARD = ROOT / "astable_multivibrator" / "astable_multivibrator.kicad_pcb"

# footprint name -> (model path, x offset in mm)
MODELS = {
    "R_Hybrid_0805_P2.54_Vertical": (
        "${KICAD9_3DMODEL_DIR}/Resistor_THT.3dshapes/R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical.wrl", -1.27),
    "LED_Hybrid_0805_D3.0mm": (
        "${KICAD9_3DMODEL_DIR}/LED_THT.3dshapes/LED_D3.0mm.wrl", -1.27),
    "CP_Hybrid_0805_D5.0mm_P2.50mm": (
        "${KICAD9_3DMODEL_DIR}/Capacitor_THT.3dshapes/CP_Radial_D5.0mm_P2.50mm.wrl", -1.25),
    "Q_NPN_Hybrid_TO-92_SOT-23": (
        "${KICAD9_3DMODEL_DIR}/Package_TO_SOT_THT.3dshapes/TO-92_Inline.wrl", -1.27),
}


def attach(fp, name):
    path, dx = MODELS[name]
    models = fp.Models()
    if any(m.m_Filename == path for m in models):
        return False
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Offset = pcbnew.VECTOR3D(dx, 0.0, 0.0)
    models.push_back(m)
    return True


def do_library():
    io = pcbnew.PCB_IO_MGR.PluginFind(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    for name in MODELS:
        fp = pcbnew.FootprintLoad(str(LIB), name)
        assert fp, name
        if attach(fp, name):
            io.FootprintSave(str(LIB), fp)
            print("lib  :", name, "+model")


def do_board():
    board = pcbnew.LoadBoard(str(BOARD))
    changed = 0
    for fp in board.GetFootprints():
        fpid = fp.GetFPID()
        name = str(fpid.GetLibItemName())
        if name not in MODELS:
            continue
        if str(fpid.GetLibNickname()) != "Hybrid":
            fp.SetFPID(pcbnew.LIB_ID("Hybrid", name))
            changed += 1
        if attach(fp, name):
            changed += 1
        print("board:", fp.GetReference(), fp.GetFPID().GetUniStringLibId(), "models =", len(fp.Models()))
    pcbnew.SaveBoard(str(BOARD), board)
    print("board saved, changes:", changed)


if __name__ == "__main__":
    do_library()
    do_board()
