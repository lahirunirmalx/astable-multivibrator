#!/usr/bin/env python3
"""Compare schematic connectivity (kicad-cli netlist) with the routed board's pad nets.

Usage: /usr/bin/python3 kicad/tools/compare_netlist.py <netlist.net> <board.kicad_pcb>
Exit 1 on any difference. Run with the python that has pcbnew (KiCad 9).
"""
import re
import sys
import pcbnew

net_file, pcb_file = sys.argv[1], sys.argv[2]
text = open(net_file).read()
sch = {}
nets = text[text.index("(nets"):]
for chunk in re.split(r'\(net \(code "\d+"\) ', nets)[1:]:
    name = re.match(r'\(name "([^"]+)"\)', chunk).group(1)
    for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', chunk):
        sch[(ref, pin)] = name
b = pcbnew.LoadBoard(pcb_file)
pcb = {}
for fp in b.GetFootprints():
    seen = set()
    for pad in fp.Pads():
        key = (fp.GetReference(), pad.GetNumber())
        if key in seen:
            continue
        seen.add(key)
        pcb[key] = pad.GetNetname()
bad = 0
for key in sorted(set(sch) | set(pcb)):
    s, p = sch.get(key, "<none>"), pcb.get(key, "<none>")
    if s != p:
        bad += 1
        print("MISMATCH", key, "sch:", s, "pcb:", p)
print(f"{len(sch)} schematic pins, {len(pcb)} board pads, {bad} mismatches")
sys.exit(1 if bad else 0)
