# astable_multivibrator - classic 2-transistor LED flasher, hybrid THT/SMD, panel-ready

Classic 2-transistor astable multivibrator LED flasher; hybrid THT+SMD footprints, panelization support, transistor pinout jumper, minimum board size

> Generic workspace rules live in the skills; this file holds only project-specific decisions.
> Created: 2026-10-20

---

## 1. Project goal

A minimum-size, panel-ready PCB for the textbook two-transistor astable multivibrator
driving two LEDs (alternating flasher). Every part position accepts EITHER a through-hole
part OR an SMD part (hybrid footprints), and the transistor footprint accepts TO-92 of
either common pinout (E-B-C or C-B-E) as well as SOT-23, selected by solder jumpers.

- Goal 1: build from whatever jellybean parts are on hand (THT or SMD), no BOM lock-in.
- Goal 2: smallest board that still hand-solders, with edges clean for KiKit panelization.

---

## 2. Technical parameters

| Item | Spec | Note |
|------|------|------|
| Supply | 3 V to 9 V DC, 5 V recommended | Above ~6 V the OFF transistor's E-B junction is driven past V_EBO (-Vcc swing) and avalanches briefly each half cycle; classic-kit behaviour, harmless at these currents but timing drifts slightly |
| Frequency | ~1.5 Hz at 47k / 10 uF (T = 1.386 * Rb * C) | 0.65 s period, 50 % duty |
| LED current | ~6 mA at 5 V, ~14 mA at 9 V with 470 R | (Vcc - Vf_LED - Vce_sat) / Rc |
| Base drive | Ib = (Vcc - 0.7) / 47k = 91 uA at 5 V | needs hFE >= 66 for saturation at 6 mA; any GP NPN |
| Layers | 2, 1.6 mm FR4 | copper both sides, GND pour |
| Fab rules | 0.2 mm track / clearance min, 0.3 mm drill min | JLCPCB / PCBWay standard |
| Panel | rectangular outline, no copper within 0.5 mm of edge, 2.54 mm header on one edge only | KiKit mouse-bite tabs on the long edges |
| Operating temp | 0 to 70 C | hobby |

---

## 3. Schematic v0.1

```
 VCC ----+---------+-------------------+---------+----- J1.1 (VCC)
         |         |                   |         |
        R1 470    R2 47k              R3 47k    R4 470
         |         |                   |         |
        LED1(A)    |                   |        LED2(A)
        LED1(K)    |                   |        LED2(K)
         |         |                   |         |
    Q1_C +---------|---C1 10uF---+     |         + Q2_C
         |         |   (+)   (-) |     |         |
         |      Q1_B             |     |         |
         |         |             +---Q2_B        |
         |         |    +---C2 10uF----|---------+
         |         |    |  (-)    (+)  |         |
         |         +----+              |         |
         |         |                   |         |
        Q1 C       |                  Q2 C       |
       B---+   (B=Q1_B)              B---+   (B=Q2_B)
        Q1 E                          Q2 E
         |                             |
 GND ----+-----------------------------+------------- J1.2 (GND)

Timing caps: C1 (+) at Q1_C, (-) at Q2_B.  C2 (+) at Q2_C, (-) at Q1_B.

Transistor hybrid footprint pads:  1=E 2=B 3=C (SOT-23 lands, B shared with TO-92 centre hole)
                                   4=TL 5=TR (TO-92 outer legs)
Pinout jumpers (per transistor, SolderJumper_3, pin 2 = common):
   JP1: 1=GND(E)  2=Q1_TL  3=Q1_C      JP2: 1=Q1_C  2=Q1_TR  3=GND(E)
   JP3: 1=GND(E)  2=Q2_TL  3=Q2_C      JP4: 1=Q2_C  2=Q2_TR  3=GND(E)
   Factory bridge 1-2  -> TL=E, TR=C  -> TO-92 pinout E-B-C (2N3904, PN2222, S8050, 2N4401)
   Cut 1-2, bridge 2-3 -> TL=C, TR=E  -> TO-92 pinout C-B-E (BC547/548/549, BC337)
   SOT-23 (MMBT3904, BC847, MMBT2222) always lands on pads 1/2/3, jumpers irrelevant.
```

---

## 4. Interface definition

### J1 - power input (1x2 pin header 2.54 mm, THT; wires may also be soldered directly)

| Pin | Signal | Note |
|-----|--------|------|
| 1 | VCC | 3 V to 9 V DC, square pad |
| 2 | GND | |

No other connectors. LEDs are the output.

---

## 5. BOM + spec freeze table v0.1

| role | part role | target spec | MPN on hand | status |
|------|-----------|-------------|-------------|--------|
| npn_sw (Q1, Q2) | general-purpose NPN, hybrid TO-92 / SOT-23 | Vceo >= 20 V, Ic >= 100 mA, hFE >= 70; TO-92 EBC or CBE, or SOT-23 BEC | any of 2N3904 / BC547 / MMBT3904 | spec_frozen (jellybean, no vendoring) |
| led_out (LED1, LED2) | indicator LED, hybrid 3 mm / 0805 | Vf 1.8 to 2.2 V (red), If 20 mA max | any | spec_frozen |
| r_coll (R1, R4) | collector / LED series R | 470 R, 1/8 W or more, axial 0207 vertical or 0805 | any | spec_frozen |
| r_base (R2, R3) | base bias R | 47k, 1/8 W or more, axial 0207 vertical or 0805 | any | spec_frozen |
| c_timing (C1, C2) | timing capacitor, hybrid radial 5 mm / 0805 | 10 uF, >= 16 V; electrolytic (+ to collector) or X5R/X7R 0805 | any | spec_frozen |
| pinout_sel (JP1..JP4) | 3-pad solder jumper, bridged 1-2 by default | KiCad Jumper:SolderJumper-3_P1.3mm_Bridged12 | n/a (copper only) | locked |
| pwr_in (J1) | 1x2 2.54 mm pin header | generic | any | spec_frozen |

All parts are generic jellybeans: Phase 2 component-selecting and Phase 2.5 vendoring are
skipped on purpose; the BOM gate runs in generic mode (library presence only).

Custom libraries (project copy in `kicad/lib/`, referenced by the project lib tables; master copy in the workspace `~/tools/PCB-Agent-Teams/lib_external/`):

| lib id | what |
|--------|------|
| Hybrid:R_Hybrid_0805_P2.54_Vertical | axial 0207 vertical P2.54 THT + 0805 lands above the row, lands overlap rings |
| Hybrid:LED_Hybrid_0805_D3.0mm | 3 mm LED P2.54 THT (pad 1 = K, square) + 0805 LED lands |
| Hybrid:CP_Hybrid_0805_D5.0mm_P2.50mm | radial 5 mm electrolytic P2.5 (pad 1 = +, square) + 0805 lands |
| Hybrid:Q_NPN_Hybrid_TO-92_SOT-23 | TO-92 inline 1.27 mm + SOT-23, 5 pads as in section 3 |
| Hybrid:Q_NPN_Hybrid (symbol) | Transistor_BJT:Q_NPN_EBC + pins 4 TL / 5 TR |

Hybrid rule: every SMD land shares a pad number with a THT pad AND physically overlaps its
annular ring, so KiCad sees one copper island per pin and the router never leaves a land floating.
Generator: `kicad/tools/build_hybrid_footprints.py` (pcbnew API, no hand-written .kicad_mod).

---

## 6. Key calculations

```
T_half = 0.693 * Rb * C = 0.693 * 47k * 10u = 0.326 s   -> f = 1 / (2 * 0.326) = 1.53 Hz
I_LED(5 V) = (5 - 2.0 - 0.2) / 470 = 6.0 mA      I_LED(9 V) = 14.5 mA   (LED max 20 mA ok)
P_R1(9 V)  = 14.5 mA^2 * 470 = 99 mW             -> 1/8 W axial or 0805 (125 mW) ok, 1/4 W preferred at 9 V
Ib(5 V)    = (5 - 0.7) / 47k = 91 uA  -> hFE_min = 6.0 mA / 91 uA = 66
Ib(9 V)    = 177 uA, Ic = 14.5 mA     -> hFE_min = 82
Base reverse swing = -(Vcc - 0.7): 5 V -> -4.3 V (< V_EBO 6 V ok); 9 V -> -8.3 V (E-B avalanche)
```

---

## 7. Layout checklist (PCB phase)

- [ ] Rectangular outline, J1 on one short edge, mating side facing outward
- [ ] No copper (pour, tracks, pads) within 0.5 mm of Edge.Cuts (mouse-bite / V-cut safe)
- [ ] Each transistor's two pinout jumpers adjacent to that transistor, bridge side visible on top silk
- [ ] Timing caps: electrolytic + pad (square) at the collector net
- [ ] GND pour both layers, stitched; keep pour clear of solder-jumper gaps
- [ ] Silk: polarity marks for LEDs (K) and caps (+); "EBC / CBE" hint next to jumpers
- [ ] Courtyards non-overlapping (THT body sizes dominate: 5 mm cap, 3 mm LED)
- [ ] KiKit panel: rails on long edges, mouse bites, DRC clean

---

## 8. Design philosophy

- Build-with-what-you-have: every passive and the transistor accept THT or SMD; no part is single-source.
- Pinout-agnostic transistor via copper-only solder jumpers (no extra parts, no cost).
- Minimum board area first: vertical axial resistors (P2.54), tight 1.27 mm TO-92, 0805 lands tucked inside THT courtyards.
- Classic circuit kept as drawn: no base protection diodes, no extra decoupling.

---

## 9. Open questions / assumptions (user not available during design)

- [x] "transistor pad jumper" interpreted as pinout-select solder jumpers for the TO-92 outer legs (E-B-C vs C-B-E). Confirm.
- [x] "hybrid footprints" interpreted as THT + SMD on shared pads (R, C, LED, Q). Confirm.
- [x] Panelization: single board kept panel-friendly plus a KiKit preset / generated panel. Confirm panel count.
- [ ] Supply voltage: designed around 5 V, tolerates 3 to 9 V.
- [ ] LED colour: any; 470 R sized for red/green at 5 to 9 V.

---

## v2 (2026-10-21): single-sided home-etch variant

Same circuit, `kicad/astable_v2_single_layer/`. Bottom copper only (F.Cu rule area, no vias), THT only,
1.0 mm tracks / 0.6 mm clearance / 1.0 mm edge, pads 1.8 to 2.4 mm with 0.9 to 1.0 mm drills
(`kicad/lib/HomeEtch.pretty`). Rb and C selectable per stage with 2x3 headers (odd pins = common,
even pins = options), pinout select on 1x3 headers with the v1 pad semantics. Three wire links
(W1, W2 on GND, W3 on Q1_B) are modelled as series elements on sub-nets joined by net-tie footprints;
the pinout block is not single-layer planar (K3,3), so they are unavoidable. Transistor socket symbol
`AstableV2:Q_NPN_TO92_Socket` has pins L / B / R named for the holes.

## placement

```yaml
placement:
  orientation: horizontal
  aspect_ratio: 1.3
  pack_density: 0.75
  board_margin: 1.5
  region_order: [LV]
  anchors:
    J1: LV
  connector_access:
    J1: {mating_dir: "+Z", note: "vertical 2.54 mm pin header, mates from above; placed on the -X short edge so a right-angle header or wires can also leave the board"}
```

Placement intent (read with the brief): single LV domain, no isolation. Mirror-symmetric layout
around the board centre: Q1 / JP1 / JP2 / LED1 / R1 / R2 / C1 on the left half, Q2 / JP3 / JP4 /
LED2 / R4 / R3 / C2 on the right half, J1 on the left short edge. Timing caps between the two
transistors (each cap touches one collector and the other base). LEDs on the long edge away from J1.
Target outline about 24 x 18 mm, rectangular, no copper within 0.5 mm of the edge.

---

## Next steps

1. Phase 1 done (this file).
2. Phase 2 / 2.5 skipped (generic parts) - run `check_readiness.py` in generic mode for the sentinel.
3. Phase 3 `draw-schematic` -> `kicad/astable_multivibrator.py` -> .kicad_sch + ERC.
4. Phase 3.5 `check-schematic`.
5. Phase 4 `draw-pcb` -> placement loop -> route.
6. Phase 4.5 `check-pcb`.
7. Panel: `kicad/panel/kikit_preset.json` + `panelize.sh`.
8. Phase 5 `release`.
