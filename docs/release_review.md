# Independent fab-artifact review - 2026-10-20 (second-pass reviewer, no files modified)

Verdict: no finding that would make a fab reject either package.

| check | result |
|---|---|
| Layers present (board + panel) | PASS: 9 gerbers + drill + map + job each; B.Paste / B.Silk legitimately empty (no bottom parts) |
| Object counts panel vs board | PASS: 8.0x on every layer, extras = fiducials, tooling, mouse bites, panel label |
| Edge.Cuts | PASS: board 1 closed loop 26.05 x 21.64 mm, copper >= 0.5 mm from edge; panel 1 outline + 9 routed gaps, no stray loops |
| Drill | PASS: board 33/33 holes cross-referenced (9 via 0.30, 24 PTH), report present; panel 407/407 incl. 140 x 0.50 mm mouse bites + 3 x 1.5 mm tooling |
| CPL | PASS: 11 top-side rows (all THT included); JP1-4 omitted because the KiCad Jumper library marks them exclude-from-pos (copper only) |
| Assembly BOM | PASS for PCB-only: 7 lines / 15 refs match the schematic; Qty/MPN columns empty by design |
| Silkscreen | PASS: all 11 designators + cap "+" marks + hatch present; cosmetic: 0.8 mm text / 0.12 mm lines are under the 1.0 / 0.15 mm fab recommendation (blurry, not rejected) |
| Gerber headers | PASS: X2, mm, 4.6, KiCad 9.0.8, consistent |
| Audit tool | 0 errors; GR-004 paste-vs-copper is a hybrid-board false positive; panel GR-002 (rails carry no copper) benign |
| Zips | PASS: md5-identical to directories, unzip -t clean |

Practical notes (not blockers):
1. ORDER_GUIDE.md (template output) cites `pcb_fab/assembly_bom.csv` and `pcb_fab/astable_multivibrator_positions.csv`; the real paths are under `pcb_fab/assembly/`. It also prints "SMT 15 / THT 0" and "?" for thickness and size. Use release/PCBWAY_ORDER.md instead.
2. `--subtract-soldermask` writes a negative-polarity (LPC) block at the end of each silkscreen gerber. Major fabs handle it; if the fab preview shows silk gaps, re-export without the flag.
3. Minimum features sit at common limits with no margin: 0.30 mm via drill / 0.15 mm annular ring; 0.50 mm mouse-bite holes.
4. Mouse-bite holes are centred on the board edge (KiKit offset 0), so small nubs remain after depanel: sand before fitting the edge resistors.
5. Not verified visually (no gerbv); silk verified by geometry only.
