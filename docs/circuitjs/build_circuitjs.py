#!/usr/bin/env python3
"""Build the CircuitJS (falstad.com) version of the astable multivibrator.

Uses the circuit-sim skill helper (~/.claude/skills/circuit-sim/circuitjs.py). Writes
docs/circuitjs/astable_multivibrator.txt (File > Import From Text fallback) and
astable_multivibrator.url.txt (the link). Values are the v1 / v2 default pair 47k / 10 uF.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/circuit-sim"))
from circuitjs import Circuit, HEADER_50HZ

ck = Circuit("$ 1 0.0005 10.20027730826997 50 5 50")   # 0.5 ms step: slow circuit
# supply: 5 V, + on the top rail
ck.vdc(96, 320, 96, 64, 5)
ck.gnd(96, 320, 96, 352)
# top rail with taps for R1, R2, R3, R4 and the bottom rail for both emitters
ck.rail(64, [96, 160, 208, 400, 448])
ck.rail(320, [96, 240, 368])
# stage 1: R1 -> LED1 -> Q1 collector; R2 -> base
ck.r(160, 64, 160, 160, 470)
ck.led(160, 160, 160, 224, rgb=(1, 0, 0), imax=0.02)
ck.w(160, 224, 192, 224); ck.w(192, 224, 240, 224)          # LED1 K -> Q1 collector (tap at 192 for C1)
ck.npn(208, 240, 240, 240, beta=200)                         # base (208,240), C (240,224), E (240,256)
ck.w(240, 256, 240, 320)
ck.r(208, 64, 208, 240, 47000)                               # R2
# stage 2: mirrored
ck.r(448, 64, 448, 160, 470)
ck.led(448, 160, 448, 224, rgb=(1, 0, 0), imax=0.02)
ck.w(448, 224, 416, 224); ck.w(416, 224, 368, 224)          # LED2 K -> Q2 collector (tap at 416 for C2)
ck.npn(400, 240, 368, 240, beta=200)                         # base (400,240), C (368,224), E (368,256)
ck.w(368, 256, 368, 320)
ck.r(400, 64, 400, 240, 47000)                               # R3
# cross coupling: C1 from Q1 collector to Q2 base (over the top), C2 from Q2 collector to Q1 base (below)
ck.c(192, 224, 192, 176, 10e-6)
ck.w(192, 176, 384, 176); ck.w(384, 176, 384, 240); ck.w(384, 240, 400, 240)
ck.c(416, 224, 416, 288, 10e-6)
ck.w(416, 288, 224, 288); ck.w(224, 288, 224, 240); ck.w(224, 240, 208, 240)
ck.note(96, 400, 96, 400, "Astable multivibrator LED flasher, 47k / 10 uF, about 1.5 Hz. Change R2, R3, C1, C2 to match the JR / JC headers on the v2 board.", size=14)
here = Path(__file__).resolve().parent
ck.save("astable_multivibrator", str(here))
# ctz= (LZ-string, what falstad's own share button emits) survives the URL transport; cct= does not carry $ , / reliably
url = ck.ctz_url()
(here / "astable_multivibrator.url.txt").write_text(url + "\n")
print(url[:80] + "...", len(url), "chars")
