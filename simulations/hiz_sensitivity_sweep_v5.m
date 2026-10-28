function out = hiz_sensitivity_sweep_v5(plant, typeName, varargin)
%HIZ_SENSITIVITY_SWEEP_V5 HiZ internal-fault sweep on a v5 plant: faultDiffPu vs fault resistance Rf at three loads (V8 option (a), 2026-10-28).
%
%   hiz_sensitivity_sweep_v5('A', 'AB')   % TransformerWithCTSaturation_v5
%   hiz_sensitivity_sweep_v5('B', 'AG')   % TransformerB_v5 (its own sweep: v4 plant B used the plant-A bins)
%
% Measures faultDiffPu (rise of the corrected differential at 40-60 ms after inception over its pre-fault value, from the model's own I_diff chart output,
% no noise, burden 1 ohm, source phase 30 deg) for 17 Rf values x 3 loads. Saves simulations/hiz_sweep_v5_<plant>_<type>.mat.
% The load knob comes from the plant's v5 load calibration (load_calibration_v5.mat / load_calibration_plant_b_v5.mat).
opts = struct('Rf', logspace(-2, 2, 17), 'LoadsPct', [30 60 100], 'PF', 0.9);
for k = 1:2:numel(varargin), opts.(varargin{k}) = varargin{k + 1}; end
types = struct('AB', [1 1 0 0], 'BC', [0 1 1 0], 'AC', [1 0 1 0], 'ABC', [1 1 1 0], 'AG', [1 0 0 1], 'BG', [0 1 0 1], 'CG', [0 0 1 1]);
assert(isfield(types, typeName), 'unknown fault type %s', typeName);
ph = types.(typeName); oo = {'off', 'on'};
thisDir = fileparts(mfilename('fullpath'));
if strcmpi(plant, 'A')
    model = 'TransformerWithCTSaturation_v5'; S = 300e6; Vhv = 230e3; Ibase = 1.8610; calFile = 'load_calibration_v5.mat';
else
    model = 'TransformerB_v5'; S = 40e6; Vhv = 132e3; Ibase = 0.8658; calFile = 'load_calibration_plant_b_v5.mat'; plant = 'B';
end
plant = upper(plant);
cm = load(fullfile(thisDir, calFile)); cal = struct('pf', cm.pfs, 'knob', cm.knobs, 'pctRated', cm.pctRated);
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on'), error('HiZ:Dirty', '%s has unsaved changes.', model); end
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() finish(model)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1'); ld = fb(model, 'Three-Phase Series RLC Load'); xf = fb(model, 'Step_down_Transformer');
setp(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); setp(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(xf, 'SetInitialFlux', 'off');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
for k = 1:3, setp(vs{k}, 'Amplitude', sprintf('%.6g', Vhv * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, setp(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); setp(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
faults = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};
for i = 1:4, setp(fb(model, faults{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); setp(fb(model, faults{i, 2}), 'Time', '10', 'Before', '0', 'After', '1'); end
if strcmp(plant, 'B')
    for pr = {'Internal_Fault_HV', 'Step_HV'; 'External_Fault_HV', 'Step_ExtHV'}.'
        setp(fb(model, pr{1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
        setp(fb(model, pr{2}), 'Time', '10', 'Before', '0', 'After', '1');
    end
end
ctNames = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}; burden = 1; if strcmp(plant, 'B'), burden = 2.5; end
for k = 1:6, setp(fb(fb(model, ctNames{k}), '1ohm'), 'Resistance', sprintf('%.6g', burden)); end
dph = get_param(fb(fb(model, 'Hybrid 87T Relay'), 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');

fb1 = fb(model, 'Internal_Fault1'); st1 = fb(model, 'Step3'); tF = 0.4; fs = 1600;
setp(fb1, 'FaultA', oo{ph(1) + 1}, 'FaultB', oo{ph(2) + 1}, 'FaultC', oo{ph(3) + 1}, 'GroundFault', oo{ph(4) + 1}); setp(st1, 'Time', sprintf('%.6f', tF));
Rf = opts.Rf(:).'; L = opts.LoadsPct(:).'; D = nan(numel(L), numel(Rf)); Lreal = nan(numel(L), numel(Rf));
fprintf('plant %s type %s | Rf(ohm): %s\n', plant, typeName, mat2str(round(Rf, 3)));
for a = 1:numel(L)
    knob = load_knob_for(L(a), opts.PF, cal);
    setp(ld, 'ActivePower', sprintf('%.6g', knob * S * opts.PF), 'InductivePower', sprintf('%.6g', knob * S * sqrt(1 - opts.PF ^ 2)), 'CapacitivePower', '0');
    for b = 1:numel(Rf)
        setp(fb1, 'FaultResistance', sprintf('%.6g', Rf(b)));
        o = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
        el = o.get('logsout').get('I_diff_comp'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
        tc = el.Values.Time; dc = squeeze(double(el.Values.Data)); if size(dc, 2) ~= 3, dc = dc.'; end
        rm = @(t1, t2) sqrt(mean(dc(tc >= t1 & tc < t2, :) .^ 2, 1));
        D(a, b) = max(rm(tF + 0.04, tF + 0.06) - rm(tF - 0.03, tF - 0.01));
        Is = ga(o.get('I_secondary_abc')); t = (0:size(Is, 1) - 1)' / fs; w = t > 0.2 & t < 0.37;
        Lreal(a, b) = 100 * mean(sqrt(mean(Is(w, :) .^ 2, 1))) / Ibase;
    end
    fprintf('load %3.0f %% (realised %.0f %%): faultDiffPu = %s\n', L(a), mean(Lreal(a, :)), mat2str(round(D(a, :), 3)));
end
out = struct('plant', plant, 'type', typeName, 'phases', ph, 'Rf', Rf, 'loadsPct', L, 'loadRealisedPct', Lreal, 'faultDiffPu', D, 'created', datestr(now)); %#ok<TNOW1,DATST>
save(fullfile(thisDir, sprintf('hiz_sweep_v5_%s_%s.mat', plant, typeName)), '-struct', 'out');
fprintf('Saved hiz_sweep_v5_%s_%s.mat\n', plant, typeName);
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
end
function x = ga(v)
if isa(v, 'timeseries'), x = squeeze(double(v.Data)); elseif isstruct(v), x = squeeze(double(v.signals.values)); else, x = squeeze(double(v)); end
if size(x, 2) ~= 3 && size(x, 1) == 3, x = x.'; end
end
