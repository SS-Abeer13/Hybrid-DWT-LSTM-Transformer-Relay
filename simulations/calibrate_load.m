function cal = calibrate_load(varargin)
%CALIBRATE_LOAD Map the load knob to the REALISED load in % of rated current (step A2 of IMPLEMENTATION_PLAN_V3.md).
%
%   cal = calibrate_load            % sweep, write load_calibration.txt / load_calibration.mat (and print the relay_config.m lines)
%
% GROUND TRUTH: the model's own V-I measurement blocks (Primary_side / Secondary_side) give the TRUE line currents and voltages.
% Realised load = true line current RMS / rated line current (753.06 A HV, 15745.9 A LV), mean of the two sides (they agree).
% The CT-secondary signals the relay sees are reported too, against the measured rated secondary 0.9302 A
% (effective CT ratios HV 809.6:1, LV 16925:1; see probe_ct_truth.m and the 2026-10-21 log entry).
%
% Case: Normal, breakers closed, no noise, no CT mismatch, source 1.0 pu, steady state t > 0.3 s, power factor 0.8 / 0.9 / 1.0.
% The plant has ~1 pu of series impedance on the LV side, so the LV bus voltage falls as the load grows; the table reports it.
% Only the load KNOB changes: ActivePower = knob*300e6*pf, InductivePower = knob*300e6*sqrt(1-pf^2).
%
% The model is changed in memory only and closed without saving.

opts = struct('Knobs', logspace(log10(0.02), log10(10), 18), 'PFs', [0.8 0.9 1.0], 'StopTime', 0.6);
for k = 1:2:numel(varargin), opts.(varargin{k}) = varargin{k + 1}; end

model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on')
    error('CalLoad:Dirty', '%s is open with UNSAVED changes. Save or close it first.', model);
end
load_system(fullfile(thisDir, [model '.slx']));
cleanup = onCleanup(@() finish(model)); %#ok<NASGU>

Srated = 300e6; IratedHV = Srated / (sqrt(3) * 230e3); IratedLV = Srated / (sqrt(3) * 11e3); IsecRated = 0.9302; fs = 1600;
hv = findBlock(model, 'Three-Phase Breaker');
lv = findBlock(model, 'Three-Phase Breaker1');
ld = findBlock(model, 'Three-Phase Series RLC Load');
xf = findBlock(model, 'Step_down_Transformer');
vs = {findBlock(model, 'VSa'), findBlock(model, 'VSb'), findBlock(model, 'VSc')};
nmu = findBlock(model, 'Noise Merging Unit');
fault = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};

setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}
    try, set_param(model, m{1}, 'none'); catch, end %#ok<NOCOM>
end
setp(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
for i = 1:size(fault, 1)
    setp(findBlock(model, fault{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');
    setp(findBlock(model, fault{i, 2}), 'Time', '10', 'Before', '0', 'After', '1');
end
setp(xf, 'SetInitialFlux', 'off');
amp = sprintf('%.6g', 230e3 * sqrt(2) / sqrt(3));
ph0 = [0 -120 120];
for k = 1:3, setp(vs{k}, 'Amplitude', amp, 'Phase', sprintf('%.6g', ph0(k))); end
for k = 1:6
    setp(findBlock(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0');
    setp(findBlock(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1');
end
% log the true currents / voltages of the two V-I measurement blocks (out1 = voltages, out2 = currents)
names = {'CalPrimV', 'CalPrimI'; 'CalSecV', 'CalSecI'};
sides = {findBlock(model, 'Primary_side'), findBlock(model, 'Secondary_side')};
for s = 1:2
    ph = get_param(sides{s}, 'PortHandles');
    for q = 1:2
        set_param(ph.Outport(q), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', names{s, q});
    end
end

knobs = opts.Knobs(:).'; pfs = opts.PFs(:).';
nk = numel(knobs); np = numel(pfs);
pctHV = nan(np, nk); pctLV = nan(np, nk); secHV = nan(np, nk); secLV = nan(np, nk); vLV = nan(np, nk);
fprintf('%-5s %-7s | %-9s %-9s | %-9s %-9s | %-8s\n', 'pf', 'knob', 'HV %rated', 'LV %rated', 'secHV %', 'secLV %', 'V_LV pu');
for j = 1:np
    pf = pfs(j);
    for i = 1:nk
        S = knobs(i) * Srated;
        setp(ld, 'ActivePower', sprintf('%.6g', S * pf), 'InductivePower', sprintf('%.6g', max(S * sqrt(max(1 - pf ^ 2, 0)), 1)), 'CapacitivePower', '0');
        out = sim(model, 'StopTime', sprintf('%.3f', opts.StopTime), 'ReturnWorkspaceOutputs', 'on');
        Ip = getArray(out, 'I_primary_abc'); Is = getArray(out, 'I_secondary_abc');
        t = (0:size(Ip, 1) - 1)' / fs; ok = t > 0.3;
        ls = out.get('logsout');
        [iP, ~] = logged(ls, 'CalPrimI'); [iS, ~] = logged(ls, 'CalSecI'); [vS, tS] = logged(ls, 'CalSecV');
        okS = tS > 0.3;
        pctHV(j, i) = 100 * rmsMean(iP(okS, :)) / IratedHV;
        pctLV(j, i) = 100 * rmsMean(iS(okS, :)) / IratedLV;
        secHV(j, i) = 100 * rmsMean(Ip(ok, :)) / IsecRated;
        secLV(j, i) = 100 * rmsMean(Is(ok, :)) / IsecRated;
        vLV(j, i) = rmsMean(vS(okS, :)) / 11e3;
        fprintf('%-5.2f %-7.3f | %-9.2f %-9.2f | %-9.2f %-9.2f | %-8.3f\n', pf, knobs(i), pctHV(j, i), pctLV(j, i), secHV(j, i), secLV(j, i), vLV(j, i));
    end
end

pct = 0.5 * (pctHV + pctLV);                                   % % of rated current (HV and LV agree)
cal = struct('knob', knobs, 'pf', pfs, 'pctRated', pct, 'pctHV', pctHV, 'pctLV', pctLV, 'secHVpct', secHV, 'secLVpct', secLV, ...
             'vLVpu', vLV, 'IsecRated', IsecRated, 'IratedHV', IratedHV, 'IratedLV', IratedLV, 'created', datestr(now)); %#ok<TNOW1,DATST>

fid = fopen(fullfile(thisDir, 'load_calibration.txt'), 'w');
fprintf(fid, 'Load calibration (calibrate_load.m, %s)\n', cal.created);
fprintf(fid, 'Normal case, breakers closed, no noise / CT mismatch, source 1.0 pu, steady state t > 0.3 s.\n');
fprintf(fid, 'Realised load = TRUE line current RMS (V-I measurement blocks) / rated line current (753.06 A HV, 15745.9 A LV), mean of both sides.\n');
fprintf(fid, 'sec%% = CT-secondary RMS / 0.9302 A (rated secondary). V_LV = LV bus line-line RMS / 11 kV.\n\n');
for j = 1:np
    fprintf(fid, 'pf %.2f\n%-8s %-11s %-11s %-9s %-9s %-8s\n', pfs(j), 'knob', 'HV %rated', 'LV %rated', 'secHV %', 'secLV %', 'V_LV pu');
    for i = 1:nk
        fprintf(fid, '%-8.3f %-11.2f %-11.2f %-9.2f %-9.2f %-8.3f\n', knobs(i), pctHV(j, i), pctLV(j, i), secHV(j, i), secLV(j, i), vLV(j, i));
    end
    fprintf(fid, '\n');
end
for j = 1:np
    [~, i110] = min(abs(pct(j, :) - 110)); [~, i30] = min(abs(pct(j, :) - 30));
    fprintf(fid, 'pf %.2f: max reachable %.0f %% of rated at knob %.1f; LV voltage %.2f pu at ~30 %% rated, %.2f pu at ~110 %% rated (knob %.2f).\n', ...
        pfs(j), max(pct(j, :)), max(knobs), vLV(j, i30), vLV(j, i110), knobs(i110));
end
fclose(fid);
save(fullfile(thisDir, 'load_calibration.mat'), 'cal');
fprintf('\nWritten load_calibration.txt / load_calibration.mat\n');
end

function m = rmsMean(x)
m = mean(sqrt(mean(abs(x) .^ 2, 1)));
end

function [v, t] = logged(ls, name)
el = ls.get(name);
if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data));
if size(v, 1) ~= numel(t), v = v.'; end
end

function finish(model)
if isappdata(0, 'HybridRelaySkipLSTM'), rmappdata(0, 'HybridRelaySkipLSTM'); end
if bdIsLoaded(model), close_system(model, 0); end
end

function blk = findBlock(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
normName = @(s) strtrim(regexprep(s, '\s+', ' '));
hit = c(strcmp(cellfun(@(s) normName(get_param(s, 'Name')), c, 'UniformOutput', false), normName(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'CalLoad:Block', 'Expected exactly one block "%s" under %s, found %d.', name, parent, numel(hit));
blk = hit{1};
end

function setp(blk, varargin)
set_param(blk, varargin{:});
for k = 1:2:numel(varargin)
    want = strtrim(varargin{k + 1}); got = strtrim(get_param(blk, varargin{k}));
    if ~strcmp(want, got)
        a = sscanf(strtrim(regexprep(want, '[\[\],;]', ' ')), '%f'); b = sscanf(strtrim(regexprep(got, '[\[\],;]', ' ')), '%f');
        assert(~isempty(a) && isequal(size(a), size(b)) && all(abs(a(:) - b(:)) <= 1e-9 * max(1, abs(a(:)))), ...
            'CalLoad:SetParam', '%s: %s should be "%s" but is "%s".', blk, varargin{k}, want, got);
    end
end
end

function x = getArray(out, name)
v = out.get(name);
if isa(v, 'timeseries'), x = double(v.Data);
elseif isstruct(v), x = double(v.signals.values);
else, x = double(v); end
end
