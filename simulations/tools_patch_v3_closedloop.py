"""Adds the 'closedloop' mode to generate_stress_dataset_v3.m (steps D3 and D4 of IMPLEMENTATION_PLAN_V3.md).

  generate_stress_dataset_v3('closedloop')                                  % D3: 12 hand-specified cases, LSTM active, writes test_hybrid_relay_v3_results.txt/.mat
  generate_stress_dataset_v3('closedloop', 'Set', 'OOD', 'Indices', [..])   % D4: re-run dataset traces (same seed / stratum / parameters) with the LSTM active
"""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "runClosedLoop" not in s, "already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:90]
    s = s.replace(old, new, 1)


rep("cfg.version   = 'v3-2026-10-21-A8-oemin';", "cfg.version   = 'v3-2026-10-22-A8-cl';")
rep("'Range', [], 'OverexcMin', 1.15);", "'Range', [], 'OverexcMin', 1.15, 'Indices', [], 'Tag', 'v3');")
rep("%   'Range'   self-test only:", "%   'Indices' closedloop only: dataset trace numbers (1..N of the chosen 'Set') to re-run with the LSTM active (D4); empty = the 12 D3 cases.\n%   'Tag'     closedloop only: suffix of the result files.\n%   'Range'   self-test only:")
rep("selfTest = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'selftest');",
    "selfTest = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'selftest');\nclosedLoop = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'closedloop');")
rep("if nargin < 1 || isempty(nSamples) || selfTest, nSamplesNum = 3040;", "if nargin < 1 || isempty(nSamples) || selfTest || closedLoop, nSamplesNum = 3040;")

# D3: no plan needed
rep("""if selfTest
    runSelfTest(model, B, ST, cfg, opts.Range);
    outFile = '';
    return;
end
""", """if selfTest
    runSelfTest(model, B, ST, cfg, opts.Range);
    outFile = '';
    return;
end
if closedLoop && isempty(opts.Indices)
    runClosedLoop(model, B, closedLoopCases(ST, cfg), cfg, thisDir, opts.Tag);
    outFile = '';
    return;
end
""")

# D4: needs the plan (same construction as the generation run)
rep("""firstOf = [1, cumsum(counts(1:end - 1)) + 1];
""", """firstOf = [1, cumsum(counts(1:end - 1)) + 1];
if closedLoop
    L = struct('name', {}, 'sc', {}, 'p', {}, 'expectTrip', {}, 'tRef', {});
    for idx = opts.Indices(:).'
        sc = ST(plan(idx));
        within = idx - firstOf(plan(idx)) + 1;
        if strcmp(opts.Set, 'OOD'), within = 0; end
        p = drawParameters(sc, cfg.seed + idx, makeCtx(cfg, sc, within, counts(plan(idx)), blockOf(idx)));
        p.sampleSeed = cfg.seed + idx;
        tref = p.tFault; if isnan(tref), tref = p.tEnergise; end
        L(end + 1) = struct('name', sprintf('%s #%d', sc.name, idx), 'sc', sc, 'p', p, 'expectTrip', logical(sc.shouldTrip), 'tRef', tref); %#ok<AGROW>
    end
    runClosedLoop(model, B, L, cfg, thisDir, opts.Tag);
    outFile = '';
    return;
end
""")

# the closed-loop engine and the D3 case list
rep("""% =====================================================================================
% Model configuration (every write is read back)""", r"""function L = closedLoopCases(ST, cfg)
% D3: 12 hand-specified cases. Each starts from a seeded random draw (noise, CT mismatch, noise seeds) and then fixes the parameters that define the case.
pick = @(n) ST(strcmp({ST.name}, n));
spec = {
 % label,                              scenario,               pct,  extra overrides (struct)
 'Normal, 30 % load',                  'Normal',               30,   struct()
 'Normal, 100 % load',                 'Normal',               100,  struct()
 'Inrush 0.8 pu remanence, 0 deg',     'Inrush_NoLoad',        60,   struct('tEnergise', 0.30, 'angle', 0, 'flux', [0.8 -0.4 -0.4])
 'Recovery inrush (HV bus, 50 ms)',    'Recovery_Inrush',      40,   struct('tFault', 0.35, 'faultClear', 0.40, 'Rf', 0.05, 'srcPhase', 30, 'freq', 50, 'srcZScale', 1)
 'Over-excitation 1.3 pu',             'Overexcitation',       50,   struct('srcScale', 1.30)
 'External 3-phase solid',             'External_ABC',         60,   struct('tFault', 0.45, 'Rf', 0.01)
 'External A-G + CT saturation 8 x',   'Stress_ExtCTSat_AG',   70,   struct('tFault', 0.45, 'Rf', 0.01, 'ctBurden', 8)
 'Internal A-G solid (LV side)',       'Internal_AG',          60,   struct('tFault', 0.45, 'Rf', 0.1)
 'Internal A-B, HV side',              'InternalHV_AB',        50,   struct('tFault', 0.45, 'Rf', 0.05)
 'Internal HiZ A-B, AI-only bin',      'Internal_HiZ_AB',      60,   struct('tFault', 0.45, 'Rf', 3.0)
 'SOTF A-B',                           'Internal_SOTF_AB',     40,   struct('tEnergise', 0.30, 'Rf', 0.1)
 'Fault during inrush A-B-G',          'Stress_FaultInInrush', 60,   struct('tEnergise', 0.25, 'tFault', 0.31, 'Rf', 0.1)};
L = struct('name', {}, 'sc', {}, 'p', {}, 'expectTrip', {}, 'tRef', {});
for k = 1:size(spec, 1)
    sc = pick(spec{k, 2});
    p = drawParameters(sc, cfg.seed + 700000 + k, makeCtx(cfg, sc, 0, 0, 0)); p.sampleSeed = cfg.seed + 700000 + k;
    ov = spec{k, 4};
    p.noisePct = 0.3; p.pf = 0.9; p.srcScale = 1.0; p.srcZScale = 1; p.freq = 50; p.ctBurden = 1.5;
    if any(strcmp(sc.kind, {'ct_stress_ext', 'ct_stress_int'})), p.noisePct = 1.5; end
    if strcmp(sc.kind, 'overexc'), p.srcScale = 1.15; end
    p.loadPu = spec{k, 3} / 100; p.loadKnob = load_knob_for(spec{k, 3}, p.pf);
    f = fieldnames(ov);
    for q = 1:numel(f)
        switch f{q}
            case 'angle', p.srcPhase = mod(ov.angle - 360 * p.freq * p.tEnergise, 360);
            case 'flux', p.residualFlux = ov.flux;
            otherwise, p.(f{q}) = ov.(f{q});
        end
    end
    if isfield(ov, 'tEnergise') && ~isfield(ov, 'tFault') && strcmp(sc.kind, 'sotf'), p.tFault = p.tEnergise; end
    if strcmp(sc.kind, 'overexc') && isfield(ov, 'srcScale'), p.srcScale = ov.srcScale; end
    if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
    if any(strcmp(sc.kind, {'normal', 'overexc'})), p.tEvent = NaN; end
    if strcmp(sc.kind, 'recovery_inrush'), p.tEvent = p.faultClear; end
    tref = p.tFault; if isnan(tref), tref = p.tEnergise; end
    L(end + 1) = struct('name', spec{k, 1}, 'sc', sc, 'p', p, 'expectTrip', logical(sc.shouldTrip), 'tRef', tref); %#ok<AGROW>
end
end

function runClosedLoop(model, B, L, cfg, thisDir, tag)
% Runs each case through Simulink WITH THE LSTM ACTIVE and records the relay's own trip decision ('Dec_Trip_Signal').
% The breakers are disconnected from the relay (External off) in this generator, so the decision is logged but does not alter the plant.
fprintf('\n=== CLOSED LOOP (%s): %d cases, LSTM active, real relay trip logic ===\n', tag, numel(L));
R = struct('name', {}, 'expectTrip', {}, 'tripped', {}, 'tripTime', {}, 'tRef', {}, 'maxProb', {}, 'passed', {}, 'delayMs', {}, 'sampleSeed', {});
fid = fopen(fullfile(thisDir, sprintf('test_hybrid_relay_%s_results.txt', tag)), 'w');
hdr = sprintf('Closed-loop validation (%s), LSTM active, relay trip logic of the saved model, %s\n%-36s %-8s %-8s %-9s %-10s %-8s\n%s\n', tag, datestr(now), 'case', 'expect', 'actual', 'max prob', 'delay ms', 'status', repmat('-', 1, 86)); %#ok<TNOW1,DATST>
fprintf('%s', hdr); if fid > 0, fprintf(fid, '%s', hdr); end
for k = 1:numel(L)
    setappdata(0, 'HybridRelaySkipLSTM', false); clear lstm_predict_wrapper;
    applyScenario(B, L(k).sc, L(k).p, cfg);
    tripped = false; tripTime = NaN; maxProb = NaN;
    try
        out = sim(model, 'StopTime', sprintf('%.4f', cfg.stopTime), 'ReturnWorkspaceOutputs', 'on');
        lg = out.get('logsout');
        for nm = {'Dec_Trip_Signal', 'TripSignal', 'Trip_Signal'}
            el = lg.get(nm{1});
            if ~isempty(el)
                if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
                t = el.Values.Time; d = squeeze(double(el.Values.Data));
                i = find(t >= 0.056 & d > 0.5, 1, 'first');
                if ~isempty(i), tripped = true; tripTime = t(i); end
                break;
            end
        end
        try
            pe = lg.get('LSTM_Prediction'); if isa(pe, 'Simulink.SimulationData.Dataset'), pe = pe{1}; end
            tp = pe.Values.Time; pv = squeeze(double(pe.Values.Data)); maxProb = max(pv(tp >= 0.056));
        catch
        end
    catch ME
        fprintf('  simulation failed for %s: %s\n', L(k).name, ME.message);
    end
    delayMs = NaN; if tripped, delayMs = 1000 * (tripTime - L(k).tRef); end
    passed = (tripped == L(k).expectTrip) && (~L(k).expectTrip || (delayMs >= 0 && delayMs <= 30));
    if ~L(k).expectTrip, passed = ~tripped; end
    R(end + 1) = struct('name', L(k).name, 'expectTrip', L(k).expectTrip, 'tripped', tripped, 'tripTime', tripTime, 'tRef', L(k).tRef, 'maxProb', maxProb, 'passed', passed, 'delayMs', delayMs, 'sampleSeed', L(k).p.sampleSeed); %#ok<AGROW>
    line = sprintf('%-36s %-8s %-8s %-9.4f %-10.1f %-8s\n', L(k).name, ifelse(L(k).expectTrip, 'TRIP', 'BLOCK'), ifelse(tripped, 'TRIP', 'BLOCK'), maxProb, delayMs, ifelse(passed, 'PASS', 'FAIL'));
    fprintf('%s', line); if fid > 0, fprintf(fid, '%s', line); end
end
ftr = sprintf('%s\nPassed %d / %d (trip decisions correct; internal faults must trip within 30 ms of the fault / energisation)\n', repmat('-', 1, 86), sum([R.passed]), numel(R));
fprintf('%s', ftr); if fid > 0, fprintf(fid, '%s', ftr); fclose(fid); end
save(fullfile(thisDir, sprintf('test_hybrid_relay_%s_results.mat', tag)), 'R');
end

% =====================================================================================
% Model configuration (every write is read back)""")
p.write_text(s, encoding="utf-8")
print("closedloop mode added")
