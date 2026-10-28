function probe_knee_sweep_v5(plant, scales)
%PROBE_KNEE_SWEEP_V5 CT waveform deviation on an external 3-phase solid fault vs CT saturation-knee scale (in memory only).
%   probe_knee_sweep_v5('B', [1 2 4 8]) multiplies the flux column of the CT Saturation curve by each scale.
if strcmpi(plant, 'A'), model = 'TransformerWithCTSaturation_v5'; burden0 = 1.0; S = 300e6; Vhv = 230e3; Vlv = 11e3;
else, model = 'TransformerB_v5'; burden0 = 2.5; S = 40e6; Vhv = 132e3; Vlv = 33e3; end
Ihv = S / (sqrt(3) * Vhv); Ilv = S / (sqrt(3) * Vlv); ts = 1 / 1600; thisDir = fileparts(mfilename('fullpath'));
bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
for k = 1:2
    sd = {'Primary_side', 'Secondary_side'}; ph = get_param(fb(model, sd{k}), 'PortHandles');
    set_param(ph.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', sprintf('I%d', k));
end
set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
ef = fb(model, 'External_Fault'); set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(fb(model, 'Step4'), 'Time', '0.3', 'Before', '0', 'After', '1');
ld = fb(model, 'Three-Phase Series RLC Load'); set_param(ld, 'ActivePower', sprintf('%.6g', 0.9 * S), 'InductivePower', sprintf('%.6g', S * sqrt(1 - 0.81)), 'CapacitivePower', '0');
ctn = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}; base = [0 0; 0.0002 4; 0.0006 11; 0.0015 17; 0.004 19.5; 0.05 21.5; 0.5 24];
% ratio from a no-fault load run
set_param(ef, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
o = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
[iH, tH] = sig(o, 'I1'); [iL, tL] = sig(o, 'I2'); Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc')); t1 = (0:size(Ip, 1) - 1)' * ts;
w = @(t) t >= 0.4; ratioHV = mean(rms(iH(w(tH), :))) / mean(rms(Ip(w(t1), :))); ratioLV = mean(rms(iL(w(tL), :))) / mean(rms(Is(w(t1), :)));
fprintf('plant %s: measured ratios HV %.2f, LV %.2f\n', plant, ratioHV, ratioLV);
set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on');
for sc = scales
    for mult = [1 4]
        for k = 1:6
            cb = fb(model, ctn{k}); kids = find_system(cb, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
            ct = kids{contains(kids, 'CT ') & ~contains(kids, 'ohm')}; b1 = find_system(cb, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Name', '1ohm');
            cur = base; cur(:, 2) = cur(:, 2) * sc; set_param(ct, 'Saturation', mat2str(cur, 6)); set_param(b1{1}, 'Resistance', sprintf('%.6g', mult * burden0));
        end
        o = sim(model, 'StopTime', '0.5', 'ReturnWorkspaceOutputs', 'on');
        [iH, tH] = sig(o, 'I1'); [iL, tL] = sig(o, 'I2'); Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc'));
        out = zeros(1, 4); q = 0;
        for lohi = [0.30 0.34; 0.40 0.46]'
            sel = t1 >= lohi(1) & t1 <= lohi(2); tq = t1(sel); a = interp1(tH, iH, tq); b = interp1(tL, iL, tq); q = q + 1;
            out(2 * q - 1) = 100 * max(sqrt(mean((ratioHV * Ip(sel, :) - a) .^ 2, 1)) ./ sqrt(mean(a .^ 2, 1)));
            out(2 * q) = 100 * max(sqrt(mean((ratioLV * Is(sel, :) - b) .^ 2, 1)) ./ sqrt(mean(b .^ 2, 1)));
        end
        fprintf('knee scale %4.1f (knee ~%3.0f pu), burden %d x: true RMS %.2f pu | deviation early HV %.1f%% LV %.1f%% | steady HV %.1f%% LV %.1f%%\n', ...
            sc, 18 * sc, mult, 0.5 * (mean(rms(iH(tH >= 0.4 & tH <= 0.46, :))) / Ihv + mean(rms(iL(tL >= 0.4 & tL <= 0.46, :))) / Ilv), out);
    end
end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
function [v, t] = sig(o, name)
el = o.get('logsout').get(name); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data)); if size(v, 1) ~= numel(t), v = v.'; end
end
function x = ga(v)
if isa(v, 'timeseries'), x = squeeze(double(v.Data)); elseif isstruct(v), x = squeeze(double(v.signals.values)); else, x = squeeze(double(v)); end
if size(x, 2) ~= 3 && size(x, 1) == 3, x = x.'; end
end
