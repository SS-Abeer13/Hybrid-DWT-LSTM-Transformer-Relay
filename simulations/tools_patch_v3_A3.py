"""Step A3 patch of generate_stress_dataset_v3.m: CT burden control (read back), true-current logging, per-trace CT ratio error check,
CT-stress scenarios for every fault type. Remanence is NOT modelled (the CT core-loss branch decays it in ~25 ms; probe_ct_stress.m)."""
from pathlib import Path

p = Path(__file__).resolve().parent / "generate_stress_dataset_v3.m"
s = p.read_text(encoding="utf-8")
assert "ctRatioErrorMax" not in s, "A3 patch already applied"


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:80]
    s = s.replace(old, new, 1)


rep("cfg.version   = 'v3-2026-10-21-A2';", "cfg.version   = 'v3-2026-10-21-A3';")
rep("cfg.loadTolPct = 10; ", "cfg.ctRatio   = [809.6 16925];          % effective CT ratios HV / LV (true line current / CT secondary), probe_ct_truth.m\ncfg.loadTolPct = 10; ")

# --- locate blocks: CT burden resistors and the V-I measurement blocks
rep("B.relay = findBlock(model, 'Hybrid 87T Relay');\nend",
    """B.relay = findBlock(model, 'Hybrid 87T Relay');
B.priV  = findBlock(model, 'Primary_side');     % V-I measurement: TRUE HV line current (for the CT ratio-error check)
B.secV  = findBlock(model, 'Secondary_side');   % V-I measurement: TRUE LV line current
ctNames = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'};
for k = 1:6
    B.ctBurden{k} = findBlock(findBlock(model, ctNames{k}), '1ohm');     % burden resistor of each CT subsystem (1 ohm nominal)
end
end""")

# --- log the true currents
rep("""dph = get_param(findBlock(B.relay, 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');
end""", """dph = get_param(findBlock(B.relay, 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');
% 5) Log the TRUE line currents (V-I measurement out2) to measure the CT ratio error per trace (ctRatioErrorMax).
for kk = 1:2
    sideBlk = {B.priV, B.secV}; nm = {'TruePrimI', 'TrueSecI'};
    pp = get_param(sideBlk{kk}, 'PortHandles');
    set_param(pp.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', nm{kk});
end
end""")

# --- apply the burden
rep("""% --- noise and CT mismatch (noise std = noisePct % of each channel's rated secondary current)""",
    """% --- CT burden (x nominal 1 ohm, same on all six CTs); remanence cannot be modelled (flux decays in ~25 ms)
for k = 1:6
    setp(B.ctBurden{k}, 'Resistance', sprintf('%.6g', p.ctBurden));
end

% --- noise and CT mismatch (noise std = noisePct % of each channel's rated secondary current)""")

# --- draw the burden
rep("""mm = 0.02; if stress, mm = 0.05; end""",
    """mm = 0.02; if stress, mm = 0.05; end
% CT burden (x 1 ohm). External faults here are weak (~1.5 pu rms at the CTs), so saturation needs a large burden: probe_ct_stress.m
% gave ratio errors of 3-59 % (A-G) and 17-82 % (A-B, A-B-C) for 4-12 x. Stress 4-10 x (log-uniform), other traces 1-3 x.
if stress, p.ctBurden = 10 ^ (log10(4) + log10(2.5) * rand()); else, p.ctBurden = 1 + 2 * rand(); end""")

# --- record + checks
rep("""'faultDiffPu', NaN, 'loadRealisedPct', NaN, 'loadOK', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');""",
    """'faultDiffPu', NaN, 'loadRealisedPct', NaN, 'loadOK', NaN, 'ctRatioErrorMax', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');""")
rep("""% duplicate waveform?""", """% CT ratio error (%): RMS(N*I_ct - I_true)/RMS(I_true) over 5-45 ms after the event, max over the six channels (HV and LV).
% >10 % = the CT visibly saturates / distorts. NaN when there is no event or the true current is below 2 % of rated.
try
    if ~isnan(p.tEvent)
        lsg = out.get('logsout');
        [iP, tP] = loggedSignal(lsg, 'TruePrimI'); [iS, ~] = loggedSignal(lsg, 'TrueSecI');
        w = t >= p.tEvent + 0.005 & t <= p.tEvent + 0.045;
        if nnz(w) > 10
            iPw = interp1(tP, iP, t(w)); iSw = interp1(tP, iS, t(w));
            rP = sqrt(mean(iPw .^ 2, 1)); rS = sqrt(mean(iSw .^ 2, 1));
            eP = sqrt(mean((cfg.ctRatio(1) * Ip(w, :) - iPw) .^ 2, 1)) ./ max(rP, eps);
            eS = sqrt(mean((cfg.ctRatio(2) * Is(w, :) - iSw) .^ 2, 1)) ./ max(rS, eps);
            ok = [rP rS] > 0.02 * [753.06 * ones(1, 3), 15745.9 * ones(1, 3)];
            if any(ok), e = [eP eS]; rec.ctRatioErrorMax = 100 * max(e(ok)); end
        end
    end
catch
end

% duplicate waveform?""")
rep("""'noiseOK', 'duplicate', 'faultDiffPu', 'loadRealisedPct', 'loadOK', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});""", """'noiseOK', 'duplicate', 'faultDiffPu', 'loadRealisedPct', 'loadOK', 'ctRatioErrorMax', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});""")
rep("""'noiseOK', 'duplicate', 'faultDiffPu', 'loadRealisedPct', 'loadOK', 'checkPassed', 'loadKnob'}""",
    """'noiseOK', 'duplicate', 'faultDiffPu', 'loadRealisedPct', 'loadOK', 'ctRatioErrorMax', 'checkPassed', 'loadKnob', 'ctBurden'}""")
rep("D.loadPu(i) = p.loadPu; D.loadKnob(i) = p.loadKnob;", "D.loadPu(i) = p.loadPu; D.loadKnob(i) = p.loadKnob; D.ctBurden(i) = p.ctBurden;")
rep("""function x = getArray(out, name)""", """function [v, t] = loggedSignal(ls, name)
el = ls.get(name);
if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data));
if size(v, 1) ~= numel(t), v = v.'; end
end

function x = getArray(out, name)""")

# --- progress line / self-test show the CT error
rep("""'[%4d/%4d] %-24s %-4s | load %4.0f%% (real %4.0f%%) pf %.2f noise %.2f%% | event %6s det %6s | %s | ETA %.0f min\\n', ...
        idx, N, sc.name, status, 100 * p.loadPu, rec.loadRealisedPct, p.pf, p.noisePct, fmtT(p.tEvent), fmtT(rec.eventDetected), ...""",
    """'[%4d/%4d] %-26s %-4s | load %4.0f%% (real %4.0f%%) pf %.2f noise %.2f%% burden %.1fx CTerr %3.0f%% | event %6s det %6s | %s | ETA %.0f min\\n', ...
        idx, N, sc.name, status, 100 * p.loadPu, rec.loadRealisedPct, p.pf, p.noisePct, p.ctBurden, rec.ctRatioErrorMax, fmtT(p.tEvent), fmtT(rec.eventDetected), ...""")
rep("""'%-17s %-3s | load %3.0f%% (real %3.0f%%) | event %s det %s visible %g | energised %s | noise %.4f/%.4f A | faultDiff %.3f pu | %s\\n', ...
        names{i}, status, 100 * p.loadPu, rec.loadRealisedPct, fmtT(p.tEvent),""", """'%-22s %-3s | load %3.0f%% (real %3.0f%%) burden %.1fx CTerr %3.0f%% | event %s det %s visible %g | energised %s | noise %.4f/%.4f A | faultDiff %.3f pu | %s\\n', ...
        names{i}, status, 100 * p.loadPu, rec.loadRealisedPct, p.ctBurden, rec.ctRatioErrorMax, fmtT(p.tEvent),""")

# --- CT-stress scenarios for every fault type (replaces the two single-type rows)
rep(""" 'Stress_CTSat_Int'     'Internal' 'ct_stress_int'   1 1 1 0  0.01  0.1   true   3
 'Stress_ExtCTSat'      'External' 'ct_stress_ext'   1 1 1 0  0.001 0.05  false  6
};""", """};""")
rep("""f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';""", """% CT-saturation stress for EVERY fault type (A3): burden 4-10 x, external and internal. Weights are placeholders until A7.
ft = {'AG' [1 0 0 1]; 'BG' [0 1 0 1]; 'CG' [0 0 1 1]; 'AB' [1 1 0 0]; 'BC' [0 1 1 0]; 'AC' [1 0 1 0]; ...
      'ABG' [1 1 0 1]; 'BCG' [0 1 1 1]; 'ACG' [1 0 1 1]; 'ABC' [1 1 1 0]; 'ABCG' [1 1 1 1]};
for q = 1:size(ft, 1)
    v = ft{q, 2};
    rows(end + 1, :) = {['Stress_ExtCTSat_' ft{q, 1}], 'External', 'ct_stress_ext', v(1), v(2), v(3), v(4), 0.001, 0.05, false, 2}; %#ok<AGROW>
    rows(end + 1, :) = {['Stress_CTSat_Int_' ft{q, 1}], 'Internal', 'ct_stress_int', v(1), v(2), v(3), v(4), 0.01, 0.1, true, 1}; %#ok<AGROW>
end
f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';""")

# --- self-test: add two CT-stress cases
rep("names = {'Normal', 'Internal_AB', 'Internal_HiZ_AB', 'Internal_AG', 'Inrush_NoLoad', 'External_ABC', 'Internal_SOTF_AB'};",
    "names = {'Normal', 'Internal_AB', 'Internal_HiZ_AB', 'Internal_AG', 'Inrush_NoLoad', 'External_ABC', 'Internal_SOTF_AB', ...\n         'Stress_ExtCTSat_ABC', 'Stress_ExtCTSat_AG', 'Stress_CTSat_Int_AB'};")
p.write_text(s, encoding="utf-8")
print("A3 patch applied")
