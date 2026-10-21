#!/usr/bin/env python3
"""Route the v2 single-sided board with Freerouting, headless.

Differences from route_freerouting.py (v1):
  - rule areas are kept (the F.Cu keepout is what makes the board single-sided) and a
    board-wide F.Cu keepout is injected into the DSN if the exporter dropped it
  - wire links W1..W3 are series elements in the schematic (two sub-nets joined by a
    net-tie footprint), so the router never tries to join their pads with copper
Usage: /usr/bin/python3 kicad/tools/route_v2.py <board.kicad_pcb> [passes]
"""
import os, re, shutil, subprocess, sys
from pathlib import Path
import pcbnew

src = Path(sys.argv[1]).resolve()
passes = sys.argv[2] if len(sys.argv) > 2 else "100"
stem = src.with_suffix("")
routed = Path(f"{stem}_routed.kicad_pcb")
dsn = Path(f"{stem}_routed.dsn")
ses = Path(f"{stem}_routed.ses")
for ext in (".kicad_pro", ".kicad_prl", ".kicad_dru"):
    s = src.with_suffix(ext)
    if s.exists():
        shutil.copy(s, routed.with_suffix(ext))
shutil.copy(src, routed)

b = pcbnew.LoadBoard(str(routed))
for z in list(b.Zones()):
    if not z.GetIsRuleArea():
        b.Remove(z)
for t in list(b.GetTracks()):
    b.Remove(t)
pcbnew.SaveBoard(str(routed), b)
ok = pcbnew.ExportSpecctraDSN(b, str(dsn))
print("dsn export", ok, flush=True)
text = dsn.read_text()
if "keepout" not in text:
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0 = bb.GetLeft() / 1e6 * 1000, -bb.GetTop() / 1e6 * 1000
    x1, y1 = bb.GetRight() / 1e6 * 1000, -bb.GetBottom() / 1e6 * 1000
    ko = f'    (keepout "no_top_copper" (polygon F.Cu 0 {x0} {y0} {x1} {y0} {x1} {y1} {x0} {y1} {x0} {y0}))\n'
    text = text.replace("  (structure\n", "  (structure\n" + ko, 1)
    print("injected F.Cu keepout", flush=True)
else:
    print("DSN has keepout from the rule area", flush=True)
# home-etch rules: 1.0 mm tracks, 0.6 mm clearance (the exporter wrote the board defaults)
text = re.sub(r"\(width \d+(\.\d+)?\)", "(width 1000)", text)
text = re.sub(r"\(clearance \d+(\.\d+)?\)", "(clearance 600)", text)
text = re.sub(r"\(clearance \d+(\.\d+)? \(type", "(clearance 600 (type", text)
dsn.write_text(text)

if ses.exists():
    ses.unlink()
env = {"HOME": os.environ["HOME"], "USER": os.environ.get("USER", "lahiru"),
       "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
cmd = ["xvfb-run", "-a", "java", "-jar", os.path.expanduser("~/tools/freerouting/freerouting-1.9.0.jar"),
       "-de", str(dsn), "-do", str(ses), "-mp", passes]
r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1500)
print("freerouting exit", r.returncode, flush=True)
print("\n".join((r.stdout + r.stderr).strip().splitlines()[-8:]), flush=True)
if not ses.exists():
    sys.exit("no SES produced")
b = pcbnew.LoadBoard(str(routed))
print("ses import", pcbnew.ImportSpecctraSES(b, str(ses)), flush=True)
pcbnew.SaveBoard(str(routed), b)
b = pcbnew.LoadBoard(str(routed))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
top = [t for t in tracks if t.GetLayer() == pcbnew.F_Cu]
print(f"routed: {len(tracks)} segments ({len(top)} on F.Cu), {len(vias)} vias -> {routed}", flush=True)
