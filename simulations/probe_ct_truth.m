function r = probe_ct_truth()
%PROBE_CT_TRUTH True transformer line currents (V-I measurement blocks) vs CT-secondary signals: real CT ratios. In-memory only.
model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() close_system(model, 0)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
fn = @(n) {fb(model, n)};
pri = fn('Primary_side'); sec = fn('Secondary_side'); assert(numel(pri) == 1 && numel(sec) == 1);
for b = [pri sec]
    ph = get_param(b{1}, 'PortHandles'); disp(['ports ' b{1} ': out ' num2str(numel(ph.Outport))]);
    for q = 1:numel(ph.Outport)
        set_param(ph.Outport(q), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', sprintf('%s_out%d', strtok(get_param(b{1}, 'Name'), '_'), q));
    end
end
hv = fn('Three-Phase Breaker'); lv = fn('Three-Phase Breaker1');
set_param(hv{1}, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); set_param(lv{1}, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
for nm = {'Internal_Fault1', 'Internal_Fault2', 'Internal_Fault3', 'External_Fault'}
    b = fn(nm{1}); set_param(b{1}, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
end
for st = {'Step3', 'Step_Evolve2', 'Step_Evolve3', 'Step4'}
    b = fn(st{1}); set_param(b{1}, 'Time', '10');
end
nmu = fn('Noise Merging Unit');
for k = 1:6
    set_param([nmu{1} '/Noise_Gain_' num2str(k)], 'Gain', '0'); set_param([nmu{1} '/CT_Gain_Mismatch_' num2str(k)], 'Gain', '1');
end
load = find_system(model, 'SearchDepth', 1, 'Name', sprintf('Three-Phase\nSeries RLC Load'));
if isempty(load), L = find_system(model, 'SearchDepth', 1, 'BlockType', 'SubSystem'); end %#ok<NASGU>
all = find_system(model, 'SearchDepth', 1, 'Type', 'Block'); ld = all(contains(all, 'RLC Load'));
assert(numel(ld) == 1, 'load block not unique'); ld = ld{1};
fs = 1600; Srated = 300e6; pf = 0.95; r = struct('knob', [], 'IhvTrue', [], 'IlvTrue', [], 'IhvSec', [], 'IlvSec', [], 'Vlv', [], 'Vhv', []);
for knob = [0.1 1 5]
    S = knob * Srated;
    set_param(ld, 'ActivePower', sprintf('%.6g', S * pf), 'InductivePower', sprintf('%.6g', S * sqrt(1 - pf ^ 2)), 'CapacitivePower', '0');
    out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
    ls = out.get('logsout');
    Ip = ga(out.get('I_primary_abc')); Is = ga(out.get('I_secondary_abc'));
    t2 = (0:size(Ip, 1) - 1)' / fs; ok2 = t2 > 0.3;
    for nm = {'Primary_out1', 'Primary_out2', 'Secondary_out1', 'Secondary_out2'}
        el = ls.get(nm{1}); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
        v = squeeze(double(el.Values.Data)); tt = el.Values.Time; if size(v, 1) ~= numel(tt), v = v.'; end
        fprintf('knob %.1f  %-14s size %s  rms %.5g\n', knob, nm{1}, mat2str(size(v)), mean(sqrt(mean(abs(v(tt > 0.3, :)) .^ 2, 1))));
    end
    fprintf('knob %.1f  CT sec HV %.4f A  LV %.4f A\n', knob, mean(sqrt(mean(Ip(ok2, :) .^ 2, 1))), mean(sqrt(mean(Is(ok2, :) .^ 2, 1))));
end
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times', name, numel(hit)); blk = hit{1};
end

function x = ga(v)
if isa(v, 'timeseries'), x = double(v.Data); elseif isstruct(v), x = double(v.signals.values); else, x = double(v); end
end
