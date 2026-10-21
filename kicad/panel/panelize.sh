#!/usr/bin/env bash
# Panelize the routed board with KiKit (2 x 4, mouse bites, top/bottom rails with tooling holes + fiducials).
# Needs the ~/electronics/.venv (python with pcbnew + kikit). Override rows/cols: ROWS=3 COLS=5 ./panelize.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="${1:-$HERE/../astable_multivibrator/astable_multivibrator.kicad_pcb}"
OUT="${2:-$HERE/astable_multivibrator_panel.kicad_pcb}"
ROWS="${ROWS:-2}"; COLS="${COLS:-4}"
KIKIT="${KIKIT:-$HOME/electronics/.venv/bin/kikit}"
"$KIKIT" panelize -p "$HERE/kikit_preset.json" --layout "rows: $ROWS; cols: $COLS" "$SRC" "$OUT"
cp "${SRC%.kicad_pcb}.kicad_pro" "${OUT%.kicad_pcb}.kicad_pro" 2>/dev/null || true
cp "$(dirname "$SRC")/fp-lib-table" "$(dirname "$SRC")/sym-lib-table" "$(dirname "$OUT")/" 2>/dev/null || true
kicad-cli pcb drc --format json --severity-all -o "${OUT%.kicad_pcb}_drc.json" "$OUT" >/dev/null
python3 - "${OUT%.kicad_pcb}_drc.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
e = sum(1 for v in d["violations"] if v["severity"] == "error"); w = len(d["violations"]) - e
print(f"panel DRC: errors={e} warnings={w} unconnected={len(d['unconnected_items'])}")
PY
echo "panel -> $OUT"
