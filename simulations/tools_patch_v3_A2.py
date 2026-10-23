"""Step A2 patch of generate_stress_dataset_v3.m: target load in % of RATED current via the calibration table (load_knob_for.m),
CT rated secondary 0.9302 A, realised-load check per trace. Idempotent guard: refuses to run twice."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "loadRealisedPct" not in s, "A2 patch already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:70]
    s = s.replace(old, new, 1)


# 1) rated CT secondary current: 0.9302 A both sides (ground truth, probe_ct_truth.m)
rep("cfg.Inom      = [1.8827 1.8827 1.8827 0.8557 0.8557 0.8557];  % rated CT secondary current (A): HV x3, LV x3",
    "cfg.Inom      = 0.9302 * ones(1, 6);   % rated CT secondary current (A): HV x3, LV x3. Measured: effective CT ratios 809.6:1 / 16925:1\n"
    "cfg.loadTolPct = 10;                    % realised load must be within +/-10 % of the target (or 2 points of rated at very light load)")
rep("cfg.version   = 'v3-2026-10-21';", "cfg.version   = 'v3-2026-10-21-A2';")

# 2) draw the load as % of rated current; knob from the calibration table
rep("""p.loadPu = 0.05 + 1.15 * rand();                       % 5-120 % of 300 MVA
if stress, p.loadPu = 0.6 + 0.6 * rand(); end
p.pf = 0.85 + 0.15 * rand();
""", """p.pf = 0.80 + 0.20 * rand();                          % 0.80-1.00 lagging
loadPct = 10 + 100 * rand();                           % 10-110 % of RATED current (A2; stratified into bins in A7)
if stress, loadPct = 60 + 50 * rand(); end
p.loadPu = loadPct / 100;                              % per unit of rated CURRENT (not of the load knob)
p.loadKnob = load_knob_for(loadPct, p.pf);             % ActivePower = knob*300 MVA*pf (calibrate_load.m)
""")

# 3) apply the knob, not the target
rep("S = p.loadPu * cfg.Srated;", "S = p.loadKnob * cfg.Srated;")

# 4) record fields
rep("""             'faultDiffPu', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');""",
    """             'faultDiffPu', NaN, 'loadRealisedPct', NaN, 'loadOK', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');""")
rep("""% detectability: rise of the relay's compensated differential (per unit) one cycle after the event""",
    """% realised load (% of rated CT-secondary current) on a healthy, settled stretch with the load connected
loadWin = [];
if any(strcmp(sc.kind, {'internal', 'external', 'ct_stress_int', 'ct_stress_ext', 'evolving'}))
    loadWin = t > 0.12 & t < min(p.tEvent - 0.03, 0.28);
elseif strcmp(sc.kind, 'normal')
    loadWin = t > 0.12 & t < 1.0;
end
if any(loadWin)
    rec.loadRealisedPct = 100 * mean(sqrt(mean([Ip(loadWin, :) Is(loadWin, :)] .^ 2, 1))) / cfg.Inom(1);
    target = 100 * p.loadPu;
    rec.loadOK = double(abs(rec.loadRealisedPct - target) <= max(cfg.loadTolPct / 100 * target, 2));
end

% detectability: rise of the relay's compensated differential (per unit) one cycle after the event""")
rep("""for f = {'eventDetected', 'energiseDetected', 'timingOK', 'eventVisible', 'noiseMeasured', 'noiseExpected', ...
         'noiseOK', 'duplicate', 'faultDiffPu', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});""", """for f = {'eventDetected', 'energiseDetected', 'timingOK', 'eventVisible', 'noiseMeasured', 'noiseExpected', ...
         'noiseOK', 'duplicate', 'faultDiffPu', 'loadRealisedPct', 'loadOK', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});""")
rep("""         'noiseOK', 'duplicate', 'faultDiffPu', 'checkPassed'}
    D.(f{1}) = nan(1, N);""", """         'noiseOK', 'duplicate', 'faultDiffPu', 'loadRealisedPct', 'loadOK', 'checkPassed', 'loadKnob'}
    D.(f{1}) = nan(1, N);""")
rep("D.loadPu(i) = p.loadPu;", "D.loadPu(i) = p.loadPu; D.loadKnob(i) = p.loadKnob;")

# 5) progress line: show target and realised load
rep("""    fprintf('[%4d/%4d] %-24s %-4s | load %4.0f%% pf %.2f noise %.2f%% | event %6s det %6s | %s | ETA %.0f min\\n', ...
        idx, N, sc.name, status, 100 * p.loadPu, p.pf, p.noisePct, fmtT(p.tEvent), fmtT(rec.eventDetected), ...""",
    """    fprintf('[%4d/%4d] %-24s %-4s | load %4.0f%% (real %4.0f%%) pf %.2f noise %.2f%% | event %6s det %6s | %s | ETA %.0f min\\n', ...
        idx, N, sc.name, status, 100 * p.loadPu, rec.loadRealisedPct, p.pf, p.noisePct, fmtT(p.tEvent), fmtT(rec.eventDetected), ...""")
rep("""    fprintf('%-17s %-3s | load %3.0f%% | event %s det %s visible %g | energised %s | noise %.4f/%.4f A | faultDiff %.3f pu | %s\\n', ...
        names{i}, status, 100 * p.loadPu, fmtT(p.tEvent),""", """    fprintf('%-17s %-3s | load %3.0f%% (real %3.0f%%) | event %s det %s visible %g | energised %s | noise %.4f/%.4f A | faultDiff %.3f pu | %s\\n', ...
        names{i}, status, 100 * p.loadPu, rec.loadRealisedPct, fmtT(p.tEvent),""")
p.write_text(s, encoding="utf-8")
print("A2 patch applied")
