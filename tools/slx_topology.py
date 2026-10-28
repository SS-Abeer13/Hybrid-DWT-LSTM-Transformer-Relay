"""List the physical (SimPowerSystems) nets of a .slx that touch the given block-name fragments. Read-only helper.

    python tools/slx_topology.py simulations/TransformerB_v4.slx External_Fault Secondary_side Breaker
"""
import collections
import html
import re
import sys
import tempfile
import zipfile
from pathlib import Path

slx = Path(sys.argv[1])
keys = sys.argv[2:]
with tempfile.TemporaryDirectory() as td:
    zipfile.ZipFile(slx).extract("simulink/systems/system_root.xml", td)
    s = (Path(td) / "simulink/systems/system_root.xml").read_text(encoding="utf-8")
names = {m.group(3): html.unescape(m.group(2)).replace("\n", " ").strip() for m in re.finditer(r'<Block BlockType="([^"]+)" Name="([^"]+)" SID="(\d+)"', s)}
parent = {}


def find(x):
    while parent.setdefault(x, x) != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


nets = []
for m in re.finditer(r'<Line LineType="Connection">(.*?)\n  </Line>', s, re.S):
    toks = list(set(re.findall(r"(\d+)#((?:lconn|rconn):\d+)", m.group(1))))
    nets.append(toks)
    for a in toks[1:]:
        parent[find(a)] = find(toks[0])
groups = collections.defaultdict(set)
for n in nets:
    for t in n:
        groups[find(t)].add(t)
for members in groups.values():
    labs = sorted(f"{names.get(b, b)}[{p}]" for b, p in members)
    if any(any(k in lab for k in keys) for lab in labs):
        print(" | ".join(labs))
