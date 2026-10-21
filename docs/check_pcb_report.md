# check-pcb report - astable_multivibrator (2026-10-20)

Board: `kicad/astable_multivibrator/astable_multivibrator.kicad_pcb` (26.15 x 21.73 mm, 2 layers, routed with Freerouting 1.9.0, GND pour both sides + 7 stitch vias).
Analysis dir: `analysis/2026-10-20_1046/` (pcb.json, cross_analysis.json, thermal.json, emc.json, gerber.json).

## Checklist

```
--- check-pcb ran ---
OK  DRC (kicad-cli, severity-all)  0 violations / 0 warnings / 0 unconnected (project rules: 0.2 track, 0.2 clearance, 0.5 edge)
OK  analyze_pcb --full             findings: BLOCKER 0 / CRITICAL 0 / HIGH 0 / warning 11 / info 4 (all triaged below)
OK  cross_analysis                 sch <-> pcb: consistent, 0 findings (15 refs, 12 nets)
OK  analyze_emc --market eu --spice-enhanced   12 findings: error 2 (GP-001) / warning 8 / info 2, risk score 77.5 - triaged, not applicable at 1.8 Hz
OK  analyze_thermal                0 findings, NOT ASSESSED (no dissipation data; whole board < 0.15 W)
OK  analyze_gerbers (board)        1 warning GR-004 (paste flashes < copper flashes: THT pads carry no paste, expected)
SKIP extract_parasitics + SPICE    not needed: no > 100k feedback, no LC / RF, 1.8 Hz oscillator
SKIP lifecycle_audit               no MPNs by design (generic jellybean parts)
OK  KiKit panel DRC                0 / 0 / 0 (2 x 4, 110.3 x 59.4 mm)
--- verdict ---
pass  next: release (fab package) - gerbers + drill + CPL already exported to release/ for board and panel
```

## Triage

| id | severity | finding | decision |
|---|---|---|---|
| PM-002 x9 | warning | R1-R4, JP1-JP4, J1 are 0.82 to 0.89 mm from the board edge | by design (minimum board). Copper keeps >= 0.5 mm from the edge (DRC rule). Mouse-bite tabs are 3 mm wide on the tab centres; sand the nubs before fitting the vertical resistors on the top edge. |
| FD-001 | warning | no fiducials on the 26 mm board | the panel rails carry 3 fiducials + 3 tooling holes; a single board this small is hand-assembled |
| TE-001 | warning | no test points | hobby board; every net reaches a THT pad that doubles as a probe point |
| GP-001 x7, GP-004 | error / warning | reference-plane gaps under signal traces, low plane fill | EMC rules target fast edges; this board switches at 1.8 Hz with 2 to 15 mA. Not applicable. Risk score 77.5 is a rule-coverage number, not a lab result. |
| RP-001 x2 | warning | no stitching via right at the Q1_TL / Q2_C layer transitions | same reason; 7 stitch vias at 4 mm pitch exist elsewhere |
| GR-004 | warning | F.Paste has 22 flashes vs 67 copper | THT pads have no paste; only the SMD lands do. Expected for a hybrid, hand-soldered board. |
| SK-002 | - | not raised | silk prints only designators and polarity marks, no numeric spec |

## Notes

- All tracks are 0.3 mm: the Power netclass patterns (`VCC`, `GND`) did not match the net names `/VCC`, `/GND` at routing time. Patterns corrected to `/VCC`, `/GND` in the .kicad_pro afterwards; no re-route (max current 15 mA).
- Final DRC was run after a pcbnew zone refill and save, so GUI, DRC and gerbers share the same fill.

## Verification gaps

- Thermal: not assessed by the tool (no dissipation data); hand calc max 99 mW in R1/R4 at 9 V (1/8 W parts fine, 1/4 W preferred).
- No datasheet cross-check (no MPN by design).
- EMC is pre-compliance heuristics only.
