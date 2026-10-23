"""A8: self-test covering EVERY scenario kind (18 cases) with an optional case range ('Range',[a b]) so it can be run in two MATLAB sessions."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "'Range'" not in s, "A8 already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:90]
    s = s.replace(old, new, 1)


rep("cfg.version   = 'v3-2026-10-21-A7b';", "cfg.version   = 'v3-2026-10-21-A8';")
rep("'Chunk', 0, 'Set', 'main', 'Only', {{}});", "'Chunk', 0, 'Set', 'main', 'Only', {{}}, 'Range', []);")
rep("%   'StopTime' simulation length in seconds (default 1.10).", "%   'StopTime' simulation length in seconds (default 1.10).\n%   'Range'   self-test only: [first last] case numbers (the heap crash can hit a long single session; run 1:9 and 10:18).")
rep("    runSelfTest(model, B, ST, cfg);", "    runSelfTest(model, B, ST, cfg, opts.Range);")
rep("function runSelfTest(model, B, ST, cfg)", "function runSelfTest(model, B, ST, cfg, range)")
a = s.index("names = {'Normal', 'Internal_AB',")
b = s.index("fprintf('\\n=== SELF-TEST")
s = s[:a] + r"""names = {'Normal', 'Internal_AB', 'Internal_HiZ_AB', 'Internal_AG', 'Inrush_NoLoad', 'Inrush_Loaded', 'External_ABC', 'Internal_SOTF_AB', 'Internal_Evolving', ...
         'Stress_ExtCTSat_ABC', 'Stress_ExtCTSat_AG', 'Stress_CTSat_Int_AB', 'InternalHV_AG', 'InternalHV_AB', 'Overexcitation', 'Recovery_Inrush', ...
         'Stress_FaultInInrush', 'Stress_ExtInInrush'};          % one case per scenario kind (18)
if isempty(range), range = [1 numel(names)]; end
sel = range(1):min(range(2), numel(names));
""" + s[b:]
rep("for i = 1:numel(names)\n    sc = ST(strcmp({ST.name}, names{i}));", "for i = sel\n    sc = ST(strcmp({ST.name}, names{i}));")
p.write_text(s, encoding="utf-8")
print("A8 applied")
