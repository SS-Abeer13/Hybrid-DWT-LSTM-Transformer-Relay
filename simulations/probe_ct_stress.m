function R = probe_ct_stress(varargin)
%PROBE_CT_STRESS How CT burden and remanence change the CT ratio error (step A3). In-memory only, nothing saved.
%   R = probe_ct_stress            % table: fault type x burden x remanence -> max ratio error (HV and LV CTs)
%
% Ratio error per phase = RMS( N*I_ct - I_true ) / RMS( I_true ) over the post-fault window [t+5 ms, t+45 ms]; N = effective CT ratio
% (HV 809.6, LV 16925) from the healthy ratio, I_true = line current of the V-I measurement blocks. Reported: max over phases.

model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() finish(model)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
fs = 1600; Nhv = 809.6; Nlv = 16925;

hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1'); ld = fb(model, 'Three-Phase Series RLC Load'); xf = fb(model, 'Step_down_Transformer');
setp(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); setp(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(xf, 'SetInitialFlux', 'off');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
for k = 1:3, setp(vs{k}, 'Amplitude', sprintf('%.6g', 230e3 * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, setp(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); setp(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
faults = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};
for i = 1:4, setp(fb(model, faults{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); setp(fb(model, faults{i, 2}), 'Time', '10', 'Before', '0', 'After', '1'); end
% load 80 % of rated at pf 0.9
setp(ld, 'ActivePower', sprintf('%.6g', load_knob_for(60, 0.9) * 300e6 * 0.9), 'InductivePower', sprintf('%.6g', load_knob_for(60, 0.9) * 300e6 * sqrt(1 - 0.81)), 'CapacitivePower', '0');
% CT blocks: the six CT subsystems, each with a burden branch '1ohm' and a saturable transformer
cts = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'};
for i = 1:6
    c = fb(model, cts{i}); CT.burden{i} = fb(c, '1ohm');
    kids = find_system(c, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
    CT.xf{i} = kids{contains(kids, 'CT ') & ~contains(kids, '1ohm')};
end
fprintf('burden block: %s | transformer: %s | InitialFlux = %s\n', CT.burden{1}, CT.xf{1}, get_param(CT.xf{1}, 'InitialFlux'));
% log the true line currents (V-I measurement out2)
sides = {fb(model, 'Primary_side'), fb(model, 'Secondary_side')}; nm = {'TruePrimI', 'TrueSecI'};
for s = 1:2, ph = get_param(sides{s}, 'PortHandles'); set_param(ph.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', nm{s}); end

conds = [3 0; 4 0; 6 0; 8 0; 12 0];       % burden multiple, remanence pu (remanence has no effect, see log)
types = {'Ext A-G', [1 0 0 1], 'External_Fault', 'Step4'; 'Ext A-B', [1 1 0 0], 'External_Fault', 'Step4'; 'Ext A-B-G', [1 1 0 1], 'External_Fault', 'Step4'; 'Ext A-B-C', [1 1 1 0], 'External_Fault', 'Step4'};
R = struct('fault', {}, 'burden', {}, 'remanence', {}, 'errHV', {}, 'errLV', {}, 'peakHV', {});
fprintf('\n%-13s %-8s %-9s | %-9s %-9s | %-10s\n', 'fault', 'burden x', 'remanence', 'err HV %', 'err LV %', 'peak Is HV');
for f = 1:size(types, 1)
    ph = types{f, 2}; oo = {'off', 'on'};
    setp(fb(model, types{f, 3}), 'FaultA', oo{ph(1) + 1}, 'FaultB', oo{ph(2) + 1}, 'FaultC', oo{ph(3) + 1}, 'GroundFault', oo{ph(4) + 1}, 'FaultResistance', '0.01');
    setp(fb(model, types{f, 4}), 'Time', '0.4');
    for c = 1:size(conds, 1)
        for i = 1:6
            setp(CT.burden{i}, 'Resistance', sprintf('%.6g', conds(c, 1)));
            sgn = [1 -1 1 1 -1 1]; set_param(CT.xf{i}, 'InitialFlux', sprintf('%.6g', sgn(i) * conds(c, 2)));
        end
        out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
        Ip = ga(out.get('I_primary_abc')); Is = ga(out.get('I_secondary_abc')); ls = out.get('logsout');
        [tp, tt] = logged(ls, 'TruePrimI'); [ts, ~] = logged(ls, 'TrueSecI');
        t1 = (0:size(Ip, 1) - 1)' / fs; w1 = t1 >= 0.405 & t1 <= 0.445;
        tpi = interp1(tt, tp, t1(w1)); tsi = interp1(tt, ts, t1(w1));        % true currents (10 kHz) at the 1600 Hz relay samples
        eHV = max(sqrt(mean((Nhv * Ip(w1, :) - tpi) .^ 2, 1)) ./ sqrt(mean(tpi .^ 2, 1)));
        eLV = max(sqrt(mean((Nlv * Is(w1, :) - tsi) .^ 2, 1)) ./ sqrt(mean(tsi .^ 2, 1)));
        R(end + 1) = struct('fault', types{f, 1}, 'burden', conds(c, 1), 'remanence', conds(c, 2), 'errHV', 100 * eHV, 'errLV', 100 * eLV, 'peakHV', max(abs(Ip(:)))); %#ok<AGROW>
        fprintf('%-13s %-8.1f %-9.2f | %-9.1f %-9.1f | %-10.2f\n', types{f, 1}, conds(c, 1), conds(c, 2), 100 * eHV, 100 * eLV, max(abs(Ip(:))));
    end
    setp(fb(model, types{f, 4}), 'Time', '10'); setp(fb(model, types{f, 3}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
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
