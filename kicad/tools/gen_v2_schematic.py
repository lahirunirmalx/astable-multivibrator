#!/usr/bin/env python3
"""Generate the v2 (single-sided, home-etch, selectable RC) schematic from scratch.

Writes kicad/astable_v2_single_layer/astable_v2.kicad_sch plus the project lib tables.
Symbols come from the KiCad system libraries and kicad/lib/AstableV2.kicad_sym; every
part has a fixed UUID derived from its reference so re-running keeps the PCB links valid.

    python3 kicad/tools/gen_v2_schematic.py
Then: kicad-cli sch erc --severity-all --exit-code-violations <sch>
"""
import re
import uuid as uuidlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRJ = ROOT / "astable_v2_single_layer"
SCH = PRJ / "astable_v2.kicad_sch"
SYSLIB = Path("/usr/share/kicad/symbols")
NS = uuidlib.UUID("7a2f0d3c-5b1e-4c7a-9d2e-aa5533770001")
ROOT_UUID = str(uuidlib.uuid5(NS, "root"))


def uid(key):
    return str(uuidlib.uuid5(NS, key))


# ------------------------------------------------------------------ symbol library text
def sym_text(path, name):
    t = Path(path).read_text()
    i = t.index(f'\t(symbol "{name}"\n')
    d = 0
    for j in range(i, len(t)):
        if t[j] == "(":
            d += 1
        elif t[j] == ")":
            d -= 1
            if d == 0:
                return t[i:j + 1]
    raise ValueError(name)


LIBS = {
    "Device:R": (SYSLIB / "Device.kicad_sym", "R"),
    "Device:C_Polarized": (SYSLIB / "Device.kicad_sym", "C_Polarized"),
    "Device:LED": (SYSLIB / "Device.kicad_sym", "LED"),
    "Connector_Generic:Conn_01x02": (SYSLIB / "Connector_Generic.kicad_sym", "Conn_01x02"),
    "Connector_Generic:Conn_01x03": (SYSLIB / "Connector_Generic.kicad_sym", "Conn_01x03"),
    "Connector_Generic:Conn_02x03_Odd_Even": (SYSLIB / "Connector_Generic.kicad_sym", "Conn_02x03_Odd_Even"),
    "Jumper:Jumper_2_Bridged": (SYSLIB / "Jumper.kicad_sym", "Jumper_2_Bridged"),
    "power:VCC": (SYSLIB / "power.kicad_sym", "VCC"),
    "power:GND": (SYSLIB / "power.kicad_sym", "GND"),
    "power:PWR_FLAG": (SYSLIB / "power.kicad_sym", "PWR_FLAG"),
    "AstableV2:Q_NPN_TO92_Socket": (ROOT / "lib" / "AstableV2.kicad_sym", "Q_NPN_TO92_Socket"),
}
LIB_TEXT, PINS = {}, {}
for lib_id, (path, name) in LIBS.items():
    s = sym_text(path, name)
    assert "(extends" not in s, lib_id
    LIB_TEXT[lib_id] = s.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    PINS[lib_id] = {n: (float(x), float(y)) for x, y, n in
                    re.findall(r'\(pin \w+ \w+\s*\n\s*\(at ([-\d.]+) ([-\d.]+) \d+\)[\s\S]*?\(number "([^"]*)"', s)}

# ------------------------------------------------------------------ geometry helpers
def pin_pos(lib_id, number, at, rot, mirror=None):
    x, y = PINS[lib_id][number]
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
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ------------------------------------------------------------------ parts
parts = {}      # ref -> dict(lib, value, fp, at, rot, mirror, ref_at, val_at, hide_value)
wires, labels, junctions, texts = [], [], [], []
P = {}


def part(ref, lib, value, fp, at, rot=0, mirror=None, ref_at=None, val_at=None, hide_value=False, in_bom=True):
    x, y = at
    parts[ref] = dict(lib=lib, value=value, fp=fp, at=at, rot=rot, mirror=mirror, in_bom=in_bom,
                      ref_at=ref_at or (x + 2.54, y - 1.27), val_at=val_at or (x + 2.54, y + 1.27), hide_value=hide_value)
    for n in PINS[lib]:
        P[(ref, n)] = pin_pos(lib, n, at, rot, mirror)


def W(a, b):
    if a != b:
        wires.append((a, b))


def L(text, x, y, rot=0, justify="left"):
    labels.append((text, x, y, rot, justify))


def T(text, x, y, size=1.5):
    texts.append((text, x, y, size))


pwr_n = [0]


def power(lib, x, y, rot=0):
    pwr_n[0] += 1
    ref = ("#FLG%02d" if lib.endswith("PWR_FLAG") else "#PWR%02d") % pwr_n[0]
    name = lib.split(":")[1]
    part(ref, lib, name, "", (x, y), rot, in_bom=False,
         ref_at=(x + 2.54, y - 5.08), val_at=(x + 2.54, y - 2.54 if name != "GND" else y + 3.81))


FP = {
    "R": "HomeEtch:R_Axial_P10.16mm_HomeEtch", "C": "HomeEtch:CP_Radial_D6.3mm_P2.50mm_HomeEtch",
    "LED": "HomeEtch:LED_D3.0mm_P2.54mm_HomeEtch", "Q": "HomeEtch:TO-92_P2.54mm_HomeEtch",
    "H2": "HomeEtch:PinHeader_1x02_P2.54mm_HomeEtch", "H3": "HomeEtch:PinHeader_1x03_P2.54mm_HomeEtch",
    "H6": "HomeEtch:PinHeader_2x03_P2.54mm_HomeEtch", "W": "HomeEtch:WireLink_P12.70mm_HomeEtch",
    "W3": "HomeEtch:WireLink_P7.62mm_HomeEtch",
}
RB_VALUES = ("22k", "47k", "100k")
C_VALUES = ("4.7uF", "10uF", "47uF")

Y_VCC, Y_R, Y_LED, Y_Q = 38.1, 45.72, 58.42, 78.74


def stage(n, ox):
    """One transistor stage: Rc + LED + TO-92 socket + Rb select header + three Rb options."""
    rc, led, q, jr = (f"R{n}" if n == 1 else "R4"), f"LED{n}", f"Q{n}", f"JR{n}"
    rbs = [f"R{n + 1}{i}" for i in (1, 2, 3)]          # R21 R22 R23 / R31 R32 R33
    x_rc, x_q, x_jr = ox + 5.08, ox + 15.24, ox + 35.56
    x_rb = [ox + 50.8, ox + 58.42, ox + 66.04]
    rail_x0 = ox - 5.08 if n == 1 else x_rc
    # VCC rail (split at every tap)
    taps = sorted({rail_x0, ox, x_rc, ox + 33.02, *x_rb}) if n == 1 else sorted({x_rc, ox + 33.02, *x_rb})
    for a, b in zip(taps, taps[1:]):
        W((a, Y_VCC), (b, Y_VCC))
    power("power:VCC", ox + 33.02, Y_VCC)
    # collector resistor + LED
    part(rc, "Device:R", "470", FP["R"], (x_rc, Y_R))
    W((x_rc, Y_VCC), P[(rc, "1")])
    part(led, "Device:LED", "LED_RED", FP["LED"], (x_rc, Y_LED), 90, ref_at=(x_rc + 2.54, Y_LED - 1.27), val_at=(x_rc + 2.54, Y_LED + 1.27))
    W(P[(rc, "2")], P[(led, "2")]); L(f"LED{n}_A", x_rc, 52.07)
    W(P[(led, "1")], (x_rc, 68.58)); L(f"Q{n}_C", x_rc, 68.58)
    # TO-92 socket, base toward the header on the right
    part(q, "AstableV2:Q_NPN_TO92_Socket", "NPN", FP["Q"], (x_q, Y_Q), 0, "y",
         ref_at=(x_q + 1.27, Y_Q + 6.35), val_at=(x_q + 1.27, Y_Q + 8.89))
    for leg, net in (("3", f"Q{n}_TR"), ("1", f"Q{n}_TL")):
        px, py = P[(q, leg)]
        W((px, py), (px - 3.81, py)); L(net, px - 3.81, py, 0, "right")
    # Rb select header: odd pins = base, even pins = options
    part(jr, "Connector_Generic:Conn_02x03_Odd_Even", "RB_SEL", FP["H6"], (x_jr, Y_Q), ref_at=(x_jr - 2.54, Y_Q - 6.35), val_at=(x_jr - 2.54, Y_Q + 6.35))
    bx = x_jr - 7.62
    W(P[(q, "2")], (bx, Y_Q)); W((bx, Y_Q), P[(jr, "3")]); L(f"Q{n}_B", P[(q, "2")][0] + 1.905, Y_Q)
    W(P[(jr, "1")], (bx, P[(jr, "1")][1])); W((bx, P[(jr, "1")][1]), (bx, Y_Q))
    W(P[(jr, "5")], (bx, P[(jr, "5")][1])); W((bx, P[(jr, "5")][1]), (bx, Y_Q))
    for rb, xr, pin, val in zip(rbs, x_rb, ("2", "4", "6"), RB_VALUES):
        part(rb, "Device:R", val, FP["R"], (xr, Y_R))
        W((xr, Y_VCC), P[(rb, "1")])
        py = P[(jr, pin)][1]
        W(P[(rb, "2")], (xr, py)); W((xr, py), P[(jr, pin)])
    T(f"Stage {n}: Rb select JR{n}, shunt on one column pair", ox - 5.08 if n == 1 else x_rc, 30.48)


def cap_block(n, cx, cy, common, other, link=None):
    jc = f"JC{n}"
    caps = [f"C{n}{i}" for i in (1, 2, 3)]
    part(jc, "Connector_Generic:Conn_02x03_Odd_Even", "C_SEL", FP["H6"], (cx, cy), ref_at=(cx - 2.54, cy - 6.35), val_at=(cx - 2.54, cy + 6.35))
    bx = cx - 7.62
    for pin in ("1", "3", "5"):
        W(P[(jc, pin)], (bx, P[(jc, pin)][1]))
    W((bx, cy - 2.54), (bx, cy)); W((bx, cy), (bx, cy + 2.54))
    W((bx, cy), (bx - 5.08, cy)); L(common, bx - 5.08, cy, 0, "right")
    ccx = cx + 17.78
    rows = (cy - 7.62, cy, cy + 7.62)
    for cap, pin, row, val in zip(caps, ("2", "4", "6"), rows, C_VALUES):
        part(cap, "Device:C_Polarized", val, FP["C"], (ccx, row), 90, ref_at=(ccx - 9.525, row - 0.635), val_at=(ccx + 7.62, row + 1.905))
        px, py = P[(jc, pin)]
        kx = px + 2.54
        if row == py:
            W((px, py), P[(cap, "1")])
        else:
            W((px, py), (kx, py)); W((kx, py), (kx, row)); W((kx, row), P[(cap, "1")])
        mx = P[(cap, "2")][0] + 2.54
        W(P[(cap, "2")], (mx, row))
    mx = P[(caps[0], "2")][0] + 2.54
    W((mx, rows[0]), (mx, rows[1])); W((mx, rows[1]), (mx, rows[2]))
    if link:
        # the - bus reaches the other base through a wire link (single-sided board):
        # pin 1 = bus side (net <other>_<link>), pin 2 = the other base
        L(f"{other}_{link}", mx + 1.27, rows[1], 0, "left")
        x1 = PINS["Jumper:Jumper_2_Bridged"]["1"][0]
        x2 = PINS["Jumper:Jumper_2_Bridged"]["2"][0]
        rot = 0 if x1 < x2 else 180
        if rot == 180:
            x1 = -x1
        cx_link = mx + 12.7 - x1
        part(link, "Jumper:Jumper_2_Bridged", "WIRE_LINK", FP["W3"], (cx_link, rows[1]), rot,
             ref_at=(cx_link - 1.27, rows[1] - 3.175), val_at=(cx_link - 3.81, rows[1] + 3.81), hide_value=True)
        W((mx, rows[1]), (mx + 12.7, rows[1])); W((mx + 12.7, rows[1]), P[(link, "1")])
        far = P[(link, "2")]
        W(far, (far[0] + 2.54, far[1])); L(other, far[0] + 2.54, far[1])
    else:
        W((mx, rows[1]), (mx + 5.08, rows[1])); L(other, mx + 5.08, rows[1])
    T(f"JC{n}: timing cap for stage {n}, + side to {common}, - side to {other}", cx - 12.7, cy - 12.7)


def jumper(ref, x, y, n1, n2, n3, link=None):
    part(ref, "Connector_Generic:Conn_01x03", "PINOUT", FP["H3"], (x, y), ref_at=(x - 2.54, y - 5.08), val_at=(x + 2.54, y + 5.08), hide_value=True)
    for pin, net in (("1", n1), ("3", n3)):
        px, py = P[(ref, pin)]
        end = (px - (12.7 if (net == "GND" and link) else 5.08), py)
        W((px, py), end)
        if net == "GND":
            if link:
                part(link, "Jumper:Jumper_2_Bridged", "WIRE_LINK", FP["W"], (end[0] - 5.08, py), 0,
                     ref_at=(end[0] - 6.35, py - 3.175), val_at=(end[0] - 10.16, py - 2.54), hide_value=True)
                L(f"GND_{link}", px - 1.27, py, 0, "right")
                a, b = P[(link, "1")], P[(link, "2")]
                W(end, max(a, b)); far = min(a, b)
                W(far, (far[0] - 2.54, far[1])); power("power:GND", far[0] - 2.54, far[1])
            else:
                power("power:GND", end[0], py)
        else:
            L(net, end[0], py, 0, "right")
    px, py = P[(ref, "2")]
    W((px, py), (px - 5.08, py)); L(n2, px - 5.08, py, 0, "right")


# ------------------------------------------------------------------ the sheet
OX1, OX2 = 35.56, 118.11
stage(1, OX1)
stage(2, OX2)
# power input, stage 1 rail start
part("J1", "Connector_Generic:Conn_01x02", "PWR_IN", FP["H2"], (OX1 - 10.16, Y_VCC), 0, "y",
     ref_at=(OX1 - 17.78, Y_VCC - 5.08), val_at=(OX1 - 17.78, Y_VCC + 5.08))
power("power:PWR_FLAG", OX1, Y_VCC)
g = P[("J1", "2")]
W(g, (g[0], g[1] + 3.81)); W((g[0], g[1] + 3.81), (g[0], g[1] + 7.62))
power("power:PWR_FLAG", g[0], g[1] + 3.81, 180)
power("power:GND", g[0], g[1] + 7.62)
# cap select blocks
cap_block(1, 55.88, 111.76, "Q1_C", "Q2_B")
cap_block(2, 138.43, 111.76, "Q2_C", "Q1_B", link="W3")
# pinout jumpers (same pad semantics as v1)
YJ = 142.24
jumper("JP1", 63.5, YJ, "GND", "Q1_TL", "Q1_C", link="W1")
jumper("JP2", 93.98, YJ, "Q1_C", "Q1_TR", "GND")
jumper("JP3", 133.35, YJ, "GND", "Q2_TL", "Q2_C")
jumper("JP4", 176.53, YJ, "Q2_C", "Q2_TR", "GND", link="W2")
T("Pinout select, per transistor: pad 1 = GND (emitter), pad 2 = TO-92 outer leg, pad 3 = collector.", 22.86, 129.54)
T("Shunt 1-2 on both = E-B-C (2N3904, PN2222, S8050).  Shunt 2-3 on both = C-B-E (BC547, BC548, BC337).", 22.86, 133.35)
T("W1 / W2 / W3: bare wire links on the component side (single-sided board); each joins two copper islands of one net.", 22.86, 153.67)
NOTES = [
    "Astable multivibrator LED flasher, v2: single copper layer (bottom), home etchable, all through-hole.",
    "JR1 / JR2 pick the base resistor (22k / 47k / 100k), JC1 / JC2 pick the timing cap (4.7u / 10u / 47u): one shunt per header.",
    "f = 1 / (1.386 * Rb * C):  22k/4.7u 7 Hz ... 47k/10u 1.5 Hz ... 100k/47u 0.15 Hz.  Supply 3 to 9 V, 5 V recommended.",
    "Unselected caps float on the + side and stay tied to the base on the - side; unselected resistors float at the base end.",
]
for i, line in enumerate(NOTES):
    T(line, 22.86, 165.1 + i * 3.81)

# junctions
from collections import Counter
deg = Counter()
for a, b in wires:
    deg[a] += 1; deg[b] += 1
for pos in P.values():
    deg[pos] += 1
junctions = [pt for pt, d in deg.items() if d >= 3]

# ------------------------------------------------------------------ emit
out = []
A = out.append
A('(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")')
A(f'\t(uuid "{ROOT_UUID}")\n\t(paper "A4")')
A('\t(title_block\n\t\t(title "Astable multivibrator LED flasher v2 - single sided, selectable RC")\n\t\t(date "2026-10-21")\n\t\t(rev "2.0")'
  '\n\t\t(company "MIT licensed hobby project")\n\t\t(comment 1 "Home etchable: bottom copper only, 1.0 mm tracks, 0.6 mm clearance, three wire links")\n\t)')
A("\t(lib_symbols\n" + "\n".join(LIB_TEXT.values()) + "\n\t)")


def effects(justify=None, hide=False, size=1.27):
    s = f"(effects (font (size {size} {size}))"
    if justify:
        s += f" (justify {justify})"
    if hide:
        s += " (hide yes)"
    return s + ")"


for k, ((x0, y0), (x1, y1)) in enumerate(wires):
    A(f'\t(wire (pts (xy {r2(x0)} {r2(y0)}) (xy {r2(x1)} {r2(y1)})) (stroke (width 0) (type default)) (uuid "{uid(f"w{k}")}"))')
for k, (x, y) in enumerate(junctions):
    A(f'\t(junction (at {r2(x)} {r2(y)}) (diameter 0) (color 0 0 0 0) (uuid "{uid(f"j{k}")}"))')
for k, (text, x, y, rot, justify) in enumerate(labels):
    A(f'\t(label "{text}" (at {r2(x)} {r2(y)} {rot}) {effects(justify + " bottom")} (uuid "{uid(f"l{k}")}"))')
for k, (text, x, y, size) in enumerate(texts):
    A(f'\t(text "{text}" (exclude_from_sim no) (at {r2(x)} {r2(y)} 0) {effects("left bottom", size=size)} (uuid "{uid(f"t{k}")}"))')

for ref, p in parts.items():
    x, y = p["at"]
    pa = (360 - p["rot"]) % 360
    hide_ref = ref.startswith("#")
    A("\t(symbol")
    A(f'\t\t(lib_id "{p["lib"]}")\n\t\t(at {r2(x)} {r2(y)} {p["rot"]})')
    if p["mirror"]:
        A(f'\t\t(mirror {p["mirror"]})')
    A(f'\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom {"yes" if p["in_bom"] else "no"})\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced no)')
    A(f'\t\t(uuid "{uid("sym:" + ref)}")')
    A(f'\t\t(property "Reference" "{ref}" (at {r2(p["ref_at"][0])} {r2(p["ref_at"][1])} {pa}) {effects("left", hide=hide_ref)})')
    A(f'\t\t(property "Value" "{p["value"]}" (at {r2(p["val_at"][0])} {r2(p["val_at"][1])} {pa}) {effects("left", hide=hide_ref or p["hide_value"])})')
    A(f'\t\t(property "Footprint" "{p["fp"]}" (at {r2(x)} {r2(y)} 0) {effects(hide=True)})')
    A(f'\t\t(property "Datasheet" "~" (at {r2(x)} {r2(y)} 0) {effects(hide=True)})')
    A(f'\t\t(property "Description" "" (at {r2(x)} {r2(y)} 0) {effects(hide=True)})')
    for n in PINS[p["lib"]]:
        A(f'\t\t(pin "{n}" (uuid "{uid(f"pin:{ref}:{n}")}"))')
    A(f'\t\t(instances (project "astable_v2" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))')
    A("\t)")
A('\t(sheet_instances (path "/" (page "1")))\n)')
PRJ.mkdir(parents=True, exist_ok=True)
SCH.write_text("\n".join(out) + "\n")
(PRJ / "fp-lib-table").write_text('(fp_lib_table\n  (version 7)\n  (lib (name "HomeEtch")(type "KiCad")(uri "${KIPRJMOD}/../lib/HomeEtch.pretty")(options "")(descr "single-sided home-etch footprints"))\n)\n')
(PRJ / "sym-lib-table").write_text('(sym_lib_table\n  (version 7)\n  (lib (name "AstableV2")(type "KiCad")(uri "${KIPRJMOD}/../lib/AstableV2.kicad_sym")(options "")(descr "TO-92 socket symbol"))\n)\n')
print(f"wrote {SCH}: {len(parts)} symbols, {len(wires)} wires, {len(junctions)} junctions, {len(labels)} labels")
