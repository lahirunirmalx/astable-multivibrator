# PCBWay order sheet - astable_multivibrator (2026-10-20)

User channel choice: PCBWay for the PCB. No MPNs exist by design (jellybean parts you already have),
so order **PCB only** (no assembly) and hand-solder; see docs/assembly.md.

## What to upload

| order | file | note |
|---|---|---|
| Panel (recommended, 8 boards per piece) | `release/astable_multivibrator_gerbers_panel_2x4.zip` | 110.3 x 59.4 mm, mouse bites, 5 mm rails top/bottom with 3 tooling holes + 3 fiducials |
| Single board | `release/20261020_190434/pcb_fab/astable_multivibrator_fab.zip` | 26.15 x 21.73 mm, from the release umbrella (also contains CPL + assembly BOM, ignore for PCB-only) |

## PCBWay quote form (https://www.pcbway.com/orderonline.aspx)

| field | value |
|---|---|
| Board type | Panel by Customer (for the panel zip) / Single PCB (for the single zip) |
| Panel details | 2 x 4, route process: panel with mouse bites, rails included in the Gerber |
| Size | 110.3 x 59.4 mm (panel) or 26.15 x 21.73 mm (single) |
| Quantity | 5 panels = 40 boards minimum |
| Layers | 2 |
| Material | FR-4 TG150 |
| Thickness | 1.6 mm |
| Min track / spacing | 6 / 6 mil (design uses 0.3 mm tracks, 0.2 mm clearance min) |
| Min hole size | 0.3 mm |
| Solder mask | green (any colour fine) |
| Silkscreen | white |
| Surface finish | HASL lead-free (hand soldering) or ENIG |
| Copper | 1 oz |
| Via process | tenting vias |
| Gold fingers / impedance / castellations | no |
| Edge connector | no |

Gerber format: KiCad 9, RS-274X X2, units mm, 6-decimal, Excellon drill in mm, drill map in Gerber X2.
Mask subtracted from silkscreen. Zones refilled before export.

## Known template glitches in release/20261020_190434/ORDER_GUIDE.md

- It cites `pcb_fab/assembly_bom.csv` and `pcb_fab/astable_multivibrator_positions.csv`; the real files are in `pcb_fab/assembly/`.
- "SMT 15 / THT 0" and the "?" thickness / size are unfilled template slots; the values above are correct.
- Independent review of all fab files: docs/release_review.md (no reject-level findings).

## Why not JLCPCB / assembly paths in ORDER_GUIDE.md

ORDER_GUIDE.md in the timestamped release folder is the generic template output. Its coverage matrix
is empty because no part has an MPN, so every assembly path reads 0/0. That is expected for this board.
