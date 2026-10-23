function R = probe_lv_series()
%PROBE_LV_SERIES What the three 0.5 ohm LV series resistors (Series RLC Branch, Branch1, Branch2) do to load sag and external fault strength.
% In-memory only; nothing is saved. Compares R_lv = 0.5 (as modelled), 0.1, 0.02 ohm.
model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() finish(model)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
fs = 1600; Nhv = 809.6; IsecRated = 0.9302;
hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1'); ld = fb(model, 'Three-Phase Series RLC Load'); xf = fb(model, 'Step_down_Transformer');
setp(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); setp(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(xf, 'SetInitialFlux', 'off');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
for k = 1:3, setp(vs{k}, 'Amplitude', sprintf('%.6g', 230e3 * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, setp(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); setp(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
faults = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};
for i = 1:4, setp(fb(model, faults{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); setp(fb(model, faults{i, 2}), 'Time', '10', 'Before', '0', 'After', '1'); end
lvR = {fb(model, 'Series RLC Branch'), fb(model, 'Series RLC Branch1'), fb(model, 'Series RLC Branch2')};
fprintf('LV series branches: R = %s / %s / %s ohm (BranchType %s)\n', get_param(lvR{1}, 'Resistance'), get_param(lvR{2}, 'Resistance'), get_param(lvR{3}, 'Resistance'), get_param(lvR{1}, 'BranchType'));
sides = {fb(model, 'Primary_side'), fb(model, 'Secondary_side')}; nm = {'TruePrimI', 'TrueSecV'}; pn = [2 1];
for s = 1:2, ph = get_param(sides{s}, 'PortHandles'); set_param(ph.Outport(pn(s)), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', nm{s}); end
Rs = [0.5 0.1 0.02]; R = struct('Rlv', {}, 'vLVat100', {}, 'idPct', {}, 'extPeakPu', {}, 'extRmsPu', {}, 'intPeakPu', {});
fprintf('\n%-8s | %-26s | %-22s | %-22s\n', 'R_lv', 'load knob 1.0 (pf .9)', 'External 3ph solid', 'Internal A-B solid');
for r = Rs
    for k = 1:3, setp(lvR{k}, 'Resistance', sprintf('%.6g', r)); end
    S = 300e6; setp(ld, 'ActivePower', sprintf('%.6g', S * 0.9), 'InductivePower', sprintf('%.6g', S * sqrt(1 - 0.81)), 'CapacitivePower', '0');
    out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on'); ls = out.get('logsout');
    [ip, ti] = logged(ls, 'TruePrimI'); [vv, tv] = logged(ls, 'TrueSecV'); ok = ti > 0.3; okv = tv > 0.3;
    idPct = 100 * mean(sqrt(mean(ip(ok, :) .^ 2, 1))) / 753.06; vpu = mean(sqrt(mean(vv(okv, :) .^ 2, 1))) / 11e3;
    % fault runs: leave the load at 60 % of rated current
    setp(ld, 'ActivePower', sprintf('%.6g', load_knob_for(60, 0.9) * S * 0.9), 'InductivePower', sprintf('%.6g', load_knob_for(60, 0.9) * S * sqrt(1 - 0.81)), 'CapacitivePower', '0');
    res = nan(1, 3);
    for f = 1:2
        if f == 1, blk = 'External_Fault'; stp = 'Step4'; ph = {'on', 'on', 'on', 'off'}; else, blk = 'Internal_Fault1'; stp = 'Step3'; ph = {'on', 'on', 'off', 'off'}; end
        setp(fb(model, blk), 'FaultA', ph{1}, 'FaultB', ph{2}, 'FaultC', ph{3}, 'GroundFault', ph{4}, 'FaultResistance', '0.01'); setp(fb(model, stp), 'Time', '0.4');
        out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
        Ip = ga(out.get('I_primary_abc')); t1 = (0:size(Ip, 1) - 1)' / fs; w = t1 >= 0.41 & t1 <= 0.45;
        res(f) = max(abs(Ip(w, :)), [], 'all') / IsecRated / sqrt(2); res(f + 1) = sqrt(mean(Ip(w, :) .^ 2, 'all')) / IsecRated; %#ok<NASGU>
        if f == 1, ext = [max(abs(Ip(w, :)), [], 'all') / IsecRated, sqrt(mean(Ip(w, :) .^ 2, 'all')) / IsecRated]; else, intp = max(abs(Ip(w, :)), [], 'all') / IsecRated; end
        setp(fb(model, stp), 'Time', '10'); setp(fb(model, blk), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    end
    R(end + 1) = struct('Rlv', r, 'vLVat100', vpu, 'idPct', idPct, 'extPeakPu', ext(1), 'extRmsPu', ext(2), 'intPeakPu', intp); %#ok<AGROW>
    fprintf('%-8.2f | V_LV %.2f pu, I %.0f %% rated | peak %.1f pu, rms %.1f pu    | peak %.1f pu\n', r, vpu, idPct, ext(1), ext(2), intp);
end
end

function finish(model)
if isappdata(0, 'HybridRelaySkipLSTM'), rmappdata(0, 'HybridRelaySkipLSTM'); end
if bdIsLoaded(model), close_system(model, 0); end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
function setp(blk, varargin)
set_param(blk, varargin{:});
for k = 1:2:numel(varargin)
    want = strtrim(varargin{k + 1}); got = strtrim(get_param(blk, varargin{k}));
    if ~strcmp(want, got)
        a = sscanf(strtrim(regexprep(want, '[\[\],;]', ' ')), '%f'); b = sscanf(strtrim(regexprep(got, '[\[\],;]', ' ')), '%f');
        assert(~isempty(a) && isequal(size(a), size(b)) && all(abs(a(:) - b(:)) <= 1e-9 * max(1, abs(a(:)))), '%s: %s should be "%s" but is "%s".', blk, varargin{k}, want, got);
    end
end
end
function x = ga(v)
if isa(v, 'timeseries'), x = double(v.Data); elseif isstruct(v), x = double(v.signals.values); else, x = double(v); end
end
function [v, t] = logged(ls, name)
el = ls.get(name); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data)); if size(v, 1) ~= numel(t), v = v.'; end
end
