#!/usr/bin/env python3
"""ngspice sweep of the v2 RC options: 3 base resistors x 3 timing caps at 5 V and 9 V.

Writes one deck per combination into docs/spice/decks/ and prints a markdown table of the
measured period / frequency / LED peak current. Model: generic 2N3904-class NPN, red LED
(same as docs/astable_fullcircuit.cir). Run: python3 docs/spice/v2_timing_sweep.py
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
DECKS = HERE / "decks"
DECKS.mkdir(exist_ok=True)
RB = [("22k", 22e3), ("47k", 47e3), ("100k", 100e3)]
CT = [("4.7uF", 4.7e-6), ("10uF", 10e-6), ("47uF", 47e-6)]

DECK = """* astable v2 timing sweep: Rb={rb} C={c} Vcc={vcc}
Vcc vcc 0 {vcc}
R1 vcc led1a 470
D1 led1a q1c LEDRED
R4 vcc led2a 470
D2 led2a q2c LEDRED
R2 vcc q1b {rbv}
R3 vcc q2b {rbv}
C1 q1c q2b {cv}
C2 q2c q1b {cv2}
Q1 q1c q1b 0 NPNGP
Q2 q2c q2b 0 NPNGP
.model NPNGP NPN(IS=6.7e-15 BF=200 VAF=74 IKF=0.08 ISE=6.7e-15 NE=1.3 BR=4 RB=10 RC=1 CJE=4.5p CJC=3.5p TF=0.4n TR=240n)
.model LEDRED D(IS=1e-18 N=1.8 RS=2 CJO=20p)
.tran {step} {tstop} 0 {step} uic
.control
set noaskquit
run
wrdata {wave} v(q1c) v(led1a)
.endc
.end
"""


def measure(wave_file, vcc):
    """Mean period from rising 2 V crossings in the second half of the run, LED peak current."""
    t, v, va = [], [], []
    for line in Path(wave_file).read_text().splitlines():
        parts = line.split()
        if len(parts) >= 4:
            t.append(float(parts[0])); v.append(float(parts[1])); va.append(float(parts[3]))
    rises = [t[i] for i in range(1, len(t)) if v[i - 1] < 2.0 <= v[i] and t[i] > t[-1] / 2]
    period = (rises[-1] - rises[0]) / (len(rises) - 1) if len(rises) >= 3 else float("nan")
    i_led = max((vcc - a) / 470 for a in va[len(va) // 2:]) * 1e3
    swing = max(v) - min(v[len(v) // 2:])
    return period, i_led, len(rises)

rows = []
for vcc in (5, 9):
    for rb, rbv in RB:
        for c, cv in CT:
            t_est = 1.386 * rbv * cv          # textbook period
            tstop = max(2.0, 14 * t_est)
            f = DECKS / f"v2_{vcc}V_{rb}_{c}.cir"
            wave = DECKS / f"v2_{vcc}V_{rb}_{c}.txt"
            deck = DECK.format(rb=rb, c=c, vcc=vcc, rbv=rbv, cv=cv, cv2=cv * 1.05,
                               step=max(2e-4, t_est / 2000), tstop=tstop, wave=wave.name)
            f.write_text(deck)
            subprocess.run(["ngspice", "-b", f.name], capture_output=True, text=True, cwd=DECKS)
            per, i_led, n = measure(wave, vcc)
            wave.unlink()
            rows.append((vcc, rb, c, 1 / t_est, 1 / per if per == per else float("nan"), per, i_led, n))

print("| Vcc | Rb | C | f textbook (Hz) | f ngspice (Hz) | period (s) | LED peak (mA) | cycles measured |")
print("|---|---|---|---|---|---|---|---|")
for vcc, rb, c, ft, fr, per, i_led, n in rows:
    if fr > 3 * ft or n > 50:      # relaxation oscillation collapsed: transistor cannot saturate
        print(f"| {vcc} V | {rb} | {c} | {ft:.2f} | unstable (does not saturate) | - | {i_led:.1f} | - |")
    else:
        print(f"| {vcc} V | {rb} | {c} | {ft:.2f} | {fr:.2f} | {per:.3f} | {i_led:.1f} | {n} |")
