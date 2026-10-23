function probe_overexc_recovery()
%PROBE_OVEREXC_RECOVERY Step A6 probe (in memory only): do over-excitation and recovery inrush give the harmonic signatures we need?
%   Differential used = plant-compensated  d = Is - Ip*M  (the LSTM input), harmonics from a one-cycle DFT of d (and of the HV current).
%   Over-excitation: source scale 1.05 / 1.2 / 1.4 pu, no fault.  Recovery: external 3-phase fault cleared after 60 ms (existing External_Fault block),
%   fault switching by the block's own SwitchTimes (External off).
model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() finish(model)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
fs = 1600; M = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1'); ld = fb(model, 'Three-Phase Series RLC Load'); xf = fb(model, 'Step_down_Transformer');
setp(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); setp(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(xf, 'SetInitialFlux', 'off');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, setp(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); setp(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
f = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};
for i = 1:4, setp(fb(model, f{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); setp(fb(model, f{i, 2}), 'Time', '10'); end
ctn = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}; for k = 1:6, setp(fb(fb(model, ctn{k}), '1ohm'), 'Resistance', '1'); end
kn = load_knob_for(30, 0.9); setp(ld, 'ActivePower', sprintf('%.6g', kn * 300e6 * 0.9), 'InductivePower', sprintf('%.6g', kn * 300e6 * sqrt(1 - 0.81)), 'CapacitivePower', '0');
sides = {fb(model, 'Primary_side')}; ph = get_param(sides{1}, 'PortHandles');
fprintf('%-34s | %-10s %-10s %-10s | %-10s\n', 'case', 'd rms (pu)', 'd 5th/1st', 'd 2nd/1st', 'HV 5th/1st');
% -------- over-excitation
for sc = [1.22 1.28 1.32 1.36 1.40 1.45 1.50 1.55]
    for k = 1:3, setp(vs{k}, 'Amplitude', sprintf('%.6g', sc * 230e3 * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
    o = sim(model, 'StopTime', '0.8', 'ReturnWorkspaceOutputs', 'on');
    [r, h5, h2, hv5] = harm(o, M, 0.60, fs);
    fprintf('%-34s | %-10.4f %-10.3f %-10.3f | %-10.3f\n', sprintf('overexcitation source %.2f pu', sc), r, h5, h2, hv5);
end
for k = 1:3, setp(vs{k}, 'Amplitude', sprintf('%.6g', 230e3 * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
end

function [r, h5, h2, hv5] = harm(o, M, t0, fs)
Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc')); d = Is - Ip * M;
i0 = round(t0 * fs) + 1; w = (i0:i0 + 31)';
F = abs(fft(d(w, :), [], 1)); Fh = abs(fft(Ip(w, :), [], 1));
r = mean(sqrt(mean(d(w, :) .^ 2, 1))) / 0.9302;
h5 = mean(F(6, :) ./ max(F(2, :), 1e-4)); h2 = mean(F(3, :) ./ max(F(2, :), 1e-4)); hv5 = mean(Fh(6, :) ./ max(Fh(2, :), 1e-4));   % 32-pt DFT: bin 2 = 50 Hz, 3 = 100 Hz, 6 = 250 Hz
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
