# Assembly guide - astable multivibrator LED flasher

Board: `kicad/astable_multivibrator/astable_multivibrator.kicad_pcb`, 26.15 x 21.73 mm, 2 layers.
Panel: `kicad/panel/astable_multivibrator_panel.kicad_pcb`, 2 x 4 with mouse bites.
Regenerate the panel with `kicad/panel/panelize.sh` (ROWS / COLS env override).

![board](../images/pcb_3d_top.png)

## 1. Pick one part per position

Every position is hybrid. Fit EITHER the through-hole part OR the SMD part, never both.

| Ref | THT option | SMD option | Polarity |
|---|---|---|---|
| R1, R4 (470 R) | axial 0207 or 0204, stood vertical on 2.54 mm pitch | 0805, lands sit on the ring tops just below the holes | none |
| R2, R3 (47k) | same | same | none |
| C1, C2 (10 uF) | radial 5 mm electrolytic, 2.5 mm pitch, 16 V or more | 0805 X5R / X7R 10 uF 16 V | THT: square pad = +, the silk hatch marks the - side. SMD: none |
| LED1, LED2 | 3 mm LED, 2.54 mm pitch | 0805 LED | square pad and silk flat = cathode (K). SMD land 1 (toward the transistor) = K |
| Q1, Q2 | TO-92 in the three holes (1.27 mm inline), flat face toward the jumpers / bottom edge (silk line under the holes) | SOT-23 on the three lands above the holes, pin 1 (B) on the land nearest the centre hole | see section 2 |
| J1 | 1x2 2.54 mm header, or wires soldered straight in | - | square pad = VCC |

## 2. Set the transistor pinout jumpers

JP1 / JP2 belong to Q1, JP3 / JP4 to Q2. They sit right under each transistor,
left jumper = left leg. The TO-92 centre hole is always the base; the outer
holes go through the jumpers.

| TO-92 pinout (flat face toward you, legs down, left to right) | Parts | What to do |
|---|---|---|
| E-B-C | 2N3904, 2N4401, PN2222, S8050, 2N2222 plastic | nothing: jumpers are factory-bridged 1-2 |
| C-B-E | BC547, BC548, BC549, BC337, BC546 | on both jumpers of that transistor: cut the 1-2 trace with a knife, bridge 2-3 with a solder blob |
| SOT-23 (B-E-C) | MMBT3904, BC847, MMBT2222, SS8050 | jumpers do not matter |

Jumper pads: 1 = GND (emitter), 2 = centre = the TO-92 outer leg, 3 = collector.
The designators JP1..JP4 are on the Fab layer only (no silk room); the small
arrow on the silk marks pad 1.

Check with a multimeter after cutting: pad 1 to pad 2 should read open, pad 2
to pad 3 should read a short.

## 3. Solder in this order

1. SMD parts, if any (0805 and SOT-23). They sit inside the THT courtyards, so
   do them before anything tall is in the way.
2. Pinout jumpers (cut / bridge as above).
3. Transistors, LEDs (short leads first, mind the flat side).
4. Resistors stood vertical: bend one lead back over the body, insert, solder.
5. Electrolytic caps (long lead = + = square pad).
6. J1 header, or wires.

If the board came out of the panel, sand the mouse-bite nubs on the long edges
flat first; R1 to R4 and the jumpers sit about 0.85 mm from the edge.

## 4. Power up

- 3 to 9 V DC on J1, square pad = +. 5 V recommended (USB works).
- Both LEDs flash alternately at about 1.5 Hz. Nothing flashing: check the
  transistor pinout and jumpers first, then LED polarity, then cap polarity.
- Only one LED on steady: the transistor on that side never switches; its
  base resistor (R2 or R3) or timing cap (C1 or C2) is open or wrong.
- Current draw is about 10 mA at 5 V.

## 5. Change the speed

Period is about 1.4 * Rb * C. With 47k:

| C1 = C2 | Flash rate |
|---|---|
| 4.7 uF | about 3.5 Hz |
| 10 uF | about 1.5 Hz (as designed, simulated 1.8 Hz at 5 V) |
| 22 uF | about 0.7 Hz |
| 47 uF | about 0.3 Hz |

Keep R2 / R3 between 22k and 100k so the transistors still saturate.
