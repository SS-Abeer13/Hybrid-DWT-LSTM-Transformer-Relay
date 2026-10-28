function outFile = generate_stress_dataset_plant_b(nSamples, varargin)
%GENERATE_STRESS_DATASET_PLANT_B Stress dataset on TransformerB_v4 (Plant B: 40 MVA, 132/33 kV, Dyn11, 1 A secondaries).
%
%   generate_stress_dataset_plant_b('selftest')        % quick cases, prints the checks, saves nothing
%   outFile = generate_stress_dataset_plant_b(1200)    % main set -> ONE file datasets\StressDataset_PlantB_<run>.mat
%   generate_stress_dataset_plant_b(150, 'Set', 'OOD') % out-of-distribution set -> StressDataset_PlantBOOD_<run>.mat
%
% OPTIONS (name, value pairs)
%   'Run'     run id. If datasets\StressDataset_PlantB*_<run>_PARTIAL.mat exists the run RESUMES from it.
%   'Resume'  alias of 'Run'.
%   'Chunk'   stop cleanly after this many simulations in THIS MATLAB process (0 = never).
%   'Set'     'main' (default) | 'OOD' (out-of-distribution ranges; default seed 20261022).
%   'Only'    char or cellstr of scenario names, kinds or zones to generate (default: all).
%   'Seed'    base seed (default 20261021; sample k uses rng(seed + k)).
%   'StopTime' simulation length in seconds (default 1.10).
%   'OverexcMin' lower bound (pu) of over-excitation source voltage (default 1.15).
%   'Indices' closedloop only: trace numbers to re-run with LSTM active; empty = 12 cases.
%   'Tag'     closedloop only: suffix of result files (default 'plant_b').
%   'Range'   self-test only: [first last] case numbers.

warning('off', 'all');
model = 'TransformerB_v4';
thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);
datasetsDir = fullfile(projectDir, 'datasets');

selfTest = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'selftest');
closedLoop = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'closedloop');
if nargin < 1 || isempty(nSamples) || selfTest || closedLoop, nSamplesNum = 1200; else, nSamplesNum = nSamples; end
opts = struct('Resume', '', 'Run', '', 'Seed', 20261021, 'StopTime', 1.10, 'Chunk', 0, 'Set', 'main', 'Only', {{}}, 'Range', [], 'OverexcMin', 1.15, 'Indices', [], 'Tag', 'plant_b');
for k = 1:2:numel(varargin)
    assert(isfield(opts, varargin{k}), 'GenPlantB:Option', 'Unknown option "%s".', varargin{k});
    opts.(varargin{k}) = varargin{k + 1};
end
seedGiven = any(strcmp(varargin(1:2:end), 'Seed'));
if ~isempty(opts.Resume) && isempty(opts.Run), opts.Run = opts.Resume; end
opts.Set = char(opts.Set);
assert(any(strcmp(opts.Set, {'main', 'OOD'})), 'GenPlantB:Option', 'Set must be main or OOD.');
if ischar(opts.Only) || isstring(opts.Only), opts.Only = cellstr(opts.Only); end
if ~seedGiven
    if strcmp(opts.Set, 'OOD'), opts.Seed = 20261022; end
    if ~isempty(opts.Only), opts.Seed = opts.Seed + 500000 + sum(double([opts.Only{:}])); end
end
fileTag = ''; if strcmp(opts.Set, 'OOD'), fileTag = 'OOD'; elseif ~isempty(opts.Only), fileTag = 'Only'; end

cfg = struct();
cfg.version   = 'plant_b-v4-2026-10-27-pub';
cfg.fs        = 1600;
cfg.stopTime  = opts.StopTime;
cfg.set       = opts.Set;
cfg.oeMin     = opts.OverexcMin;
cfg.only      = strjoin(opts.Only, ',');
cfg.seed      = opts.Seed;
cfg.Srated    = 40e6;                  % Plant B: 40 MVA
cfg.Vhv       = 132e3;                 % Plant B: 132 kV
cfg.Vlv       = 33e3;                  % Plant B: 33 kV
cfg.Inom      = 0.8232 * ones(1, 6);   % rated CT secondary current (A): HV x3, LV x3 (probe_ct_truth_plant_b.m)
cfg.ctRatio   = [202.0119 808.8849];   % effective CT ratios HV / LV
cfg.nominalBurden = 2.5;               % nominal CT burden resistor: 2.5 ohms
cfg.loadTolPct = 10;
cfg.timingTol = 0.0125;

% Load calibration for Plant B
calMat = load(fullfile(thisDir, 'load_calibration_plant_b.mat'));
cfg.loadCal = struct('pf', calMat.pfs, 'knob', calMat.knobs, 'pctRated', calMat.pctRated);

% ---------------------------------------------------------------- model, in memory only
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on')
    error('GenPlantB:Dirty', ['%s is open with UNSAVED changes. Save or close it first: this generator ' ...
        'changes the model in memory and closes it WITHOUT saving.'], model);
end
load_system(fullfile(thisDir, [model '.slx']));
cleanup = onCleanup(@() finishGeneration(model));  %#ok<NASGU>

B = locateBlocks(model);
prepareModelForGeneration(B);
cfg.srcZ0 = [str2double(get_param(B.srcZ, 'Resistance')), str2double(get_param(B.srcZ, 'Inductance'))];
assert(abs(cfg.srcZ0(1) - 0.46) < 1e-3 && abs(cfg.srcZ0(2) - 0.0221) < 1e-4, 'GenPlantB:SrcZ', ...
    'unexpected source impedance %s / %s', get_param(B.srcZ, 'Resistance'), get_param(B.srcZ, 'Inductance'));
cfg.hizBins = jsondecode(fileread(fullfile(thisDir, 'hiz_bins.json')));
cfg.blwnStd = sqrt(0.1 / str2double(get_param(B.blwn, 'Ts')));
cfg.quantStep = str2double(get_param(findBlock(B.nmu, 'Quantizer'), 'QuantizationInterval'));
ST = scenarioTable();

if selfTest
    runSelfTest(model, B, ST, cfg, opts.Range);
    outFile = '';
    return;
end
if closedLoop && isempty(opts.Indices)
    runClosedLoop(model, B, closedLoopCases(ST, cfg), cfg, thisDir, opts.Tag);
    outFile = '';
    return;
end

% ---------------------------------------------------------------- plan / resume
if ~isempty(opts.Only)
    keep = ismember({ST.name}, opts.Only) | ismember({ST.kind}, opts.Only) | ismember({ST.zone}, opts.Only);
    assert(any(keep), 'GenPlantB:Only', 'Only = {%s} matches no scenario name, kind or zone.', strjoin(opts.Only, ', '));
    ST = ST(keep);
end
weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
counts(1) = counts(1) + (nSamplesNum - sum(counts));
N = sum(counts);
plan = repelem(1:numel(ST), counts);
blockOf = zeros(1, N);
if strcmp(opts.Set, 'OOD')
    [plan, blockOf, counts, ST] = oodPlan(ST);          % 5 blocks x 30 traces = 150 traces
    N = numel(plan);
end
firstOf = [1, cumsum(counts(1:end - 1)) + 1];

if closedLoop
    L = struct('name', {}, 'sc', {}, 'p', {}, 'expectTrip', {}, 'tRef', {});
    for idx = opts.Indices(:).'
        sc = ST(plan(idx));
        within = idx - firstOf(plan(idx)) + 1;
        if strcmp(opts.Set, 'OOD'), within = 0; end
        p = drawParameters(sc, cfg.seed + idx, makeCtx(cfg, sc, within, counts(plan(idx)), blockOf(idx)));
        p.sampleSeed = cfg.seed + idx;
        tref = p.tFault; if isnan(tref), tref = p.tEnergise; end
        L(end + 1) = struct('name', sprintf('%s #%d', sc.name, idx), 'sc', sc, 'p', p, 'expectTrip', logical(sc.shouldTrip), 'tRef', tref); %#ok<AGROW>
    end
    runClosedLoop(model, B, L, cfg, thisDir, opts.Tag);
    outFile = '';
    return;
end

if isempty(opts.Run)
    runId = datestr(now, 'yyyymmdd_HHMMSS'); %#ok<TNOW1,DATST>
else
    runId = opts.Run;
end
finalFile = fullfile(datasetsDir, sprintf('StressDataset_PlantB%s_%s.mat', fileTag, runId));
if isfile(finalFile)
    fprintf('Run %s is already finished: %s\n', runId, finalFile);
    outFile = finalFile;
    return;
end
if ~isfile(partialFile(datasetsDir, fileTag, runId))
    dataset = preallocate(N);
    startAt = 1;
else
    P = load(partialFile(datasetsDir, fileTag, runId));
    assert(isequal(P.generationConfig.seed, cfg.seed) && P.generationConfig.N == N, ...
        'GenPlantB:Resume', 'Resume file was made with a different seed or sample count.');
    dataset = P.dataset;
    startAt = find(cellfun(@isempty, dataset.simulationStatus), 1);
    if isempty(startAt), startAt = N + 1; end
end
cfg.N = N; cfg.runId = runId;

fprintf('=== Stress dataset Plant B | set %s | run %s | %d samples | %d scenarios | start at %d | chunk %d ===\n', opts.Set, runId, N, numel(ST), startAt, opts.Chunk);
for i = 1:numel(ST), fprintf('  %-26s %4d\n', ST(i).name, counts(i)); end

fingerprints = containers.Map('KeyType', 'char', 'ValueType', 'double');
for j = 1:startAt - 1
    if ~isempty(dataset.fingerprint{j}), fingerprints(dataset.fingerprint{j}) = j; end
end

t0 = tic;
for idx = startAt:N
    sc = ST(plan(idx));
    within = idx - firstOf(plan(idx)) + 1;
    if strcmp(opts.Set, 'OOD'), within = 0; end
    p = drawParameters(sc, cfg.seed + idx, makeCtx(cfg, sc, within, counts(plan(idx)), blockOf(idx)));
    p.sampleSeed = cfg.seed + idx;
    applyScenario(B, sc, p, cfg);
    [rec, status] = simulateAndCheck(model, B, sc, p, cfg, fingerprints);
    dataset = store(dataset, idx, sc, p, rec, status);
    if ~isempty(rec.fingerprint) && ~fingerprints.isKey(rec.fingerprint)
        fingerprints(rec.fingerprint) = idx;
    end

    el = toc(t0); done = idx - startAt + 1;
    fprintf('[%4d/%4d] %-26s %-4s | load %4.0f%% (real %4.0f%%) pf %.2f noise %.2f%% burden %.1fx CTerr %3.0f%% | event %6s det %6s | %s | ETA %.0f min\n', ...
        idx, N, sc.name, status, 100 * p.loadPu, rec.loadRealisedPct, p.pf, p.noisePct, p.ctBurden, rec.ctRatioErrorMax, fmtT(p.tEvent), fmtT(rec.eventDetected), ...
        checkText(rec), el / done * (N - idx) / 60);

    if mod(idx, 25) == 0
        generationConfig = cfg; scenarioTableOut = ST;
        save(partialFile(datasetsDir, fileTag, runId), 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
    end
    if opts.Chunk > 0 && done >= opts.Chunk && idx < N
        generationConfig = cfg; scenarioTableOut = ST;
        save(partialFile(datasetsDir, fileTag, runId), 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
        fprintf('CHUNK_DONE at sample %d of %d (run %s). Restart MATLAB with the same Run id to continue.\n', idx, N, runId);
        outFile = '';
        return;
    end
end

generationConfig = cfg; scenarioTableOut = ST;
outFile = finalFile;
save(outFile, 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
if isfile(partialFile(datasetsDir, fileTag, runId)), delete(partialFile(datasetsDir, fileTag, runId)); end

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
ft = {'AG' [1 0 0 1]; 'BG' [0 1 0 1]; 'CG' [0 0 1 1]; 'AB' [1 1 0 0]; 'BC' [0 1 1 0]; 'AC' [1 0 1 0]; ...
      'ABG' [1 1 0 1]; 'BCG' [0 1 1 1]; 'ACG' [1 0 1 1]; 'ABC' [1 1 1 0]; 'ABCG' [1 1 1 1]};
rows = {
 'Normal'               'Normal'   'normal'          0 0 0 0  0     0     false 303
 'Inrush_NoLoad'        'Inrush'   'inrush_noload'   0 0 0 0  0     0     false 200
 'Inrush_Loaded'        'Inrush'   'inrush_loaded'   0 0 0 0  0     0     false 120
 'Recovery_Inrush'      'Inrush'   'recovery_inrush' 1 1 1 0  0.05  0.3   false  80
 'Overexcitation'       'Overexc'  'overexc'         0 0 0 0  0     0     false 150
 'Internal_Evolving'    'Internal' 'evolving'        1 1 0 0  0.01  0.5   true   80
 'Internal_SOTF_AB'     'Internal' 'sotf'            1 1 0 0  0.01  2     true   40
 'Internal_SOTF_ABC'    'Internal' 'sotf'            1 1 1 0  0.01  2     true   40
 'External_HiZ_AB'      'External' 'external'        1 1 0 0  1     25    false  30
 'External_HiZ_ABC'     'External' 'external'        1 1 1 0  1     25    false  30
 'Stress_FaultInInrush' 'Internal' 'fault_in_inrush' 1 1 0 1  0.01  1     true  120
 'Stress_ExtInInrush'   'Inrush'   'ext_in_inrush'   1 1 0 0  0.001 0.03  false 100
};
for q = 1:size(ft, 1)
    v = ft{q, 2};
    rows(end + 1, :) = {['Internal_' ft{q, 1}],            'Internal', 'internal',      v(1), v(2), v(3), v(4), 0.01,  2,    true,  46}; %#ok<AGROW>
    rows(end + 1, :) = {['InternalHV_' ft{q, 1}],          'Internal', 'internal_hv',   v(1), v(2), v(3), v(4), 0.01,  2,    true,  18}; %#ok<AGROW>
    rows(end + 1, :) = {['External_' ft{q, 1}],            'External', 'external',      v(1), v(2), v(3), v(4), 0.001, 0.03, false, 40}; %#ok<AGROW>
    rows(end + 1, :) = {['Stress_ExtCTSat_' ft{q, 1}],     'External', 'ct_stress_ext', v(1), v(2), v(3), v(4), 0.001, 0.03, false, 22}; %#ok<AGROW>
    rows(end + 1, :) = {['Stress_CTSat_Int_' ft{q, 1}],    'Internal', 'ct_stress_int', v(1), v(2), v(3), v(4), 0.01,  0.1,  true,  11}; %#ok<AGROW>
end
hz = {'AB' [1 1 0 0]; 'BC' [0 1 1 0]; 'AC' [1 0 1 0]; 'ABC' [1 1 1 0]; 'AG' [1 0 0 1]};
for q = 1:size(hz, 1)
    v = hz{q, 2};
    rows(end + 1, :) = {['Internal_HiZ_' hz{q, 1}], 'Internal', 'internal', v(1), v(2), v(3), v(4), 1, 25, true, 48}; %#ok<AGROW>
end
f = {'name','zone','kind','fA','fB','fC','fG','RfLo','RfHi','shouldTrip','weight'};
ST = cell2struct(rows, f, 2).';
for i = 1:numel(ST)
    t = ''; L = 'ABCG'; v = [ST(i).fA ST(i).fB ST(i).fC ST(i).fG];
    for q = 1:4, if v(q), t = [t L(q)]; end, end %#ok<AGROW>
    if isempty(t), t = 'None'; end
    ST(i).faultTag = t;
end
end

function p = drawParameters(sc, seed, ctx)
rng(seed, 'twister');
stress = startsWith(sc.kind, 'ct_stress');
ood = ctx.block;
p.pf = 0.80 + 0.20 * rand();
if stress, edges = [60 85 110]; else, edges = [10 30 60 90 110]; end
K = numel(edges) - 1; lb = bin(ctx, 1, K);
loadPct = edges(lb) + diff(edges([lb lb + 1])) * rand();
p.loadBin = lb + 2 * stress;
if ood == 1, if rand() < 0.5, loadPct = 1 + 9 * rand(); p.loadBin = 0; else, loadPct = 110 + 20 * rand(); p.loadBin = 5; end, end
p.loadPu = loadPct / 100;
p.loadKnob = load_knob_for(loadPct, p.pf, ctx.loadCal);
p.srcScale = 0.95 + 0.10 * rand();

lo = 0.05; hi = 1.0; if stress, lo = 1; hi = 3; end
p.noisePct = 10 ^ (log10(lo) + (log10(hi) - log10(lo)) * rand());
mm = 0.02; if stress, mm = 0.05; end
if ood == 5, p.noisePct = 4 + 2 * rand(); mm = 0.08; end

if stress, p.ctBurden = 1 + 3 * rand(); else, p.ctBurden = 1 + 2 * rand(); end
if ood == 3, p.ctBurden = 4 + 4 * rand(); end
p.ctGain = 1 + (2 * rand(1, 6) - 1) * mm;
p.noiseSeeds = randi([1 2^31 - 2], 1, 6);

p.srcZScale = 2 ^ (2 * rand() - 1);
p.freq = 49.8 + 0.4 * rand();
if ood == 2, p.srcZScale = 3 * (0.9 + 0.2 * rand()); p.freq = 50 + sign(rand() - 0.5) * (0.5 + 0.05 * (2 * rand() - 1)); end
if ood == 2 && p.freq == 50, p.freq = 50.5; end

p.hizBin = 0;
if startsWith(sc.name, 'Internal_HiZ_')
    p.hizBin = bin(ctx, 4, 3);
    bn = ctx.hiz.(sc.name(numel('Internal_HiZ_') + 1:end)).bins;
    r = {bn.visible, bn.ai_only, bn.undetect}; r = sort(r{p.hizBin}(:)');
    p.Rf = 10 ^ (log10(r(1)) + (log10(r(2)) - log10(r(1))) * rand());
elseif sc.RfHi > sc.RfLo
    p.Rf = 10 ^ (log10(sc.RfLo) + (log10(sc.RfHi) - log10(sc.RfLo)) * rand());
else
    p.Rf = sc.RfLo;
end

p.tEnergise = 0; p.tFault = NaN; p.tFault2 = NaN; p.faultClear = NaN;
switch sc.kind
    case 'recovery_inrush'
        p.tFault = 0.30 + 0.15 * rand();
        p.faultClear = p.tFault + 0.040 + 0.060 * rand();
    case {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext'}
        p.tFault = 0.30 + 0.45 * rand();
    case 'evolving'
        p.tFault = 0.30 + 0.35 * rand();
        p.tFault2 = p.tFault + 0.02 + 0.08 * rand();
    case {'inrush_noload', 'inrush_loaded'}
        p.tEnergise = 0.10 + 0.60 * rand();
    case 'sotf'
        p.tEnergise = 0.20 + 0.50 * rand();
        p.tFault = p.tEnergise;
    case {'fault_in_inrush', 'ext_in_inrush'}
        p.tEnergise = 0.10 + 0.40 * rand();
        p.tFault = p.tEnergise + 0.02 + 0.28 * rand();
end
if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
if any(strcmp(sc.kind, {'normal', 'overexc'})), p.tEvent = NaN; end
if strcmp(sc.kind, 'recovery_inrush'), p.tEvent = p.faultClear; end

if strcmp(sc.kind, 'overexc'), p.srcScale = ctx.oeMin + (1.45 - ctx.oeMin) * rand(); if ood == 4, p.srcScale = 1.50 + 0.10 * rand(); end, end

p.angleBin = 0;
if isnan(p.tEvent)
    p.srcPhase = 360 * rand();
else
    p.angleBin = bin(ctx, 2, 5);
    if p.angleBin <= 4
        ang = 90 * (p.angleBin - 1) + 90 * rand();
    else
        ang = mod(90 * randi(2) - 90 + 20 * (rand() - 0.5), 360);
    end
    p.srcPhase = mod(ang - 360 * p.freq * p.tEvent, 360);
end

p.fluxBin = 0;
if any(strcmp(sc.kind, {'inrush_noload', 'inrush_loaded', 'sotf', 'fault_in_inrush', 'ext_in_inrush'}))
    p.fluxBin = bin(ctx, 3, 3);
    fe = [0 0.27 0.53 0.80]; target = fe([p.fluxBin p.fluxBin + 1]); if ood == 4, target = [0.85 0.95]; end
    for tries = 1:5000
        f12 = -1 + 2 * rand(1, 2); fl = [f12, -sum(f12)];
        if ood == 4, fl = [0.9, -0.45, -0.45]; fl = fl(randperm(3)) * sign(rand() - 0.5); end
        m = max(abs(fl));
        if m >= target(1) && m < target(2) && m <= 1.0, break; end
        if tries == 5000, fl = fl / max(m, eps) * mean(target); end
    end
    p.residualFlux = fl;
else
    flux = -0.8 + 1.6 * rand(1, 2); p.residualFlux = [flux, -sum(flux)];
end
p.inceptionAngle = NaN; if ~isnan(p.tEvent), p.inceptionAngle = mod(p.srcPhase + 360 * p.freq * p.tEvent, 360); end
p.oodBlock = ood;
end

function b = bin(ctx, dim, K)
if ctx.within <= 0 || ctx.n <= 0
    b = randi(K); return;
end
b = balancedBin(ctx.seed0, ctx.sid, dim, ctx.within, ctx.n, K);
end

function b = balancedBin(seed0, sid, dim, within, n, K)
rs = RandStream('twister', 'Seed', mod(seed0 * 7919 + sid * 104729 + dim * 1299709, 2 ^ 32 - 1));
perm = randperm(rs, n);
b = mod(perm(within) - 1, K) + 1;
end

function ctx = makeCtx(cfg, sc, within, n, block)
ctx = struct('oeMin', cfg.oeMin, 'hiz', cfg.hizBins, 'seed0', cfg.seed, 'within', within, 'n', n, 'block', block, ...
             'sid', sum(double(sc.name) .* (1:numel(sc.name))), 'loadCal', cfg.loadCal);
end

function [plan, blockOf, counts, ST] = oodPlan(ST)
% OOD set for Plant B: 5 blocks x 30 traces = 150 traces total
L = {
 1, {'Normal' 4; 'External_ABC' 4; 'External_AB' 4; 'Inrush_Loaded' 3}, {'Internal_AB' 4; 'Internal_ABC' 4; 'InternalHV_AB' 4; 'Internal_AG' 3}
 2, {'Normal' 5; 'External_ABC' 5; 'Inrush_Loaded' 5}, {'Internal_AB' 5; 'Internal_ABC' 5; 'InternalHV_AG' 5}
 3, {'Stress_ExtCTSat_ABC' 5; 'Stress_ExtCTSat_AB' 5; 'Stress_ExtCTSat_AG' 5}, {'Stress_CTSat_Int_AB' 5; 'Stress_CTSat_Int_ABC' 5; 'Stress_CTSat_Int_AG' 5}
 4, {'Overexcitation' 6; 'Inrush_NoLoad' 3; 'Inrush_Loaded' 3; 'Recovery_Inrush' 3}, {'Internal_AB' 5; 'Internal_SOTF_AB' 5; 'Stress_FaultInInrush' 5}
 5, {'Normal' 5; 'External_ABC' 5; 'Inrush_Loaded' 5}, {'Internal_AB' 5; 'Internal_ABC' 5; 'InternalHV_AB' 5}};
names = {ST.name}; plan = []; blockOf = [];
for r = 1:size(L, 1)
    for g = 2:3
        for q = 1:size(L{r, g}, 1)
            ix = find(strcmp(names, L{r, g}{q, 1}));
            assert(isscalar(ix), 'GenPlantB:OOD', 'OOD scenario %s not in scenario table', L{r, g}{q, 1});
            plan = [plan, repmat(ix, 1, L{r, g}{q, 2})]; %#ok<AGROW>
            blockOf = [blockOf, repmat(L{r, 1}, 1, L{r, g}{q, 2})]; %#ok<AGROW>
        end
    end
end
counts = histcounts(plan, 0.5:1:numel(ST) + 0.5);
end

function L = closedLoopCases(ST, cfg)
pick = @(n) ST(strcmp({ST.name}, n));
spec = {
 'Normal, 30 % load',                  'Normal',               30,   struct()
 'Normal, 100 % load',                 'Normal',               100,  struct()
 'Inrush 0.8 pu remanence, 0 deg',     'Inrush_NoLoad',        60,   struct('tEnergise', 0.30, 'angle', 0, 'flux', [0.8 -0.4 -0.4])
 'Recovery inrush (HV bus, 50 ms)',    'Recovery_Inrush',      40,   struct('tFault', 0.35, 'faultClear', 0.40, 'Rf', 0.05, 'srcPhase', 30, 'freq', 50, 'srcZScale', 1)
 'Over-excitation 1.3 pu',             'Overexcitation',       50,   struct('srcScale', 1.30)
 'External 3-phase solid',             'External_ABC',         60,   struct('tFault', 0.45, 'Rf', 0.01)
 'External A-G + CT saturation 8 x',   'Stress_ExtCTSat_AG',   70,   struct('tFault', 0.45, 'Rf', 0.01, 'ctBurden', 8)
 'Internal A-G solid (LV side)',       'Internal_AG',          60,   struct('tFault', 0.45, 'Rf', 0.1)
 'Internal A-B, HV side',              'InternalHV_AB',        50,   struct('tFault', 0.45, 'Rf', 0.05)
 'Internal HiZ A-B, AI-only bin',      'Internal_HiZ_AB',      60,   struct('tFault', 0.45, 'Rf', 3.0)
 'SOTF A-B',                           'Internal_SOTF_AB',     40,   struct('tEnergise', 0.30, 'Rf', 0.1)
 'Fault during inrush A-B-G',          'Stress_FaultInInrush', 60,   struct('tEnergise', 0.25, 'tFault', 0.31, 'Rf', 0.1)};
L = struct('name', {}, 'sc', {}, 'p', {}, 'expectTrip', {}, 'tRef', {});
for k = 1:size(spec, 1)
    sc = pick(spec{k, 2});
    p = drawParameters(sc, cfg.seed + 700000 + k, makeCtx(cfg, sc, 0, 0, 0)); p.sampleSeed = cfg.seed + 700000 + k;
    ov = spec{k, 4};
    p.noisePct = 0.3; p.pf = 0.9; p.srcScale = 1.0; p.srcZScale = 1; p.freq = 50; p.ctBurden = 1.0;
    if any(strcmp(sc.kind, {'ct_stress_ext', 'ct_stress_int'})), p.noisePct = 1.5; end
    if strcmp(sc.kind, 'overexc'), p.srcScale = 1.15; end
    p.loadPu = spec{k, 3} / 100; p.loadKnob = load_knob_for(spec{k, 3}, p.pf, cfg.loadCal);
    f = fieldnames(ov);
    for q = 1:numel(f)
        switch f{q}
            case 'angle', p.srcPhase = mod(ov.angle - 360 * p.freq * p.tEnergise, 360);
            case 'flux', p.residualFlux = ov.flux;
            otherwise, p.(f{q}) = ov.(f{q});
        end
    end
    if isfield(ov, 'tEnergise') && ~isfield(ov, 'tFault') && strcmp(sc.kind, 'sotf'), p.tFault = p.tEnergise; end
    if strcmp(sc.kind, 'overexc') && isfield(ov, 'srcScale'), p.srcScale = ov.srcScale; end
    if isnan(p.tFault), p.tEvent = p.tEnergise; else, p.tEvent = p.tFault; end
    if any(strcmp(sc.kind, {'normal', 'overexc'})), p.tEvent = NaN; end
    if strcmp(sc.kind, 'recovery_inrush'), p.tEvent = p.faultClear; end
    tref = p.tFault; if isnan(tref), tref = p.tEnergise; end
    L(end + 1) = struct('name', spec{k, 1}, 'sc', sc, 'p', p, 'expectTrip', logical(sc.shouldTrip), 'tRef', tref); %#ok<AGROW>
end
end

function runClosedLoop(model, B, L, cfg, thisDir, tag)
fprintf('\n=== CLOSED LOOP (%s): %d cases, LSTM active, real relay trip logic ===\n', tag, numel(L));
R = struct('name', {}, 'expectTrip', {}, 'tripped', {}, 'tripTime', {}, 'tRef', {}, 'maxProb', {}, 'passed', {}, 'delayMs', {}, 'sampleSeed', {});
fid = fopen(fullfile(thisDir, sprintf('test_hybrid_relay_%s_results.txt', tag)), 'w');
hdr = sprintf('Closed-loop validation (%s), LSTM active, relay trip logic of the saved model, %s\n%-36s %-8s %-8s %-9s %-10s %-8s\n%s\n', tag, datestr(now), 'case', 'expect', 'actual', 'max prob', 'delay ms', 'status', repmat('-', 1, 86)); %#ok<TNOW1,DATST>
fprintf('%s', hdr); if fid > 0, fprintf(fid, '%s', hdr); end
for k = 1:numel(L)
    setappdata(0, 'HybridRelaySkipLSTM', false); clear lstm_predict_wrapper;
    applyScenario(B, L(k).sc, L(k).p, cfg);
    tripped = false; tripTime = NaN; maxProb = NaN;
    try
        out = sim(model, 'StopTime', sprintf('%.4f', cfg.stopTime), 'ReturnWorkspaceOutputs', 'on');
        lg = out.get('logsout');
        for nm = {'Dec_Trip_Signal', 'TripSignal', 'Trip_Signal'}
            el = lg.get(nm{1});
            if ~isempty(el)
                if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
                t = el.Values.Time; d = squeeze(double(el.Values.Data));
                i = find(t >= 0.056 & d > 0.5, 1, 'first');
                if ~isempty(i), tripped = true; tripTime = t(i); end
                break;
            end
        end
        try
            pe = lg.get('LSTM_Prediction'); if isa(pe, 'Simulink.SimulationData.Dataset'), pe = pe{1}; end
            tp = pe.Values.Time; pv = squeeze(double(pe.Values.Data)); maxProb = max(pv(tp >= 0.056));
        catch
        end
    catch ME
        fprintf('  simulation failed for %s: %s\n', L(k).name, ME.message);
    end
    delayMs = NaN; if tripped, delayMs = 1000 * (tripTime - L(k).tRef); end
    passed = (tripped == L(k).expectTrip) && (~L(k).expectTrip || (delayMs >= 0 && delayMs <= 30));
    if ~L(k).expectTrip, passed = ~tripped; end
    R(end + 1) = struct('name', L(k).name, 'expectTrip', L(k).expectTrip, 'tripped', tripped, 'tripTime', tripTime, 'tRef', L(k).tRef, 'maxProb', maxProb, 'passed', passed, 'delayMs', delayMs, 'sampleSeed', L(k).p.sampleSeed); %#ok<AGROW>
    line = sprintf('%-36s %-8s %-8s %-9.4f %-10.1f %-8s\n', L(k).name, ifelse(L(k).expectTrip, 'TRIP', 'BLOCK'), ifelse(tripped, 'TRIP', 'BLOCK'), maxProb, delayMs, ifelse(passed, 'PASS', 'FAIL'));
    fprintf('%s', line); if fid > 0, fprintf(fid, '%s', line); end
end
ftr = sprintf('%s\nPassed %d / %d (trip decisions correct; internal faults must trip within 30 ms of the fault / energisation)\n', repmat('-', 1, 86), sum([R.passed]), numel(R));
fprintf('%s', ftr); if fid > 0, fprintf(fid, '%s', ftr); fclose(fid); end
save(fullfile(thisDir, sprintf('test_hybrid_relay_%s_results.mat', tag)), 'R');
end

% =====================================================================================
% Model configuration
% =====================================================================================
function B = locateBlocks(model)
B.model = model;
B.hv    = findBlock(model, 'Three-Phase Breaker');
B.lv    = findBlock(model, 'Three-Phase Breaker1');
B.load  = findBlock(model, 'Three-Phase Series RLC Load');
B.xf    = findBlock(model, 'Step_down_Transformer');
B.vs    = {findBlock(model, 'VSa'), findBlock(model, 'VSb'), findBlock(model, 'VSc')};
B.fault = struct('blk', {findBlock(model, 'Internal_Fault1'), findBlock(model, 'Internal_Fault2'), ...
                         findBlock(model, 'Internal_Fault3'), findBlock(model, 'External_Fault'), findBlock(model, 'Internal_Fault_HV'), findBlock(model, 'External_Fault_HV')}, ...
                 'step', {findBlock(model, 'Step3'), findBlock(model, 'Step_Evolve2'), ...
                          findBlock(model, 'Step_Evolve3'), findBlock(model, 'Step4'), findBlock(model, 'Step_HV'), findBlock(model, 'Step_ExtHV')});
B.nmu   = findBlock(model, 'Noise Merging Unit');
B.blwn  = findBlock(B.nmu, 'Band-Limited White Noise');
for k = 1:6
    B.noiseGain{k} = findBlock(B.nmu, sprintf('Noise_Gain_%d', k));
    B.ctGain{k}    = findBlock(B.nmu, sprintf('CT_Gain_Mismatch_%d', k));
end
B.relay = findBlock(model, 'Hybrid 87T Relay');
B.srcZ  = findBlock(model, 'Three-Phase Series RLC Branch');
B.priV  = findBlock(model, 'Primary_side');
B.secV  = findBlock(model, 'Secondary_side');
ctNames = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'};
for k = 1:6
    B.ctBurden{k} = findBlock(findBlock(model, ctNames{k}), '1ohm');
end
end

function blk = findBlock(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
normName = @(s) strtrim(regexprep(s, '\s+', ' '));
hit = c(strcmp(cellfun(@(s) normName(get_param(s, 'Name')), c, 'UniformOutput', false), normName(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'GenPlantB:Block', 'Expected exactly one block "%s" under %s, found %d.', name, parent, numel(hit));
blk = hit{1};
end

function setp(blk, varargin)
set_param(blk, varargin{:});
for k = 1:2:numel(varargin)
    want = strtrim(varargin{k + 1}); got = strtrim(get_param(blk, varargin{k}));
    if ~strcmp(want, got)
        a = parseNums(want); b = parseNums(got);
        assert(~isempty(a) && isequal(size(a), size(b)) && all(abs(a(:) - b(:)) <= 1e-9 * max(1, abs(a(:)))), ...
            'GenPlantB:SetParam', '%s: %s should be "%s" but is "%s".', blk, varargin{k}, want, got);
    end
end
end

function finishGeneration(model)
if isappdata(0, 'HybridRelaySkipLSTM'), rmappdata(0, 'HybridRelaySkipLSTM'); end
if bdIsLoaded(model), close_system(model, 0); end
end

function v = parseNums(s)
t = strtrim(regexprep(s, '[\[\],;]', ' '));
if isempty(t) || ~isempty(regexp(t, '[^0-9eE+\-\.\s]', 'once')), v = []; return; end
v = sscanf(t, '%f');
end

function prepareModelForGeneration(B)
setp(B.hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(B.lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setappdata(0, 'HybridRelaySkipLSTM', true);
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}
    try
        set_param(B.model, m{1}, 'none');
    catch ME
        warning('GenPlantB:Diag', 'Could not set %s (%s); the log will just be longer.', m{1}, ME.message);
    end
end
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
setp(B.blwn, 'Cov', mat2str(0.1 * ones(1, 6)), 'seed', mat2str(1:6));
dph = get_param(findBlock(B.relay, 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');
for kk = 1:2
    sideBlk = {B.priV, B.secV}; nm = {'TruePrimI', 'TrueSecI'};
    pp = get_param(sideBlk{kk}, 'PortHandles');
    set_param(pp.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', nm{kk});
end
end

function applyScenario(B, sc, p, cfg)
for f = B.fault
    setp(f.blk, 'External', 'on', 'SwitchTimes', '[0.05 1]', 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');
    setp(f.step, 'Time', '10', 'Before', '0', 'After', '1');
end

switch sc.kind
    case 'normal'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
    case {'internal', 'ct_stress_int'}
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case 'overexc'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
    case 'recovery_inrush'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        setp(B.fault(6).blk, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off', 'FaultResistance', sprintf('%.6g', p.Rf), ...
            'External', 'off', 'SwitchTimes', sprintf('[%.6f %.6f]', p.tFault, p.faultClear));
    case 'internal_hv'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 5, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case {'external', 'ct_stress_ext'}
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 4, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case 'evolving'
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 1, [1 1 0 0], p.Rf, p.tFault);
        armFault(B, 2, [0 1 1 0], p.Rf, p.tFault2);
    case {'inrush_noload', 'inrush_loaded'}
        breakersEnergise(B, p.tEnergise, strcmp(sc.kind, 'inrush_loaded'));
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
    case 'sotf'
        breakersEnergise(B, p.tEnergise, true);
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, max(p.tEnergise - 0.05, 0.01));
    case 'fault_in_inrush'
        breakersEnergise(B, p.tEnergise, true);
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
        armFault(B, 1, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    case 'ext_in_inrush'
        breakersEnergise(B, p.tEnergise, true);
        setp(B.xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(p.residualFlux, 4));
        armFault(B, 4, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
    otherwise
        error('GenPlantB:Kind', 'Unknown scenario kind %s', sc.kind);
end

% Load (rated 33 kV on Plant B) and source (132 kV line-to-line)
S = p.loadKnob * cfg.Srated;
setp(B.load, 'ActivePower', sprintf('%.6g', S * p.pf), ...
             'InductivePower', sprintf('%.6g', max(S * sqrt(max(1 - p.pf ^ 2, 0)), 1)), 'CapacitivePower', '0');
amp = sprintf('%.6g', p.srcScale * 132e3 * sqrt(2) / sqrt(3));
ph0 = [0 -120 120];
for k = 1:3
    setp(B.vs{k}, 'Amplitude', amp, 'Phase', sprintf('%.6g', p.srcPhase + ph0(k)), 'Frequency', sprintf('%.6g', p.freq));
end
setp(B.srcZ, 'Resistance', sprintf('%.6g', cfg.srcZ0(1) * p.srcZScale), 'Inductance', sprintf('%.6g', cfg.srcZ0(2) * p.srcZScale));

% CT burden (x nominal 2.5 ohms on Plant B)
for k = 1:6
    setp(B.ctBurden{k}, 'Resistance', sprintf('%.6g', cfg.nominalBurden * p.ctBurden));
end

% Noise and CT mismatch
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
setp(B.hv, 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
setp(B.lv, 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
end

function breakersEnergise(B, t, loaded)
setp(B.hv, 'InitialState', 'open', 'SwitchTimes', sprintf('[%.6f 11]', t));
if loaded
    setp(B.lv, 'InitialState', 'open', 'SwitchTimes', sprintf('[%.6f 11]', t));
else
    setp(B.lv, 'InitialState', 'open', 'SwitchTimes', '[10 11]');
end
end

% =====================================================================================
% Simulation + waveform checks
% =====================================================================================
function [rec, status] = simulateAndCheck(model, B, sc, p, cfg, fingerprints)
rec = struct('Ip', [], 'Is', [], 'eventDetected', NaN, 'energiseDetected', NaN, 'timingOK', 0, 'eventVisible', NaN, ...
             'noiseMeasured', NaN, 'noiseExpected', NaN, 'noiseOK', NaN, 'duplicate', 0, ...
             'faultDiffPu', NaN, 'extFaultPu', NaN, 'loadRealisedPct', NaN, 'loadOK', NaN, 'ctRatioErrorMax', NaN, ...
             'harm5Ratio', NaN, 'diffRmsPu', NaN, 'recDiffPeakPu', NaN, 'recH2', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');
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

sigHV = p.noisePct / 100 * cfg.Inom(1);
thr = 6 * sqrt(sigHV ^ 2 + cfg.quantStep ^ 2 / 12) + cfg.quantStep + 0.01 * cfg.Inom(1);
k = find(max(abs(Ip), [], 2) > thr, 1);
if isempty(k), rec.energiseDetected = NaN; else, rec.energiseDetected = (k - 1) / fs; end

Mpl = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
d = Is * Mpl.' - Ip;
cdiff = [zeros(32, 1); max(abs(d(33:end, :) - d(1:end - 32, :)), [], 2)];
if isnan(p.tEvent)
    rec.timingOK = 1;
else
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
        tol = cfg.timingTol;
        if any(strcmp(sc.kind, {'fault_in_inrush', 'ext_in_inrush'})), tol = 0.030; end
        rec.timingOK = double(abs(rec.eventDetected - p.tEvent) <= tol);
    else
        rec.timingOK = NaN;
    end
end

if strcmp(sc.kind, 'recovery_inrush')
    rb = mean(sqrt(mean(Ip(t >= p.tFault - 0.04 & t <= p.tFault - 0.005, :) .^ 2, 1)));
    rd = mean(sqrt(mean(Ip(t >= p.tFault + 0.012 & t <= p.faultClear - 0.005, :) .^ 2, 1)));
    hvDipRatio = rd / max(rb, eps);
    rec.timingOK = double(hvDipRatio < 0.85);
    rec.eventVisible = rec.timingOK;
end

if strcmp(sc.kind, 'inrush_noload') && isnan(rec.energiseDetected)
    energiseOK = true;
    rec.eventVisible = 0; rec.timingOK = NaN;
elseif startsWith(sc.kind, 'inrush') || any(strcmp(sc.kind, {'sotf', 'fault_in_inrush', 'ext_in_inrush'}))
    energiseOK = abs(rec.energiseDetected - p.tEnergise) <= cfg.timingTol;
else
    energiseOK = rec.energiseDetected <= 0.03;
end
if ~energiseOK, rec.timingOK = 0; end

healthy = t > 0.12 & t < 0.28;
if any(strcmp(sc.kind, {'normal', 'overexc'})), healthy = t > 0.12 & t < 1.0; end
if startsWith(sc.kind, 'inrush') || any(strcmp(sc.kind, {'sotf', 'fault_in_inrush', 'ext_in_inrush'})), healthy = false(size(t)); end
if any(healthy)
    q2 = cfg.quantStep ^ 2 / 12;
    sp = p.noisePct / 100 * cfg.Inom(1:3); ss = p.noisePct / 100 * cfg.Inom(4:6);
    rec.noiseExpected = median(sqrt(2 * (sp .^ 2 + ss .^ 2 + 2 * q2)));
    seg = d(healthy, :); seg32 = seg(33:end, :) - seg(1:end - 32, :);
    rec.noiseMeasured = median(std(seg32));
    resid = 2 * max(abs(sin(pi * (1:7) * p.freq * 32 / fs))) * sqrt(mean(seg(:) .^ 2));
    rec.noiseOK = double(rec.noiseMeasured > 0.5 * rec.noiseExpected && rec.noiseMeasured < 2 * rec.noiseExpected + 0.01 + resid);
end

loadWin = [];
if any(strcmp(sc.kind, {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext', 'evolving'}))
    loadWin = t > 0.12 & t < min(p.tEvent - 0.03, 0.28);
elseif any(strcmp(sc.kind, {'normal', 'overexc'}))
    loadWin = t > 0.12 & t < 1.0;
elseif strcmp(sc.kind, 'recovery_inrush')
    loadWin = t > 0.12 & t < 0.28;
end
if any(loadWin)
    lsg0 = out.get('logsout');
    [iP0, tP0] = loggedSignal(lsg0, 'TruePrimI'); [iS0, ~] = loggedSignal(lsg0, 'TrueSecI');
    tHi = t(find(loadWin, 1, 'first')); tLo = t(find(loadWin, 1, 'last'));
    wT = tP0 >= tHi & tP0 <= tLo;
    pH = mean(sqrt(mean(iP0(wT, :) .^ 2, 1))) / 174.9546;
    pL = mean(sqrt(mean(iS0(wT, :) .^ 2, 1))) / 699.8182;
    rec.loadRealisedPct = 100 * 0.5 * (pH + pL);
    if strcmp(sc.kind, 'overexc'), rec.loadRealisedPct = 100 * pL; end
    target = 100 * p.loadPu * p.srcScale;
    rec.loadOK = double(abs(rec.loadRealisedPct - target) <= max(cfg.loadTolPct / 100 * target, 2));
end

try
    el = out.get('logsout').get('I_diff_comp');
    tc = el.Values.Time; dc = squeeze(double(el.Values.Data));
    if size(dc, 2) ~= 3, dc = dc.'; end
    if ~isnan(p.tFault) && ~strcmp(sc.kind, 'recovery_inrush')
        rmsWin = @(t1, t2) sqrt(mean(dc(tc >= t1 & tc < t2, :) .^ 2, 1));
        rec.faultDiffPu = max(rmsWin(p.tFault + 0.04, p.tFault + 0.06) - rmsWin(p.tFault - 0.03, p.tFault - 0.01));
    end
    if any(strcmp(sc.zone, 'External')) && ~isnan(p.tFault)
        wF = t >= p.tFault + 0.010 & t <= p.tFault + 0.050;
        if any(wF)
            rmsIp = sqrt(mean(Ip(wF, :) .^ 2, 1)) / cfg.Inom(1);
            rmsIs = sqrt(mean(Is(wF, :) .^ 2, 1)) / cfg.Inom(4);
            rec.extFaultPu = max([rmsIp rmsIs]);
        end
    end
catch
end

try
    if ~isnan(p.tEvent)
        lsg = out.get('logsout');
        [iP, tP] = loggedSignal(lsg, 'TruePrimI'); [iS, ~] = loggedSignal(lsg, 'TrueSecI');
        w = t >= p.tEvent + 0.005 & t <= p.tEvent + 0.045;
        if nnz(w) > 10
            iPw = interp1(tP, iP, t(w)); iSw = interp1(tP, iS, t(w));
            rP = sqrt(mean(iPw .^ 2, 1)); rS = sqrt(mean(iSw .^ 2, 1));
            eP = sqrt(mean((cfg.ctRatio(1) * Ip(w, :) - iPw) .^ 2, 1)) ./ max(rP, eps);
            eS = sqrt(mean((cfg.ctRatio(2) * Is(w, :) - iSw) .^ 2, 1)) ./ max(rS, eps);
            ok = [rP rS] > 0.02 * [174.9546 * ones(1, 3), 699.8182 * ones(1, 3)];
            if any(ok), e = [eP eS]; rec.ctRatioErrorMax = 100 * max(e(ok)); end
        end
    end
catch
end

% Plant B (Dyn11): Phase compensation applied to LV side
Mpl = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
dpl = Is * Mpl.' - Ip;
dft = @(i0) abs(fft(dpl(i0:i0 + 31, :), [], 1));
if strcmp(sc.kind, 'overexc')
    i0 = round(0.60 * fs) + 1; F = dft(i0);
    rec.harm5Ratio = mean(F(6, :) ./ max(F(2, :), 1e-4));
    rec.diffRmsPu = mean(sqrt(mean(dpl(i0:i0 + 31, :) .^ 2, 1))) / cfg.Inom(1);
elseif strcmp(sc.kind, 'recovery_inrush')
    best = 0; h2 = NaN;
    for i0 = round((p.faultClear + 0.005) * fs):2:min(round((p.faultClear + 0.15) * fs), size(dpl, 1) - 32)
        r = mean(sqrt(mean(dpl(i0:i0 + 31, :) .^ 2, 1))) / cfg.Inom(1);
        if r > best, best = r; F = dft(i0); h2 = mean(F(3, :) ./ max(F(2, :), 1e-4)); end
    end
    rec.recDiffPeakPu = best; rec.recH2 = h2;
end

md = java.security.MessageDigest.getInstance('SHA-1');
md.update(typecast([Ip(:); Is(:)], 'int8'));
rec.fingerprint = lower(reshape(dec2hex(typecast(md.digest(), 'uint8'))', 1, []));
rec.duplicate = double(fingerprints.isKey(rec.fingerprint));

rec.checkPassed = double(rec.timingOK ~= 0 && rec.duplicate == 0 && rec.noiseOK ~= 0);
status = 'OK'; if ~rec.checkPassed, status = 'CHK'; end
end

function [v, t] = loggedSignal(ls, name)
el = ls.get(name);
if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data));
if size(v, 1) ~= numel(t), v = v.'; end
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
         'noiseOK', 'duplicate', 'faultDiffPu', 'extFaultPu', 'loadRealisedPct', 'loadOK', 'ctRatioErrorMax', 'harm5Ratio', ...
         'diffRmsPu', 'recDiffPeakPu', 'recH2', 'checkPassed', 'loadKnob', 'ctBurden', 'loadBin', 'angleBin', 'fluxBin', 'hizBin', 'sourceZScale', 'frequencyHz', 'oodBlock'}
    D.(f{1}) = nan(1, N);
end
end

function D = store(D, i, sc, p, rec, status)
D.zone{i} = sc.zone; D.faultType{i} = sc.faultTag; D.scenarioName{i} = sc.name; D.scenarioKind{i} = sc.kind;
D.simulationStatus{i} = ifelse(strcmp(status, 'ERR'), ['Failed: ' rec.message], 'Success');
D.primaryCurrent{i} = rec.Ip; D.secondaryCurrent{i} = rec.Is;
D.fingerprint{i} = rec.fingerprint; D.checkMessage{i} = rec.message;
D.shouldTrip(i) = uint8(sc.shouldTrip);
D.inceptionTime(i) = p.tFault;
D.energisationTime(i) = p.tEnergise;
D.faultTime2(i) = p.tFault2; if strcmp(sc.kind, 'recovery_inrush'), D.faultTime2(i) = p.faultClear; end
D.faultResistance(i) = p.Rf; D.inceptionAngle(i) = p.inceptionAngle;
D.noiseLevel(i) = p.noisePct / 100; D.noisePct(i) = p.noisePct;
D.loadPu(i) = p.loadPu; D.loadKnob(i) = p.loadKnob; D.ctBurden(i) = p.ctBurden;
D.loadBin(i) = p.loadBin; D.angleBin(i) = p.angleBin; D.fluxBin(i) = p.fluxBin; D.hizBin(i) = p.hizBin;
D.sourceZScale(i) = p.srcZScale; D.frequencyHz(i) = p.freq; D.oodBlock(i) = p.oodBlock; D.powerFactor(i) = p.pf; D.sourceScale(i) = p.srcScale; D.sourcePhaseDeg(i) = p.srcPhase;
D.ctMismatchMaxPct(i) = 100 * max(abs(p.ctGain - 1)); D.sampleSeed(i) = p.sampleSeed;
for f = {'eventDetected', 'energiseDetected', 'timingOK', 'eventVisible', 'noiseMeasured', 'noiseExpected', ...
         'noiseOK', 'duplicate', 'faultDiffPu', 'extFaultPu', 'loadRealisedPct', 'loadOK', 'ctRatioErrorMax', 'harm5Ratio', 'diffRmsPu', 'recDiffPeakPu', 'recH2', 'checkPassed'}
    D.(f{1})(i) = rec.(f{1});
end
end

function f = partialFile(dir, fileTag, runId)
f = fullfile(dir, sprintf('StressDataset_PlantB%s_%s_PARTIAL.mat', fileTag, runId));
end

% =====================================================================================
% Self-test
% =====================================================================================
function runSelfTest(model, B, ST, cfg, range)
names = {'Normal', 'Internal_AB', 'Internal_HiZ_AB', 'Internal_AG', 'Inrush_NoLoad', 'Inrush_Loaded', 'External_ABC', 'Internal_SOTF_AB', 'Internal_Evolving', ...
         'Stress_ExtCTSat_ABC', 'Stress_ExtCTSat_AG', 'Stress_CTSat_Int_AB', 'InternalHV_AG', 'InternalHV_AB', 'Overexcitation', 'Recovery_Inrush', ...
         'Stress_FaultInInrush', 'Stress_ExtInInrush'};
if isempty(range), range = [1 numel(names)]; end
sel = range(1):min(range(2), numel(names));
fprintf('\n=== SELF-TEST PLANT B (nothing is saved) ===\n');
fp = containers.Map('KeyType', 'char', 'ValueType', 'double');
allOK = true;
for i = sel
    sc = ST(strcmp({ST.name}, names{i}));
    p = drawParameters(sc, cfg.seed + 900000 + i, makeCtx(cfg, sc, 0, 0, 0)); p.sampleSeed = cfg.seed + 900000 + i;
    applyScenario(B, sc, p, cfg);
    [rec, status] = simulateAndCheck(model, B, sc, p, cfg, fp);
    if ~isempty(rec.fingerprint), fp(rec.fingerprint) = i; end
    fprintf('%-22s %-3s | load %3.0f%% (real %3.0f%%) burden %.1fx CTerr %3.0f%% | event %s det %s visible %g | energised %s | noise %.4f/%.4f A | faultDiff %.3f pu (extFault %.2f pu) | %s\n', ...
        names{i}, status, 100 * p.loadPu, rec.loadRealisedPct, p.ctBurden, rec.ctRatioErrorMax, fmtT(p.tEvent), fmtT(rec.eventDetected), rec.eventVisible, ...
        fmtT(rec.energiseDetected), rec.noiseMeasured, rec.noiseExpected, rec.faultDiffPu, rec.extFaultPu, checkText(rec));
    if strcmp(sc.kind, 'overexc')
        fprintf('      over-excitation: source %.2f pu, differential %.3f pu rms, 5th/1st harmonic %.2f\n', p.srcScale, rec.diffRmsPu, rec.harm5Ratio);
    elseif strcmp(sc.kind, 'recovery_inrush')
        fprintf('      recovery inrush: HV-bus fault %.3f -> %.3f s (Rf %.2f ohm), peak differential after clearing %.3f pu, 2nd/1st harmonic %.2f\n', p.tFault, p.faultClear, p.Rf, rec.recDiffPeakPu, rec.recH2);
    end
    allOK = allOK && rec.checkPassed == 1;
end
if allOK
    fprintf('SELF-TEST PLANT B PASSED. Ready to generate dataset.\n');
else
    fprintf('SELF-TEST PLANT B: some checks failed.\n');
end
end

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
