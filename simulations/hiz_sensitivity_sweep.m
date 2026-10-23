function out = hiz_sensitivity_sweep(typeName, varargin)
%HIZ_SENSITIVITY_SWEEP Step A4: how the measured differential (faultDiffPu) falls with the fault resistance of an internal fault.
%
%   hiz_sensitivity_sweep('AB')        % one fault type, 13 Rf values x 3 loads = 39 sims -> simulations/hiz_sweep_AB.mat
%   (run once per type: AB BC AC ABC AG; a MATLAB restart per type avoids the heap-corruption crash)
%   python lstm_models/hiz_bins_fit.py % merges the files, fits the Rf at 0.30 pu and 0.05 pu, writes hiz_bins.json + the figure
%
% Same definition as the dataset: faultDiffPu = max over phases of ( RMS(I_diff, t+40..60 ms) - RMS(I_diff, t-30..-10 ms) ), with I_diff
% the relay's corrected per-unit differential (base 0.9302 A). No noise, no CT mismatch, burden 1 x, source 1.0 pu, pf 0.9,
% internal fault on the LV terminals at t = 0.4 s, breakers closed. In-memory only; the model is closed without saving.

opts = struct('Rf', logspace(-1, 2, 13), 'LoadsPct', [30 60 100], 'PF', 0.9);
for k = 1:2:numel(varargin), opts.(varargin{k}) = varargin{k + 1}; end
types = struct('AB', [1 1 0 0], 'BC', [0 1 1 0], 'AC', [1 0 1 0], 'ABC', [1 1 1 0], 'AG', [1 0 0 1], 'BG', [0 1 0 1], 'CG', [0 0 1 1]);
assert(isfield(types, typeName), 'unknown fault type %s', typeName);
ph = types.(typeName); oo = {'off', 'on'};

model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on'), error('HiZ:Dirty', '%s has unsaved changes.', model); end
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() finish(model)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1'); ld = fb(model, 'Three-Phase Series RLC Load'); xf = fb(model, 'Step_down_Transformer');
setp(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); setp(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(xf, 'SetInitialFlux', 'off');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
for k = 1:3, setp(vs{k}, 'Amplitude', sprintf('%.6g', 230e3 * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, setp(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); setp(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
faults = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};
for i = 1:4, setp(fb(model, faults{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); setp(fb(model, faults{i, 2}), 'Time', '10', 'Before', '0', 'After', '1'); end
ctNames = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'};
for k = 1:6, setp(fb(fb(model, ctNames{k}), '1ohm'), 'Resistance', '1'); end
dph = get_param(fb(fb(model, 'Hybrid 87T Relay'), 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');

fb1 = fb(model, 'Internal_Fault1'); st1 = fb(model, 'Step3'); tF = 0.4; fs = 1600;
setp(fb1, 'FaultA', oo{ph(1) + 1}, 'FaultB', oo{ph(2) + 1}, 'FaultC', oo{ph(3) + 1}, 'GroundFault', oo{ph(4) + 1}); setp(st1, 'Time', sprintf('%.6f', tF));
Rf = opts.Rf(:).'; L = opts.LoadsPct(:).'; D = nan(numel(L), numel(Rf)); Lreal = nan(numel(L), numel(Rf));
fprintf('type %s | Rf(ohm): %s\n', typeName, mat2str(round(Rf, 3)));
for a = 1:numel(L)
    knob = load_knob_for(L(a), opts.PF);
    setp(ld, 'ActivePower', sprintf('%.6g', knob * 300e6 * opts.PF), 'InductivePower', sprintf('%.6g', knob * 300e6 * sqrt(1 - opts.PF ^ 2)), 'CapacitivePower', '0');
    for b = 1:numel(Rf)
        setp(fb1, 'FaultResistance', sprintf('%.6g', Rf(b)));
        o = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
        el = o.get('logsout').get('I_diff_comp'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
        tc = el.Values.Time; dc = squeeze(double(el.Values.Data)); if size(dc, 2) ~= 3, dc = dc.'; end
        rm = @(t1, t2) sqrt(mean(dc(tc >= t1 & tc < t2, :) .^ 2, 1));
        D(a, b) = max(rm(tF + 0.04, tF + 0.06) - rm(tF - 0.03, tF - 0.01));
        Is = ga(o.get('I_secondary_abc')); t = (0:size(Is, 1) - 1)' / fs; w = t > 0.2 & t < 0.37;
        Lreal(a, b) = 100 * mean(sqrt(mean(Is(w, :) .^ 2, 1))) / 0.9302;
    end
    fprintf('load %3.0f %% (realised %.0f %%): faultDiffPu = %s\n', L(a), mean(Lreal(a, :)), mat2str(round(D(a, :), 3)));
end
out = struct('type', typeName, 'phases', ph, 'Rf', Rf, 'loadsPct', L, 'loadRealisedPct', Lreal, 'faultDiffPu', D, 'created', datestr(now)); %#ok<TNOW1,DATST>
save(fullfile(thisDir, sprintf('hiz_sweep_%s.mat', typeName)), '-struct', 'out');
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
