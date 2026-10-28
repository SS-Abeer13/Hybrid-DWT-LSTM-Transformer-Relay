function cal = calibrate_load_v5(varargin)
%CALIBRATE_LOAD_V4 Map the load knob to realised load on TransformerWithCTSaturation_v5.
%
% Runs steady-state load sweep on v5 model with series CT wiring.
% Output: simulations/load_calibration_v5.txt and .mat

opts = struct('Knobs', logspace(log10(0.02), log10(10), 18), 'PFs', [0.8 0.9 1.0], 'StopTime', 0.6);
for k = 1:2:numel(varargin), opts.(varargin{k}) = varargin{k + 1}; end

model = 'TransformerWithCTSaturation_v5';
thisDir = fileparts(mfilename('fullpath'));
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on')
    error('CalLoad:Dirty', '%s is open with UNSAVED changes. Save or close it first.', model);
end
load_system(fullfile(thisDir, [model '.slx']));
cleanup = onCleanup(@() finish(model)); %#ok<NASGU>

Srated = 300e6;
IratedHV = Srated / (sqrt(3) * 230e3);
IratedLV = Srated / (sqrt(3) * 11e3);
IsecRated = 1.8610;   % v5 measured 1.8604 A (plant_v5_checks_A.txt), kept at the v4 value (0.03 % difference)
fs = 1600;

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

knobs = opts.Knobs(:).'; pfs = opts.PFs(:).';
nk = numel(knobs); np = numel(pfs);
pctHV = nan(np, nk); pctLV = nan(np, nk); secHV = nan(np, nk); secLV = nan(np, nk);
fprintf('%-5s %-7s | %-9s %-9s | %-9s %-9s\n', 'pf', 'knob', 'HV %rated', 'LV %rated', 'secHV %', 'secLV %');
for j = 1:np
    pf = pfs(j);
    for i = 1:nk
        knob = knobs(i);
        P = knob * Srated * pf;
        Q = knob * Srated * sqrt(max(1 - pf^2, 0));
        setp(ld, 'ActivePower', sprintf('%.6g', P), 'InductivePower', sprintf('%.6g', max(Q, 1)), 'CapacitivePower', '0');
        out = sim(model, 'StopTime', sprintf('%.3f', opts.StopTime), 'ReturnWorkspaceOutputs', 'on');
        Ip = double(out.get('I_primary_abc'));
        Is = double(out.get('I_secondary_abc'));
        t = (0:size(Ip, 1) - 1)' / fs;
        w = t >= 0.4 & t <= opts.StopTime;
        ihv_sec = mean(rms(Ip(w, :)));
        ilv_sec = mean(rms(Is(w, :)));
        secHV(j, i) = 100 * ihv_sec / IsecRated;
        secLV(j, i) = 100 * ilv_sec / IsecRated;
        pctHV(j, i) = secHV(j, i);
        pctLV(j, i) = secLV(j, i);
        fprintf('%-5.2f %-7.4f | %-9.2f %-9.2f | %-9.2f %-9.2f\n', pf, knob, pctHV(j, i), pctLV(j, i), secHV(j, i), secLV(j, i));
    end
end

cal = struct('knobs', knobs, 'pfs', pfs, 'pctHV', pctHV, 'pctLV', pctLV, 'secHV', secHV, 'secLV', secLV, ...
    'pctRated', (pctHV + pctLV) / 2, 'created', datestr(now));
save(fullfile(thisDir, 'load_calibration_v5.mat'), '-struct', 'cal');

% Write load_calibration_v5.txt
fid = fopen(fullfile(thisDir, 'load_calibration_v5.txt'), 'w');
fprintf(fid, '%% Auto-generated load calibration for v5\n');
fprintf(fid, 'cfg.LOAD_KNOB_PER_RATED = struct(''pf'', %s, ...\n', mat2str(pfs));
fprintf(fid, '    ''knob'', %s, ...\n', mat2str(knobs, 5));
fprintf(fid, '    ''pctRated'', %s);\n', mat2str(round(cal.pctRated, 3)));
fclose(fid);
fprintf('Saved load_calibration_v5.mat and load_calibration_v5.txt\n');
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
blk = hit{1};
end

function setp(blk, varargin)
set_param(blk, varargin{:});
end
