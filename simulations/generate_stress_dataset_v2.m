function outFile = generate_stress_dataset_v2(nSamples, varargin)
%GENERATE_STRESS_DATASET_V2 Stress dataset where every scenario parameter is APPLIED and VERIFIED.
%
%   generate_stress_dataset_v2('selftest')        % 5 quick cases, prints the checks, saves nothing
%   outFile = generate_stress_dataset_v2(1200)    % full run -> ONE file datasets\StressDataset_v2_<run>.mat
%   generate_stress_dataset_v2(1200, 'Resume', '20261019_201500')   % continue an interrupted run
%
% WHY v2 (bugs found in generate_stress_dataset_headless.m, 2026-10-19):
%  1. configureBreakersClosed used SwitchTimes '[]', set_param failed, and try/catch hid it.
%     The breakers stayed at the LAST inrush sample's settings, so every internal fault (and the
%     early external faults) was energised at 0.781 s instead of faulting an energised transformer.
%  2. injectNoiseCT was an empty placeholder: noise level and CT mismatch were never applied.
%     All 168 'Normal' traces were byte-identical.
%  3. The Noise Merging Unit used ONE noise source for all six CT channels, so the noise was
%     identical on primary and secondary and cancelled in Ip - Is.
%  4. Load was fixed at 10 MW (3 % of 300 MVA). Every 'Normal' case was the same light load.
%  5. 'HiZ' internal faults used 50-300 ohm on the 11 kV side: ~0.1 % of rated current,
%     physically invisible to a differential relay. They were only "detected" through the
%     0.781 s energisation transient.
%  5b. Internal_Fault2 (B-G) / Internal_Fault3 were switched on at 0.05 s by Step_Evolve2/3 and never
%     reset, silently turning e.g. 'Internal_AG' into an A-B-G fault.
%  5c. Physics: faults sit on the 11 kV DELTA winding; single-line-to-ground fault current returns only
%     through the grounded-Y load neutral, so it scales with load (invisible at the old fixed 3 % load).
%  6. Three copies of the same 600 traces were saved (checkpoint + two finals).
%
% WHAT v2 DOES:
%  * Every set_param is read back and compared; a mismatch STOPS the run (no silent catch).
%  * Breakers are disconnected from the relay (External = off) and driven by switching times.
%    Internal and external faults happen on an ENERGISED, LOADED transformer (0.30-0.75 s).
%    Switch-onto-fault, fault-during-inrush and external-during-inrush are separate scenarios.
%  * Load 5-120 % of 300 MVA, power factor 0.85-1.0, source voltage 0.95-1.05 pu and a random
%    source phase (random point-on-wave at fault/energisation).
%  * Six INDEPENDENT noise channels (Demux inserted in memory), noise 0.05-1 % of rated CT
%    secondary current (1-3 % for stress cases), CT gain mismatch +/-2 % (+/-5 % stress).
%  * High-impedance faults use 1-25 ohm (detectable to borderline). The measured compensated
%    differential (faultDiffPu) is stored so the training step can set a sensitivity limit.
%  * After each simulation the waveform is checked: energisation time, fault time (+/-12.5 ms),
%    noise level and duplicate waveform. Results are stored per sample (checkPassed etc.).
%  * Reproducible: sample k uses rng(seed + k). One output file. The .slx is NEVER saved:
%    all changes are in memory and discarded at the end (close_system(model, 0)).
%
% Output fields (dataset.*) are compatible with lstm_models/stress_dataset.py.

model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);
datasetsDir = fullfile(projectDir, 'datasets');

selfTest = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'selftest');
if nargin < 1 || isempty(nSamples) || selfTest, nSamplesNum = 1200; else, nSamplesNum = nSamples; end
opts = struct('Resume', '', 'Seed', 20261019, 'StopTime', 1.10);
for k = 1:2:numel(varargin), opts.(varargin{k}) = varargin{k + 1}; end

cfg = struct();
cfg.version   = 'v2-2026-10-19';
cfg.fs        = 1600;
cfg.stopTime  = opts.StopTime;
cfg.seed      = opts.Seed;
cfg.Srated    = 300e6;
cfg.Inom      = [1.8827 1.8827 1.8827 0.8557 0.8557 0.8557];  % rated CT secondary current (A): HV x3, LV x3
cfg.timingTol = 0.0125;                                       % allowed |detected - intended| event time (s)

% ---------------------------------------------------------------- model, safely in memory only
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on')
    error('GenV2:Dirty', ['%s is open with UNSAVED changes. Save or close it first: this generator ' ...
        'changes the model in memory and closes it WITHOUT saving.'], model);
end
load_system(fullfile(thisDir, [model '.slx']));
cleanup = onCleanup(@() finishGeneration(model));  %#ok<NASGU>  never saves the .slx, clears the LSTM skip flag

B = locateBlocks(model);
prepareModelForGeneration(B);
cfg.blwnStd = sqrt(0.1 / str2double(get_param(B.blwn, 'Ts')));      % BLWN output std (Cov 0.1 per channel)
cfg.quantStep = str2double(get_param(findBlock(B.nmu, 'Quantizer'), 'QuantizationInterval'));
ST = scenarioTable();

if selfTest
    runSelfTest(model, B, ST, cfg);
    outFile = '';
    return;
end

% ---------------------------------------------------------------- plan / resume
weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
counts(1) = counts(1) + (nSamplesNum - sum(counts));
N = sum(counts);
plan = repelem(1:numel(ST), counts);

if isempty(opts.Resume)
    runId = datestr(now, 'yyyymmdd_HHMMSS'); %#ok<TNOW1,DATST>
    dataset = preallocate(N);
    startAt = 1;
else
    runId = opts.Resume;
    P = load(partialFile(datasetsDir, runId));
    assert(isequal(P.generationConfig.seed, cfg.seed) && P.generationConfig.N == N, ...
        'GenV2:Resume', 'Resume file was made with a different seed or sample count.');
    dataset = P.dataset;
    startAt = find(cellfun(@isempty, dataset.simulationStatus), 1);
    if isempty(startAt), startAt = N + 1; end
end
cfg.N = N; cfg.runId = runId;

fprintf('=== Stress dataset v2 | run %s | %d samples | %d scenarios ===\n', runId, N, numel(ST));
for i = 1:numel(ST), fprintf('  %-26s %4d\n', ST(i).name, counts(i)); end

fingerprints = containers.Map('KeyType', 'char', 'ValueType', 'double');
for j = 1:startAt - 1
    if ~isempty(dataset.fingerprint{j}), fingerprints(dataset.fingerprint{j}) = j; end
end

t0 = tic;
for idx = startAt:N
    sc = ST(plan(idx));
    p = drawParameters(sc, cfg.seed + idx);
    p.sampleSeed = cfg.seed + idx;
    applyScenario(B, sc, p, cfg);
    [rec, status] = simulateAndCheck(model, B, sc, p, cfg, fingerprints);
    dataset = store(dataset, idx, sc, p, rec, status);
    if ~isempty(rec.fingerprint) && ~fingerprints.isKey(rec.fingerprint)
        fingerprints(rec.fingerprint) = idx;
    end

    el = toc(t0); done = idx - startAt + 1;
    fprintf('[%4d/%4d] %-24s %-4s | load %4.0f%% pf %.2f noise %.2f%% | event %6s det %6s | %s | ETA %.0f min\n', ...
        idx, N, sc.name, status, 100 * p.loadPu, p.pf, p.noisePct, fmtT(p.tEvent), fmtT(rec.eventDetected), ...
        checkText(rec), el / done * (N - idx) / 60);

    if mod(idx, 25) == 0
        generationConfig = cfg; scenarioTableOut = ST; %#ok<NASGU>
        save(partialFile(datasetsDir, runId), 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
    end
end

generationConfig = cfg; scenarioTableOut = ST; %#ok<NASGU>
outFile = fullfile(datasetsDir, sprintf('StressDataset_v2_%s.mat', runId));
save(outFile, 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
if isfile(partialFile(datasetsDir, runId)), delete(partialFile(datasetsDir, runId)); end

ok = dataset.checkPassed == 1;
fprintf('\nSaved ONE file: %s\n', outFile);
fprintf('Checks passed: %d / %d  (failed samples are kept but flagged; training skips them)\n', sum(ok), N);
fprintf('Duplicate waveforms: %d | timing failures: %d | events too small to see: %d | sim errors: %d\n', ...
    sum(dataset.duplicate == 1), sum(dataset.timingOK == 0), sum(dataset.eventVisible == 0), ...
    sum(~strcmp(dataset.simulationStatus, 'Success')));
end

% =====================================================================================
% Scenarios
% =====================================================================================
function ST = scenarioTable()
% name | zone | kind | fA fB fC fG | RfLo RfHi (ohm) | shouldTrip | weight
% PHYSICS: the transformer is Y (ungrounded) / Delta, and the internal fault blocks sit on the 11 kV
% DELTA terminals. A single-line-to-ground fault returns only through the grounded-Y LOAD neutral, so its
% current grows with load: ~invisible at the July data's fixed 3 % load (all 'B-G' traces were identical),
% but 0.55 pu at 61 % load in the 2026-10-19 self-test. Load-dependent detectability is realistic; faults
% below --min-fault-pu are dropped (and counted) by the training step.
rows = {
 'Normal'               'Normal'   'normal'          0 0 0 0  0     0     false 14
 'Inrush_NoLoad'        'Inrush'   'inrush_noload'   0 0 0 0  0     0     false  7
 'Inrush_Loaded'        'Inrush'   'inrush_loaded'   0 0 0 0  0     0     false  5
 'Internal_AG'          'Internal' 'internal'        1 0 0 1  0.01  2     true   3
 'Internal_BG'          'Internal' 'internal'        0 1 0 1  0.01  2     true   2
 'Internal_CG'          'Internal' 'internal'        0 0 1 1  0.01  2     true   2
 'Internal_ABG'         'Internal' 'internal'        1 1 0 1  0.01  2     true   3
 'Internal_BCG'         'Internal' 'internal'        0 1 1 1  0.01  2     true   3
 'Internal_ACG'         'Internal' 'internal'        1 0 1 1  0.01  2     true   3
 'Internal_AB'          'Internal' 'internal'        1 1 0 0  0.01  2     true   4
 'Internal_BC'          'Internal' 'internal'        0 1 1 0  0.01  2     true   4
 'Internal_AC'          'Internal' 'internal'        1 0 1 0  0.01  2     true   4
 'Internal_ABC'         'Internal' 'internal'        1 1 1 0  0.01  2     true   5
 'Internal_ABCG'        'Internal' 'internal'        1 1 1 1  0.01  2     true   3
 'Internal_HiZ_AB'      'Internal' 'internal'        1 1 0 0  1     25    true   3
 'Internal_HiZ_BC'      'Internal' 'internal'        0 1 1 0  1     25    true   3
 'Internal_HiZ_AC'      'Internal' 'internal'        1 0 1 0  1     25    true   3
 'Internal_HiZ_ABC'     'Internal' 'internal'        1 1 1 0  1     25    true   3
 'Internal_HiZ_AG'      'Internal' 'internal'        1 0 0 1  1     25    true   2
 'Internal_Evolving'    'Internal' 'evolving'        1 1 0 0  0.01  0.5   true   4
 'Internal_SOTF_AB'     'Internal' 'sotf'            1 1 0 0  0.01  2     true   2
 'Internal_SOTF_ABC'    'Internal' 'sotf'            1 1 1 0  0.01  2     true   2
 'External_AG'          'External' 'external'        1 0 0 1  0.01  5     false  3
 'External_BG'          'External' 'external'        0 1 0 1  0.01  5     false  2
 'External_CG'          'External' 'external'        0 0 1 1  0.01  5     false  2
 'External_ABG'         'External' 'external'        1 1 0 1  0.01  5     false  5
 'External_BCG'         'External' 'external'        0 1 1 1  0.01  5     false  4
 'External_ACG'         'External' 'external'        1 0 1 1  0.01  5     false  4
 'External_AB'          'External' 'external'        1 1 0 0  0.01  5     false  6
 'External_BC'          'External' 'external'        0 1 1 0  0.01  5     false  4
 'External_ABC'         'External' 'external'        1 1 1 0  0.01  5     false 10
 'External_ABCG'        'External' 'external'        1 1 1 1  0.01  5     false  8
 'External_HiZ_AB'      'External' 'external'        1 1 0 0  1     25    false  3
 'External_HiZ_ABC'     'External' 'external'        1 1 1 0  1     25    false  3
 'Stress_FaultInInrush' 'Internal' 'fault_in_inrush' 1 1 0 1  0.01  1     true   4
 'Stress_ExtInInrush'   'Inrush'   'ext_in_inrush'   1 1 0 0  0.01  5     false  4
 'Stress_CTSat_Int'     'Internal' 'ct_stress_int'   1 1 1 0  0.01  0.1   true   3
 'Stress_ExtCTSat'      'External' 'ct_stress_ext'   1 1 1 0  0.001 0.05  false  6
};
f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';
for i = 1:numel(ST)
    t = ''; L = 'ABCG'; v = [ST(i).fA ST(i).fB ST(i).fC ST(i).fG];
    for q = 1:4, if v(q), t = [t L(q)]; end, end %#ok<AGROW>
    if isempty(t), t = 'None'; end
    ST(i).faultTag = t;
end
end

function p = drawParameters(sc, seed)
rng(seed, 'twister');
stress = startsWith(sc.kind, 'ct_stress');
p.loadPu = 0.05 + 1.15 * rand();                       % 5-120 % of 300 MVA
if stress, p.loadPu = 0.6 + 0.6 * rand(); end
p.pf = 0.85 + 0.15 * rand();
p.srcScale = 0.95 + 0.10 * rand();
p.srcPhase = 360 * rand();
lo = 0.05; hi = 1.0;                                   % noise, % of rated CT secondary current
if stress, lo = 1; hi = 3; end
p.noisePct = 10 ^ (log10(lo) + (log10(hi) - log10(lo)) * rand());
mm = 0.02; if stress, mm = 0.05; end
p.ctGain = 1 + (2 * rand(1, 6) - 1) * mm;
p.noiseSeeds = randi([1 2^31 - 2], 1, 6);
flux = -0.8 + 1.6 * rand(1, 2);
p.residualFlux = [flux, -sum(flux)];
if sc.RfHi > sc.RfLo
    p.Rf = 10 ^ (log10(sc.RfLo) + (log10(sc.RfHi) - log10(sc.RfLo)) * rand());
else
    p.Rf = sc.RfLo;
end
p.tEnergise = 0; p.tFault = NaN; p.tFault2 = NaN;
switch sc.kind
    case {'internal', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();
    case 'evolving'
        p.tFault = 0.30 + 0.35 * rand();
        p.tFault2 = p.tFault + 0.02 + 0.08 * rand();
    case {'inrush_noload', 'inrush_loaded'}
        p.tEnergise = 0.10 + 0.60 * rand();
    case 'sotf'
        p.tEnergise = 0.20 + 0.50 * rand();
        p.tFault = p.tEnergise;                        % fault already present when energised
    case {'fault_in_inrush', 'ext_in_inrush'}
        p.tEnergise = 0.10 + 0.40 * rand();
        p.tFault = p.tEnergise + 0.02 + 0.28 * rand();
end
if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
if strcmp(sc.kind, 'normal'), p.tEvent = NaN; end
p.inceptionAngle = mod(p.srcPhase + 360 * 50 * max(p.tEvent, 0), 360);
end

% =====================================================================================
% Model configuration (every write is read back)
% =====================================================================================
function B = locateBlocks(model)
B.model = model;
B.hv    = findBlock(model, 'Three-Phase Breaker');
B.lv    = findBlock(model, 'Three-Phase Breaker1');
B.load  = findBlock(model, 'Three-Phase Series RLC Load');
B.xf    = findBlock(model, 'Step_down_Transformer');
B.vs    = {findBlock(model, 'VSa'), findBlock(model, 'VSb'), findBlock(model, 'VSc')};
B.fault = struct('blk', {findBlock(model, 'Internal_Fault1'), findBlock(model, 'Internal_Fault2'), ...
                         findBlock(model, 'Internal_Fault3'), findBlock(model, 'External_Fault')}, ...
                 'step', {findBlock(model, 'Step3'), findBlock(model, 'Step_Evolve2'), ...
                          findBlock(model, 'Step_Evolve3'), findBlock(model, 'Step4')});
B.nmu   = findBlock(model, 'Noise Merging Unit');
B.blwn  = findBlock(B.nmu, 'Band-Limited White Noise');
for k = 1:6
    B.noiseGain{k} = findBlock(B.nmu, sprintf('Noise_Gain_%d', k));
    B.ctGain{k}    = findBlock(B.nmu, sprintf('CT_Gain_Mismatch_%d', k));
end
B.relay = findBlock(model, 'Hybrid 87T Relay');
end

function blk = findBlock(parent, name)
% Exact block under `parent` (one level), comparing names with whitespace/newlines normalised.
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
normName = @(s) strtrim(regexprep(s, '\s+', ' '));
hit = c(strcmp(cellfun(@(s) normName(get_param(s, 'Name')), c, 'UniformOutput', false), normName(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'GenV2:Block', 'Expected exactly one block "%s" under %s, found %d.', name, parent, numel(hit));
blk = hit{1};
end

function setp(blk, varargin)
% set_param + read-back. Any mismatch stops the run instead of being silently ignored.
set_param(blk, varargin{:});
for k = 1:2:numel(varargin)
    want = strtrim(varargin{k + 1}); got = strtrim(get_param(blk, varargin{k}));
    if ~strcmp(want, got)
        a = parseNums(want); b = parseNums(got);       % numeric compare without eval
        assert(~isempty(a) && isequal(size(a), size(b)) && all(abs(a(:) - b(:)) <= 1e-9 * max(1, abs(a(:)))), ...
            'GenV2:SetParam', '%s: %s should be "%s" but is "%s".', blk, varargin{k}, want, got);
    end
end
end

function finishGeneration(model)
if isappdata(0, 'HybridRelaySkipLSTM'), rmappdata(0, 'HybridRelaySkipLSTM'); end
if bdIsLoaded(model), close_system(model, 0); end
end

function v = parseNums(s)
% Numbers in a parameter string such as '[0.1 0.2]' or '1e-3'; [] if it is not purely numeric.
t = strtrim(regexprep(s, '[\[\],;]', ' '));
if isempty(t) || ~isempty(regexp(t, '[^0-9eE+\-\.\s]', 'once')), v = []; return; end
v = sscanf(t, '%f');
end

function prepareModelForGeneration(B)
% In-memory only (the model is closed without saving at the end).
% 1) Breakers no longer follow the relay trip output: generated traces must not be cut by a relay decision.
%    External must be switched off TOGETHER with valid SwitchTimes: with External off the breaker mask
%    reads SwitchTimes(1), so an empty '[]' makes mask initialisation fail (the old generator's hidden bug).
setp(B.hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(B.lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
% 2) The LSTM is not needed (features are computed offline from the logged currents). Commenting blocks
%    out leaves downstream signal sizes undefined ("underspecified signal dimensions"), so instead the
%    model stays wired as-is and lstm_predict_wrapper.m returns 0 at once while this flag is set.
%    The flag is removed again on exit (see the onCleanup in the main function).
setappdata(0, 'HybridRelaySkipLSTM', true);
% Quiet, harmless diagnostics (algebraic loop in the CT/transformer models, the unused Manual Switch,
% breaker inputs no longer wired to the relay) would add ~30 lines per simulation to the log.
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}
    try
        set_param(B.model, m{1}, 'none');
    catch ME
        warning('GenV2:Diag', 'Could not set %s (%s); the log will just be longer.', m{1}, ME.message);
    end
end
% 3) Six INDEPENDENT noise channels: BLWN with a 6-element seed -> Demux -> Noise_Gain_1..6.
dm = [B.nmu '/Noise_Demux'];
if getSimulinkBlockHandle(dm) == -1
    ph = get_param(B.blwn, 'PortHandles');
    ln = get_param(ph.Outport(1), 'Line');
    if ln ~= -1, delete_line(ln); end
    pos = get_param(B.blwn, 'Position');
    add_block('simulink/Signal Routing/Demux', dm, 'Outputs', '6', 'Position', pos + [60 0 70 40]);
    dph = get_param(dm, 'PortHandles');
    add_line(B.nmu, ph.Outport(1), dph.Inport(1), 'autorouting', 'on');
    for k = 1:6
        gph = get_param(B.noiseGain{k}, 'PortHandles');
        add_line(B.nmu, dph.Outport(k), gph.Inport(1), 'autorouting', 'on');
    end
end
setp(B.blwn, 'Cov', mat2str(0.1 * ones(1, 6)), 'seed', mat2str(1:6));   % set together: sizes must match
% 4) Log the relay's Yd1-compensated per-unit differential (for the detectability measure faultDiffPu).
dph = get_param(findBlock(B.relay, 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');
end

function applyScenario(B, sc, p, cfg)
% --- faults: everything off, every step far in the future
for f = B.fault
    setp(f.blk, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');
    setp(f.step, 'Time', '10', 'Before', '0', 'After', '1');
end

switch sc.kind
    case 'normal'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
    case {'internal', 'ct_stress_int'}
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case {'external', 'ct_stress_ext'}
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 4, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case 'evolving'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 1, [1 1 0 0], p.Rf, p.tFault);     % A-B first ...
        armFault(B, 2, [0 1 1 0], p.Rf, p.tFault2);    % ... then B-C joins -> A-B-C (visible from the start;
                                                        %     an A-G start would be invisible on the delta side)
    case {'inrush_noload', 'inrush_loaded'}
        breakersEnergise(B, p.tEnergise, strcmp(sc.kind, 'inrush_loaded'));
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
    case 'sotf'
        breakersEnergise(B, p.tEnergise, true);
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, max(p.tEnergise - 0.05, 0.01));   % fault present before closing
    case 'fault_in_inrush'
        breakersEnergise(B, p.tEnergise, true);
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case 'ext_in_inrush'
        breakersEnergise(B, p.tEnergise, true);
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
        armFault(B, 4, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    otherwise
        error('GenV2:Kind', 'Unknown scenario kind %s', sc.kind);
end

% --- load (constant-Z, rated 11 kV) and source
S = p.loadPu * cfg.Srated;
setp(B.load, 'ActivePower', sprintf('%.6g', S * p.pf), ...
             'InductivePower', sprintf('%.6g', max(S * sqrt(max(1 - p.pf ^ 2, 0)), 1)), 'CapacitivePower', '0');
amp = sprintf('%.6g', p.srcScale * 230e3 * sqrt(2) / sqrt(3));
ph0 = [0 -120 120];
for k = 1:3
    setp(B.vs{k}, 'Amplitude', amp, 'Phase', sprintf('%.6g', p.srcPhase + ph0(k)));
end

% --- noise and CT mismatch (noise std = noisePct % of each channel's rated secondary current)
setp(B.blwn, 'seed', mat2str(p.noiseSeeds));
for k = 1:6
    sigma = p.noisePct / 100 * cfg.Inom(k);
    setp(B.noiseGain{k}, 'Gain', sprintf('%.8g', sigma / cfg.blwnStd));
    setp(B.ctGain{k}, 'Gain', sprintf('%.8g', p.ctGain(k)));
end
end

function armFault(B, i, phases, Rf, t)
oo = {'off', 'on'};
setp(B.fault(i).blk, 'FaultA', oo{phases(1) + 1}, 'FaultB', oo{phases(2) + 1}, 'FaultC', oo{phases(3) + 1}, ...
    'GroundFault', oo{phases(4) + 1}, 'FaultResistance', sprintf('%.6g', Rf));
setp(B.fault(i).step, 'Time', sprintf('%.6f', t));
end

function breakersClosed(B)
% '[10 11]' = no switching inside the 1.1 s run. ('[]' made set_param fail in the old generator.)
setp(B.hv, 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(B.lv, 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
end

function breakersEnergise(B, t, loaded)
setp(B.hv, 'InitialState', 'open', 'SwitchTimes', sprintf('[%.6f 11]', t));
if loaded
    setp(B.lv, 'InitialState', 'open', 'SwitchTimes', sprintf('[%.6f 11]', t));
else
    setp(B.lv, 'InitialState', 'open', 'SwitchTimes', '[10 11]');     % LV stays open: no-load energisation
end
end

% =====================================================================================
% Simulation + waveform checks
% =====================================================================================
function [rec, status] = simulateAndCheck(model, B, sc, p, cfg, fingerprints)
rec = struct('Ip', [], 'Is', [], 'eventDetected', NaN, 'energiseDetected', NaN, 'timingOK', 0, 'eventVisible', NaN, ...
             'noiseMeasured', NaN, 'noiseExpected', NaN, 'noiseOK', NaN, 'duplicate', 0, ...
             'faultDiffPu', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');
try
    out = sim(model, 'StopTime', sprintf('%.4f', cfg.stopTime), 'ReturnWorkspaceOutputs', 'on');
catch ME
    status = 'ERR'; rec.message = ME.message; return;
end
Ip = getArray(out, 'I_primary_abc'); Is = getArray(out, 'I_secondary_abc');
nExp = round(cfg.stopTime * cfg.fs) + 1;
if ~isequal(size(Ip), [nExp 3]) || ~isequal(size(Is), [nExp 3])
    status = 'ERR'; rec.message = sprintf('logged size %s / %s, expected [%d 3]', mat2str(size(Ip)), mat2str(size(Is)), nExp);
    return;
end
rec.Ip = Ip; rec.Is = Is;
fs = cfg.fs; t = (0:nExp - 1)' / fs;

% energisation: first sample where |Ip| clearly exceeds noise + quantisation (6 sigma + 1 % of rated)
sigHV = p.noisePct / 100 * cfg.Inom(1);
thr = 6 * sqrt(sigHV ^ 2 + cfg.quantStep ^ 2 / 12) + cfg.quantStep + 0.01 * cfg.Inom(1);
k = find(max(abs(Ip), [], 2) > thr, 1);
if isempty(k), rec.energiseDetected = NaN; else, rec.energiseDetected = (k - 1) / fs; end

% event (fault / energisation): first sample where the cycle-difference of Ip - Is jumps
d = Ip - Is;
cdiff = [zeros(32, 1); max(abs(d(33:end, :) - d(1:end - 32, :)), [], 2)];
% timingOK: 1 = event seen at the intended time, 0 = WRONG time (generation bug),
%           NaN = event too small to see in Ip - Is (e.g. high-impedance fault): not a generation error.
if isnan(p.tEvent)
    rec.timingOK = 1;                                            % Normal: nothing to time
else
    % reference level: the 2 cycles just before the event (after any energisation transient)
    t1 = p.tEvent - 0.045;
    if p.tEnergise > 0 && p.tEvent > p.tEnergise, t1 = max(t1, p.tEnergise + 0.015); end
    pre = cdiff(t >= t1 & t <= p.tEvent - 0.005);
    base = 0; if ~isempty(pre), s = sort(pre); base = s(ceil(0.995 * numel(s))); end
    win = t >= p.tEvent - 0.02 & t <= p.tEvent + 0.04;
    peak = max(cdiff(win));
    rec.eventVisible = double(peak > 3 * base && peak > 1e-3);
    if rec.eventVisible
        j = find(win & cdiff > base + 0.5 * (peak - base), 1);
        rec.eventDetected = t(j);
        rec.timingOK = double(abs(rec.eventDetected - p.tEvent) <= cfg.timingTol);
    else
        rec.timingOK = NaN;
    end
end
% Energisation time must ALWAYS match: this is what caught the stuck-breaker bug.
if strcmp(sc.kind, 'inrush_noload') && isnan(rec.energiseDetected)
    energiseOK = true;                                           % tiny inrush (favourable flux): unverifiable, not an error
    rec.eventVisible = 0; rec.timingOK = NaN;
elseif startsWith(sc.kind, 'inrush') || any(strcmp(sc.kind, {'sotf', 'fault_in_inrush', 'ext_in_inrush'}))
    energiseOK = abs(rec.energiseDetected - p.tEnergise) <= cfg.timingTol;
else
    energiseOK = rec.energiseDetected <= 0.03;                   % energised from the start
end
if ~energiseOK, rec.timingOK = 0; end

% noise: std of the cycle-difference on a healthy stretch vs the expected value
healthy = t > 0.12 & t < 0.28;
if strcmp(sc.kind, 'normal'), healthy = t > 0.12 & t < 1.0; end
if startsWith(sc.kind, 'inrush') || any(strcmp(sc.kind, {'sotf', 'fault_in_inrush', 'ext_in_inrush'})), healthy = false(size(t)); end
if any(healthy)
    q2 = cfg.quantStep ^ 2 / 12;                                  % quantisation noise per channel
    sp = p.noisePct / 100 * cfg.Inom(1:3); ss = p.noisePct / 100 * cfg.Inom(4:6);
    rec.noiseExpected = median(sqrt(2 * (sp .^ 2 + ss .^ 2 + 2 * q2)));
    seg = d(healthy, :); seg32 = seg(33:end, :) - seg(1:end - 32, :);
    rec.noiseMeasured = median(std(seg32));
    rec.noiseOK = double(rec.noiseMeasured > 0.5 * rec.noiseExpected && rec.noiseMeasured < 2 * rec.noiseExpected + 0.01);
end

% detectability: rise of the relay's compensated differential (per unit) one cycle after the event
try
    el = out.get('logsout').get('I_diff_comp');
    tc = el.Values.Time; dc = squeeze(double(el.Values.Data));
    if size(dc, 2) ~= 3, dc = dc.'; end
    if ~isnan(p.tFault)
        rmsWin = @(t1, t2) sqrt(mean(dc(tc >= t1 & tc < t2, :) .^ 2, 1));
        rec.faultDiffPu = max(rmsWin(p.tFault + 0.04, p.tFault + 0.06) - rmsWin(p.tFault - 0.03, p.tFault - 0.01));
    end
catch
end

% duplicate waveform?
md = java.security.MessageDigest.getInstance('SHA-1');
md.update(typecast([Ip(:); Is(:)], 'int8'));
rec.fingerprint = lower(reshape(dec2hex(typecast(md.digest(), 'uint8'))', 1, []));
rec.duplicate = double(fingerprints.isKey(rec.fingerprint));

rec.checkPassed = double(rec.timingOK ~= 0 && rec.duplicate == 0 && rec.noiseOK ~= 0);   % NaN counts as not-failed
status = 'OK'; if ~rec.checkPassed, status = 'CHK'; end
end

function x = getArray(out, name)
v = out.get(name);
if isa(v, 'timeseries'), x = double(v.Data);
elseif isstruct(v), x = double(v.signals.values);
else, x = double(v); end
end

% =====================================================================================
% Storage
% =====================================================================================
function D = preallocate(N)
D = struct();
for f = {'zone', 'faultType', 'scenarioName', 'scenarioKind', 'simulationStatus', 'primaryCurrent', ...
         'secondaryCurrent', 'fingerprint', 'checkMessage'}
    D.(f{1}) = cell(1, N);
end
D.shouldTrip = zeros(1, N, 'uint8');
for f = {'inceptionTime', 'energisationTime', 'faultTime2', 'faultResistance', 'inceptionAngle', 'noiseLevel', ...
         'noisePct', 'loadPu', 'powerFactor', 'sourceScale', 'sourcePhaseDeg', 'ctMismatchMaxPct', 'sampleSeed', ...
         'eventDetected', 'energiseDetected', 'timingOK', 'eventVisible', 'noiseMeasured', 'noiseExpected', ...
         'noiseOK', 'duplicate', 'faultDiffPu', 'checkPassed'}
    D.(f{1}) = nan(1, N);
end
end

function D = store(D, i, sc, p, rec, status)
D.zone{i} = sc.zone; D.faultType{i} = sc.faultTag; D.scenarioName{i} = sc.name; D.scenarioKind{i} = sc.kind;
D.simulationStatus{i} = ifelse(strcmp(status, 'ERR'), ['Failed: ' rec.message], 'Success');
D.primaryCurrent{i} = rec.Ip; D.secondaryCurrent{i} = rec.Is;
D.fingerprint{i} = rec.fingerprint; D.checkMessage{i} = rec.message;
D.shouldTrip(i) = uint8(sc.shouldTrip);
D.inceptionTime(i) = p.tFault;          % NaN when there is no fault (Normal, inrush)
D.energisationTime(i) = p.tEnergise;
D.faultTime2(i) = p.tFault2;
D.faultResistance(i) = p.Rf; D.inceptionAngle(i) = p.inceptionAngle;
D.noiseLevel(i) = p.noisePct / 100; D.noisePct(i) = p.noisePct;
D.loadPu(i) = p.loadPu; D.powerFactor(i) = p.pf; D.sourceScale(i) = p.srcScale; D.sourcePhaseDeg(i) = p.srcPhase;
D.ctMismatchMaxPct(i) = 100 * max(abs(p.ctGain - 1)); D.sampleSeed(i) = p.sampleSeed;
for f = {'eventDetected', 'energiseDetected', 'timingOK', 'eventVisible', 'noiseMeasured', 'noiseExpected', ...
         'noiseOK', 'duplicate', 'faultDiffPu', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});
end
end

function f = partialFile(dir, runId)
f = fullfile(dir, sprintf('StressDataset_v2_%s_PARTIAL.mat', runId));
end

% =====================================================================================
% Self-test: 5 cases, prints the checks, saves nothing
% =====================================================================================
function runSelfTest(model, B, ST, cfg)
names = {'Normal', 'Internal_AB', 'Internal_HiZ_AB', 'Internal_AG', 'Inrush_NoLoad', 'External_ABC', 'Internal_SOTF_AB'};
fprintf('\n=== SELF-TEST (nothing is saved) ===\n');
fprintf('Expect: AB / HiZ_AB / SOTF visible and timed; Internal_AG on the delta winding: visible 0, faultDiff ~0.\n');
fp = containers.Map('KeyType', 'char', 'ValueType', 'double');
allOK = true;
for i = 1:numel(names)
    sc = ST(strcmp({ST.name}, names{i}));
    p = drawParameters(sc, cfg.seed + 900000 + i); p.sampleSeed = cfg.seed + 900000 + i;
    applyScenario(B, sc, p, cfg);
    [rec, status] = simulateAndCheck(model, B, sc, p, cfg, fp);
    if ~isempty(rec.fingerprint), fp(rec.fingerprint) = i; end
    fprintf('%-17s %-3s | load %3.0f%% | event %s det %s visible %g | energised %s | noise %.4f/%.4f A | faultDiff %.3f pu | %s\n', ...
        names{i}, status, 100 * p.loadPu, fmtT(p.tEvent), fmtT(rec.eventDetected), rec.eventVisible, ...
        fmtT(rec.energiseDetected), rec.noiseMeasured, rec.noiseExpected, rec.faultDiffPu, checkText(rec));
    allOK = allOK && rec.checkPassed == 1;
end
if allOK
    fprintf('SELF-TEST PASSED. Run: generate_stress_dataset_v2(1200)\n');
else
    fprintf('SELF-TEST: some checks failed. Send this output to Claude before generating.\n');
end
end

% =====================================================================================
function s = fmtT(t)
if isnan(t), s = '-'; else, s = sprintf('%.3fs', t); end
end

function s = checkText(rec)
if rec.checkPassed, s = 'checks OK'; return; end
parts = {};
if rec.timingOK == 0, parts{end + 1} = 'TIMING'; end
if rec.duplicate == 1, parts{end + 1} = 'DUPLICATE'; end
if rec.noiseOK == 0, parts{end + 1} = 'NOISE'; end
if ~isempty(rec.message), parts{end + 1} = rec.message; end
s = ['FAILED: ' strjoin(parts, ', ')];
end

function v = ifelse(c, a, b)
if c, v = a; else, v = b; end
end
