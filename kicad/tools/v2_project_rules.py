#!/usr/bin/env python3
"""Write the home-etch design rules into astable_v2.kicad_pro (idempotent).

pcbnew.SaveBoard() rewrites the project file with default rules, so this runs at the end
of gen_v2_board.py and finalize_v2.py, and can be run on its own:
    python3 kicad/tools/v2_project_rules.py
kicad-cli pcb drc reads its rules from here, not from the board file.
"""
import json
from pathlib import Path

PRO = Path(__file__).resolve().parents[1] / "astable_v2_single_layer" / "astable_v2.kicad_pro"
RULES = {"min_clearance": 0.6, "min_track_width": 0.8, "min_copper_edge_clearance": 1.0,
         "min_hole_clearance": 0.5, "min_hole_to_hole": 0.5, "min_through_hole_diameter": 0.8,
         "min_via_diameter": 1.6, "min_via_annular_width": 0.4, "min_connection": 0.8,
         "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 2,
         "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.08,
         "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True}
NETCLASS = {"name": "Default", "track_width": 1.0, "clearance": 0.6, "via_diameter": 1.6, "via_drill": 0.8,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 1.0, "diff_pair_gap": 0.6,
            "diff_pair_via_gap": 0.6, "wire_width": 6, "bus_width": 12, "line_style": 0, "priority": 2147483647,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}
IGNORE = ("silk_over_copper", "silk_overlap", "silk_edge_clearance")   # no silkscreen on an etched board


def apply():
    d = json.loads(PRO.read_text())
    ds = d.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update(RULES)
    sev = ds.setdefault("rule_severities", {})
    for k in IGNORE:
        sev[k] = "ignore"
    sev.setdefault("lib_footprint_mismatch", "warning")
    ns = d.setdefault("net_settings", {})
    ns["classes"] = [NETCLASS]
    ns["netclass_assignments"] = []
    ns["netclass_patterns"] = []
    d.setdefault("meta", {})["filename"] = PRO.name
    PRO.write_text(json.dumps(d, indent=2))
    return PRO


if __name__ == "__main__":
    print("rules written to", apply())
