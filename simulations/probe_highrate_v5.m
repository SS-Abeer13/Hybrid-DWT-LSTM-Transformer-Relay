function probe_highrate_v5(plant)
%PROBE_HIGHRATE_V5 D1 feasibility (BENCHMARK_FAIRNESS_PLAN.md Part 2): the same external 3-phase fault simulated with the standard settings
% (powergui Ts 100 us, noise Ts 100 us, relay inputs logged at 1600 Hz) and with the high-rate settings (powergui Ts 25 us = 40 kHz,
% noise Ts 25 us, relay-input ZOH and the two To Workspace blocks at 50 us = 20 kHz). Everything is changed in memory only; nothing is saved.
% Reports wall time, memory of one trace, the noise-free agreement of the fundamental-frequency RMS and the spectrum above 1.6 kHz.
if nargin < 1, plant = 'A'; end
thisDir = fileparts(mfilename('fullpath'));
if strcmpi(plant, 'A'), model = 'TransformerWithCTSaturation_v5'; S = 300e6; else, model = 'TransformerB_v5'; S = 40e6; end
bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
ef = fb(model, 'External_Fault'); set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.01', 'GroundResistance', '0.01');
set_param(fb(model, 'Step4'), 'Time', '0.5', 'Before', '0', 'After', '1');
ld = fb(model, 'Three-Phase Series RLC Load'); set_param(ld, 'ActivePower', sprintf('%.6g', 0.6 * S * 0.9), 'InductivePower', sprintf('%.6g', 0.6 * S * sqrt(1 - 0.81)), 'CapacitivePower', '0');
gui = find_system(model, 'SearchDepth', 1, 'MaskType', 'PSB option menu block'); gui = gui{1};
blwn = fb(nmu, 'Band-Limited White Noise'); zoh = fa(model, 'ZOH_1600'); tw = {fa(model, 'To Workspace'), fa(model, 'To Workspace1')};
orig = struct('gui', get_param(gui, 'SampleTime'), 'blwn', get_param(blwn, 'Ts'), 'zoh', get_param(zoh, 'SampleTime'), 'tw', get_param(tw{1}, 'SampleTime'));
fid = fopen(fullfile(thisDir, sprintf('highrate_probe_v5_%s.txt', upper(plant))), 'w');
pr = @(varargin) fprintf2(fid, varargin{:});
pr('High-rate feasibility probe, plant %s, %s. Original: powergui %s, noise Ts %s, ZOH %s, To Workspace %s\n', upper(plant), datestr(now), orig.gui, orig.blwn, orig.zoh, orig.tw);
res = struct();
for cfg = {'standard', 'highrate'}
    c = cfg{1};
    if strcmp(c, 'highrate')
        set_param(gui, 'SampleTime', '25e-6'); set_param(blwn, 'Ts', '25e-6'); set_param(zoh, 'SampleTime', '50e-6'); set_param(tw{1}, 'SampleTime', '50e-6'); set_param(tw{2}, 'SampleTime', '50e-6');
    end
    t0 = tic; o = sim(model, 'StopTime', '1.1', 'ReturnWorkspaceOutputs', 'on'); wall = toc(t0);
    Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc')); n = size(Ip, 1); fs = n / 1.1;
    whos_ip = whos('Ip');
    res.(c) = struct('wall_s', wall, 'n', n, 'fs', fs, 'Ip', Ip, 'Is', Is);
    pr('%-9s: wall %.1f s, %d samples (%.0f Hz), one trace (6 channels) = %.2f MB\n', c, wall, n, fs, 6 * whos_ip.bytes / 1e6);
end
% agreement: LV fundamental RMS in 0.55-0.65 s (50 Hz, one-cycle windows) and energy above 1.6 kHz
for c = {'standard', 'highrate'}
    r = res.(c{1}); fs = r.fs; t = (0:r.n - 1)' / fs; w = t >= 0.55 & t <= 0.65; x = r.Is(w, :);
    X = abs(fft(x - mean(x, 1))) / size(x, 1); f = (0:size(x, 1) - 1)' * fs / size(x, 1); hi = f > 1600 & f < fs / 2;
    pr('%-9s: LV RMS (0.55-0.65 s) per phase %s A; energy above 1.6 kHz / total (per phase) %s\n', c{1}, mat2str(sqrt(mean(x .^ 2, 1)), 5), mat2str(sum(X(hi, :) .^ 2, 1) ./ sum(X(f < fs / 2, :) .^ 2, 1), 3));
end
fclose(fid);
end
function fprintf2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end
function x = ga(v)
if isa(v, 'timeseries'), x = squeeze(double(v.Data)); elseif isstruct(v), x = squeeze(double(v.signals.values)); else, x = squeeze(double(v)); end
if size(x, 2) ~= 3 && size(x, 1) == 3, x = x.'; end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end

function blk = fa(model, name)
h = find_system(model, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Name', name);
assert(numel(h) == 1, 'block %s found %d times', name, numel(h)); blk = h{1};
end
