#!/usr/bin/env python3
"""Route a placed .kicad_pcb with Freerouting, headless.

Steps: copy placed board -> strip copper zones (Freerouting must route GND as tracks,
otherwise pads sitting inside a plane are treated as connected and end up on islands
after refill) -> pcbnew.ExportSpecctraDSN -> freerouting -de/-do -> ImportSpecctraSES ->
save <stem>_routed.kicad_pcb (sidecar .kicad_pro copied so DRC uses the project rules).
Run with the system python3 that has pcbnew. Usage: route_freerouting.py <placed.kicad_pcb> [passes]
"""
import os, shutil, subprocess, sys
from pathlib import Path
import pcbnew

src = Path(sys.argv[1]).resolve()
passes = sys.argv[2] if len(sys.argv) > 2 else "60"
stem = src.with_suffix("")
routed = Path(f"{stem}_routed.kicad_pcb")
dsn = Path(f"{stem}_routed.dsn")
ses = Path(f"{stem}_routed.ses")

# sidecars first so LoadBoard of the copy sees netclasses
for ext in (".kicad_pro", ".kicad_prl", ".kicad_dru"):
    s = src.with_suffix(ext)
    if s.exists():
        shutil.copy(s, routed.with_suffix(ext))
shutil.copy(src, routed)

b = pcbnew.LoadBoard(str(routed))
zones = list(b.Zones())
for z in zones:
    b.Remove(z)
# also drop any stale tracks/vias from a previous run
for t in list(b.GetTracks()):
    b.Remove(t)
pcbnew.SaveBoard(str(routed), b)
print(f"stripped {len(zones)} zones", flush=True)

ok = pcbnew.ExportSpecctraDSN(b, str(dsn))
print("dsn export", ok, dsn.stat().st_size if dsn.exists() else "missing", flush=True)
if not dsn.exists():
    sys.exit("DSN export failed")

if ses.exists():
    ses.unlink()
env = {"HOME": os.environ["HOME"], "USER": os.environ.get("USER", "lahiru"),
       "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
cmd = ["xvfb-run", "-a", "java", "-jar", os.path.expanduser("~/tools/freerouting/freerouting-1.9.0.jar"),
       "-de", str(dsn), "-do", str(ses), "-mp", passes]
print("running:", " ".join(cmd), flush=True)
r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1500)
print("freerouting exit", r.returncode, flush=True)
tail = (r.stdout + r.stderr).strip().splitlines()[-15:]
print("\n".join(tail), flush=True)
if not ses.exists():
    sys.exit("no SES produced")

b = pcbnew.LoadBoard(str(routed))
ok = pcbnew.ImportSpecctraSES(b, str(ses))
print("ses import", ok, flush=True)
pcbnew.SaveBoard(str(routed), b)
b = pcbnew.LoadBoard(str(routed))
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
print(f"routed board: {len(tracks)} track segments, {len(vias)} vias -> {routed}", flush=True)
