"""Adds the generator option 'OverexcMin' (lower bound of the over-excitation source voltage, default 1.15 pu = main set) for the coverage top-up."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "OverexcMin" not in s, "already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:90]
    s = s.replace(old, new, 1)


rep("'Only', {{}}, 'Range', []);", "'Only', {{}}, 'Range', [], 'OverexcMin', 1.15);")
rep("%   'Range'   self-test only:", "%   'OverexcMin' lower bound (pu) of the over-excitation source voltage, default 1.15 (main set); the coverage top-up uses 1.22 (saturated core).\n%   'Range'   self-test only:")
rep("cfg.set       = opts.Set;", "cfg.set       = opts.Set;\ncfg.oeMin     = opts.OverexcMin;")
rep("ctx = struct('hiz', cfg.hizBins,", "ctx = struct('oeMin', cfg.oeMin, 'hiz', cfg.hizBins,")
rep("p.srcScale = 1.15 + 0.30 * rand(); if ood == 4", "p.srcScale = ctx.oeMin + (1.45 - ctx.oeMin) * rand(); if ood == 4")
rep("cfg.version   = 'v3-2026-10-21-A8';", "cfg.version   = 'v3-2026-10-21-A8-oemin';")
p.write_text(s, encoding="utf-8")
print("OverexcMin option added")
