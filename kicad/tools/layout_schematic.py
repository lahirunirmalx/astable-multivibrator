#!/usr/bin/env python3
"""Re-lay the generated (label-only) schematic as a classic wired drawing.

Reads the existing .kicad_sch, keeps every symbol instance UUID / reference /
value / footprint / pin UUID (so the PCB footprint links stay valid) and the
lib_symbols block, and writes a new sheet with symbols placed in the textbook
two-transistor astable arrangement, wired, with one net label per net so the
net names stay identical to the routed PCB.

Usage:
    python3 kicad/tools/layout_schematic.py [in.kicad_sch] [out.kicad_sch]
Verify afterwards with kicad-cli sch erc + the netlist compare in
kicad/tools/compare_netlist.py.
"""
import re
import sys
import uuid as uuidlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "astable_multivibrator" / "astable_multivibrator.kicad_sch"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else SRC


# ------------------------------------------------------------------ s-expr
def parse(text):
    tok = re.findall(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+', text)
    pos = 0

    def node():
        nonlocal pos
        t = tok[pos]
        pos += 1
        if t == "(":
            out = []
            while tok[pos] != ")":
                out.append(node())
            pos += 1
            return out
        if t.startswith('"'):
            return t[1:-1].replace('\\"', '"')
        return t
    return node()


def find_all(lst, key):
    return [x for x in lst if isinstance(x, list) and x and x[0] == key]


def find(lst, key):
    r = find_all(lst, key)
    return r[0] if r else None


def block_text(text, key):
    """Raw text of the first top-level (key ...) block."""
    i = text.index(f"\n\t({key}")
    depth = 0
    for j in range(i + 1, len(text)):
        c = text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1:j + 1]
    raise ValueError(key)


src_text = SRC.read_text()
tree = parse(src_text)
ROOT_UUID = find(tree, "uuid")[1]
LIB_SYMBOLS = block_text(src_text, "lib_symbols")

parts = {}
for sym in find_all(tree, "symbol"):
    props = {p[1]: p[2] for p in find_all(sym, "property")}
    pins = {p[1]: find(p, "uuid")[1] for p in find_all(sym, "pin")}
    parts[props["Reference"]] = dict(
        lib_id=find(sym, "lib_id")[1], uuid=find(sym, "uuid")[1],
        value=props.get("Value", ""), footprint=props.get("Footprint", ""),
        datasheet=props.get("Datasheet", "~"), pins=pins)

# ------------------------------------------------------------------ geometry
# pin offsets from the symbol anchor, library coordinates (y up)
PIN_LIB = {
    "Device:R": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:LED": {"1": (-3.81, 0), "2": (3.81, 0)},
    "Device:C_Polarized": {"1": (0, 3.81), "2": (0, -3.81)},
    "Hybrid:Q_NPN_Hybrid": {"2": (-5.08, 0), "3": (2.54, 5.08), "1": (2.54, -5.08),
                            "4": (-5.08, 5.08), "5": (-5.08, -5.08)},
    "Jumper:SolderJumper_3_Bridged12": {"1": (-5.08, 0), "2": (0, -3.81), "3": (5.08, 0)},
    "Connector_Generic:Conn_01x02": {"1": (-5.08, 0), "2": (-5.08, -2.54)},
    "power:VCC": {"1": (0, 0)},
    "power:GND": {"1": (0, 0)},
    "power:PWR_FLAG": {"1": (0, 0)},
}


def pin_pos(lib_id, number, at, rot, mirror=None):
    x, y = PIN_LIB[lib_id][number]
    if mirror == "y":
        x = -x
    if mirror == "x":
        y = -y
    r = rot % 360
    if r == 90:
        x, y = -y, x
    elif r == 180:
        x, y = -x, -y
    elif r == 270:
        x, y = y, -x
    return (round(at[0] + x, 2), round(at[1] - y, 2))


def r2(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


# ------------------------------------------------------------------ placement
X_L1, X_L2, X_R2, X_R1 = 60.96, 91.44, 142.24, 172.72   # columns
Y_VCC, Y_GND = 38.1, 93.98
Y_R, Y_LED, Y_Q = 45.72, 58.42, 78.74
Y_C1, Y_C2 = 66.04, 71.12
X_C = 116.84
X_C1, X_C2 = 106.68, 127.0
Y_JP = 118.11

placed = {   # ref -> (x, y, rot, mirror)
    "J1":   (33.02, Y_VCC, 0, "y"),
    "R1":   (X_L1, Y_R, 0, None), "R2": (X_L2, Y_R, 0, None),
    "R3":   (X_R2, Y_R, 0, None), "R4": (X_R1, Y_R, 0, None),
    "LED1": (X_L1, Y_LED, 90, None), "LED2": (X_R1, Y_LED, 90, None),
    "Q1":   (X_L1 + 2.54, Y_Q, 0, "y"), "Q2": (X_R1 - 2.54, Y_Q, 0, None),
    "C1":   (X_C1, Y_C1, 90, None),      # pin1 (+) left  -> Q1_C
    "C2":   (X_C2, Y_C2, 270, None),     # pin1 (+) right -> Q2_C
    "JP1":  (55.88, Y_JP, 0, None), "JP2": (96.52, Y_JP, 0, None),
    "JP3":  (137.16, Y_JP, 0, None), "JP4": (177.8, Y_JP, 0, None),
}

P = {}   # (ref, pin) -> position
for ref, (x, y, rot, mir) in placed.items():
    for n in PIN_LIB[parts[ref]["lib_id"]]:
        P[(ref, n)] = pin_pos(parts[ref]["lib_id"], n, (x, y), rot, mir)

# power symbols (not in the source file as instances with refs we care about)
power = []   # (lib_id, ref, x, y, rot)
wires = []   # ((x0,y0),(x1,y1))
labels = []  # (text, x, y, rot, justify)


def W(a, b):
    wires.append((a, b))


def L(text, x, y, rot=0, justify="left"):
    labels.append((text, x, y, rot, justify))


# VCC rail and J1
W(P[("J1", "1")], (50.8, Y_VCC)); W((50.8, Y_VCC), (X_L1, Y_VCC)); W((X_L1, Y_VCC), (X_L2, Y_VCC))
power.append(("power:PWR_FLAG", "#FLG01", 50.8, Y_VCC, 0)); W((X_L2, Y_VCC), (X_C, Y_VCC))
W((X_C, Y_VCC), (X_R2, Y_VCC)); W((X_R2, Y_VCC), (X_R1, Y_VCC))
power.append(("power:VCC", "#PWR01", X_C, Y_VCC, 0))
# GND rail and J1
j1g = P[("J1", "2")]
W(j1g, (45.72, j1g[1])); W((45.72, j1g[1]), (45.72, Y_GND)); W((45.72, Y_GND), (53.34, Y_GND)); W((53.34, Y_GND), (X_L1, Y_GND))
power.append(("power:PWR_FLAG", "#FLG02", 53.34, Y_GND, 180))
W((X_L1, Y_GND), (X_C, Y_GND)); W((X_C, Y_GND), (X_R1, Y_GND))
power.append(("power:GND", "#PWR02", X_C, Y_GND, 0))
# resistors from rail
for r in ("R1", "R2", "R3", "R4"):
    W((P[(r, "1")][0], Y_VCC), P[(r, "1")])
# left column: R1 -> LED1 -> Q1 collector, with C1 tap
W(P[("R1", "2")], P[("LED1", "2")]); L("LED1_A", X_L1, 52.07)
W(P[("LED1", "1")], (X_L1, Y_C1)); W((X_L1, Y_C1), P[("Q1", "3")]); L("Q1_C", X_L1, 64.77)
W(P[("Q1", "1")], (X_L1, Y_GND))
# right column: R4 -> LED2 -> Q2 collector, with C2 tap
W(P[("R4", "2")], P[("LED2", "2")]); L("LED2_A", X_R1, 52.07)
W(P[("LED2", "1")], (X_R1, Y_C2)); W((X_R1, Y_C2), P[("Q2", "3")]); L("Q2_C", X_R1, 64.77)
W(P[("Q2", "1")], (X_R1, Y_GND))
# base columns
W(P[("R2", "2")], (X_L2, Y_C2)); W((X_L2, Y_C2), (X_L2, Y_Q)); W((X_L2, Y_Q), P[("Q1", "2")]); L("Q1_B", 73.66, Y_Q)
W(P[("R3", "2")], (X_R2, Y_C1)); W((X_R2, Y_C1), (X_R2, Y_Q)); W((X_R2, Y_Q), P[("Q2", "2")]); L("Q2_B", 149.86, Y_Q)
# cross-coupling caps
W((X_L1, Y_C1), P[("C1", "1")]); W(P[("C1", "2")], (X_R2, Y_C1))
W((X_R1, Y_C2), P[("C2", "1")]); W(P[("C2", "2")], (X_L2, Y_C2))
# TO-92 outer legs
W(P[("Q1", "4")], (76.2, P[("Q1", "4")][1])); L("Q1_TL", 76.2, P[("Q1", "4")][1])
W(P[("Q1", "5")], (76.2, P[("Q1", "5")][1])); L("Q1_TR", 76.2, P[("Q1", "5")][1])
W(P[("Q2", "4")], (157.48, P[("Q2", "4")][1])); L("Q2_TL", 157.48, P[("Q2", "4")][1], 0, "right")
W(P[("Q2", "5")], (157.48, P[("Q2", "5")][1])); L("Q2_TR", 157.48, P[("Q2", "5")][1], 0, "right")
# pinout jumpers: pad1 / pad3 nets, pad2 = TO-92 leg
JP = {"JP1": ("GND", "Q1_TL", "Q1_C"), "JP2": ("Q1_C", "Q1_TR", "GND"),
      "JP3": ("GND", "Q2_TL", "Q2_C"), "JP4": ("Q2_C", "Q2_TR", "GND")}
pwr_n = 3
for jp, (n1, n2, n3) in JP.items():
    p1, p2, p3 = P[(jp, "1")], P[(jp, "2")], P[(jp, "3")]
    for pin, net, dx in ((p1, n1, -5.08), (p3, n3, 5.08)):
        end = (round(pin[0] + dx, 2), pin[1])
        W(pin, end)
        if net == "GND":
            down = (end[0], end[1] + 5.08)
            W(end, down)
            power.append(("power:GND", f"#PWR{pwr_n:02d}", down[0], down[1], 0)); pwr_n += 1
        else:
            L(net, end[0], end[1], 0, "left" if dx > 0 else "right")
    end = (p2[0], p2[1] + 5.08)
    W(p2, end); L(n2, end[0], end[1], 270)

# junctions: nodes touched by 3 or more wire ends / pins
from collections import Counter
deg = Counter()
for a, b in wires:
    deg[a] += 1; deg[b] += 1
for (ref, n), pos in P.items():
    deg[pos] += 1
for lib, ref, x, y, rot in power:
    deg[(x, y)] += 1
junctions = [pt for pt, d in deg.items() if d >= 3]

# ------------------------------------------------------------------ emit
out = []
A = out.append
A('(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")')
A(f'\t(uuid "{ROOT_UUID}")\n\t(paper "A4")')
A('\t(title_block\n\t\t(title "Astable multivibrator LED flasher")\n\t\t(date "2026-10-21")\n\t\t(rev "1.0")'
  '\n\t\t(company "MIT licensed hobby project")\n\t\t(comment 1 "Hybrid THT / SMD footprints; TO-92 pinout selected by solder jumpers")\n\t)')
PWR_FLAG_LIB = Path("/usr/share/kicad/symbols/power.kicad_sym").read_text()
i = PWR_FLAG_LIB.index('\t(symbol "PWR_FLAG"')
depth = 0
for j in range(i, len(PWR_FLAG_LIB)):
    if PWR_FLAG_LIB[j] == "(":
        depth += 1
    elif PWR_FLAG_LIB[j] == ")":
        depth -= 1
        if depth == 0:
            break
flag = PWR_FLAG_LIB[i:j + 1].replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)
A(LIB_SYMBOLS[:-1].rstrip() + "\n" + flag + "\n\t)")


def effects(justify=None, hide=False, size=1.27):
    s = f"(effects (font (size {size} {size}))"
    if justify:
        s += f" (justify {justify})"
    if hide:
        s += " (hide yes)"
    return s + ")"


for (x0, y0), (x1, y1) in wires:
    A(f'\t(wire (pts (xy {r2(x0)} {r2(y0)}) (xy {r2(x1)} {r2(y1)})) (stroke (width 0) (type default)) (uuid "{uuidlib.uuid4()}"))')
for (x, y) in junctions:
    A(f'\t(junction (at {r2(x)} {r2(y)}) (diameter 0) (color 0 0 0 0) (uuid "{uuidlib.uuid4()}"))')
for text, x, y, rot, justify in labels:
    A(f'\t(label "{text}" (at {r2(x)} {r2(y)} {rot}) {effects(justify + " bottom")} (uuid "{uuidlib.uuid4()}"))')

NOTES = [
    "Two-transistor astable multivibrator, LEDs flash alternately.",
    "f = 1 / (1.386 * Rb * C) = 1.5 Hz with Rb = 47k, C = 10 uF.  Supply 3 to 9 V (5 V recommended).",
    "Every R / C / LED / Q position is a hybrid footprint: fit the THT part OR the 0805 / SOT-23 part.",
    "JP1..JP4 select the TO-92 outer-leg pinout: bridged 1-2 (factory) = E-B-C (2N3904, PN2222, S8050);",
    "cut 1-2 and bridge 2-3 = C-B-E (BC547, BC548, BC337). SOT-23 parts ignore the jumpers.",
]
for i, line in enumerate(NOTES):
    A(f'\t(text "{line}" (exclude_from_sim no) (at 33.02 {r2(137.16 + i * 3.81)} 0) {effects("left bottom", size=1.5)} (uuid "{uuidlib.uuid4()}"))')
A(f'\t(text "Pinout select (per transistor): pad 1 = GND (E), pad 2 = TO-92 outer leg, pad 3 = collector" (exclude_from_sim no) (at 33.02 {r2(Y_JP - 10.16)} 0) {effects("left bottom", size=1.5)} (uuid "{uuidlib.uuid4()}"))')


def emit_symbol(ref, lib_id, suid, x, y, rot, mirror, value, footprint, datasheet, pins, ref_at, val_at, in_bom=True, hide_value=False):
    pa = (360 - rot) % 360
    A('\t(symbol')
    A(f'\t\t(lib_id "{lib_id}")')
    A(f'\t\t(at {r2(x)} {r2(y)} {rot})')
    if mirror:
        A(f'\t\t(mirror {mirror})')
    A('\t\t(unit 1)\n\t\t(exclude_from_sim no)')
    A(f'\t\t(in_bom {"yes" if in_bom else "no"})\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced no)')
    A(f'\t\t(uuid "{suid}")')
    hide_ref = ref.startswith("#")
    A(f'\t\t(property "Reference" "{ref}" (at {r2(ref_at[0])} {r2(ref_at[1])} {pa}) {effects("left", hide=hide_ref)})')
    A(f'\t\t(property "Value" "{value}" (at {r2(val_at[0])} {r2(val_at[1])} {pa}) {effects("left", hide=hide_ref or hide_value)})')
    A(f'\t\t(property "Footprint" "{footprint}" (at {r2(x)} {r2(y)} 0) {effects(hide=True)})')
    A(f'\t\t(property "Datasheet" "{datasheet}" (at {r2(x)} {r2(y)} 0) {effects(hide=True)})')
    A(f'\t\t(property "Description" "" (at {r2(x)} {r2(y)} 0) {effects(hide=True)})')
    for n, puid in pins.items():
        A(f'\t\t(pin "{n}" (uuid "{puid}"))')
    A(f'\t\t(instances (project "astable_multivibrator" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))')
    A('\t)')


for ref, (x, y, rot, mir) in placed.items():
    p = parts[ref]
    lib = p["lib_id"]
    if lib in ("Device:R", "Device:C_Polarized") and rot == 0:
        ref_at, val_at = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27)
    elif lib == "Device:C_Polarized":
        ref_at, val_at = (x - 1.27, y - 3.81), (x - 1.27, y + 5.08)
    elif lib == "Device:LED":
        ref_at, val_at = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27)
    elif lib == "Hybrid:Q_NPN_Hybrid":
        ref_at, val_at = ((x - 10.16, y - 1.27), (x - 10.16, y + 1.27)) if mir else ((x + 5.08, y - 1.27), (x + 5.08, y + 1.27))
    elif lib.startswith("Jumper:"):
        ref_at, val_at = (x - 3.81, y - 5.08), (x + 7.62, y + 2.54)
    else:  # J1
        ref_at, val_at = (x - 7.62, y - 5.08), (x - 7.62, y + 5.08)
    emit_symbol(ref, lib, p["uuid"], x, y, rot, mir, p["value"], p["footprint"], p["datasheet"], p["pins"], ref_at, val_at,
                hide_value=lib.startswith("Jumper:"))

for lib, ref, x, y, rot in power:
    name = lib.split(":")[1]
    emit_symbol(ref, lib, str(uuidlib.uuid4()), x, y, rot, None, name, "", "", {"1": str(uuidlib.uuid4())},
                (x + 2.54, y - 5.08 if name != "GND" else y + 5.08), (x + 2.54, y - 2.54 if name != "GND" else y + 2.54),
                in_bom=False)

A(f'\t(sheet_instances (path "/" (page "1")))')
A(')')
DST.write_text("\n".join(out) + "\n")
print(f"wrote {DST}: {len(placed)} parts, {len(power)} power symbols, {len(wires)} wires, {len(junctions)} junctions, {len(labels)} labels")
