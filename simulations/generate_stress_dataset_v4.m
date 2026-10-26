function outFile = generate_stress_dataset_v4(nSamples, varargin)
%GENERATE_STRESS_DATASET_V4 Stress dataset on TransformerWithCTSaturation_v4 (series CT wiring).
%
%   generate_stress_dataset_v4('selftest')        % quick cases, prints the checks, saves nothing
%   outFile = generate_stress_dataset_v4(3040)    % main set -> ONE file datasets\StressDataset_v4_<run>.mat
%   generate_stress_dataset_v4(300, 'Set', 'OOD') % out-of-distribution set -> StressDataset_v4OOD_<run>.mat
%   generate_stress_dataset_v4(80, 'Only', 'Stress_ExtCTSat')   % top-up of named scenarios / kinds / zones
%                                                  %   -> StressDataset_v4Only_<run>.mat (own seed range: no duplicates of the main run)
%
% OPTIONS (name, value pairs)
%   'Run'     run id. If datasets\StressDataset_v4*_<run>_PARTIAL.mat exists the run RESUMES from it (same seed and N required),
%             otherwise it starts fresh under that id. Default: timestamp (fresh run).
%   'Resume'  alias of 'Run' (v2 name).
%   'Chunk'   stop cleanly after this many simulations in THIS MATLAB process (partial file saved) and return ''. The wrapper
%             run_stress_v3_generate.bat restarts MATLAB until the final file exists. MATLAB's heap-corruption crash
%             (0xc0000374) appears after ~50-150 simulations, so a restart BEFORE it avoids losing work. 0 = never (default).
%   'Set'     'main' (default) | 'OOD' (out-of-distribution ranges; default seed 20261022).
%   'Only'    char or cellstr of scenario names, kinds or zones to generate (default: all).
%   'Seed'    base seed (default 20261021; sample k uses rng(seed + k)).
%   'StopTime' simulation length in seconds (default 1.10).
%   'OverexcMin' lower bound (pu) of the over-excitation source voltage, default 1.15 (main set); the coverage top-up uses 1.22 (saturated core).
%   'Indices' closedloop only: dataset trace numbers (1..N of the chosen 'Set') to re-run with the LSTM active (D4); empty = the 12 D3 cases.
%   'Tag'     closedloop only: suffix of the result files.
%   'Range'   self-test only: [first last] case numbers (the heap crash can hit a long single session; run 1:9 and 10:18).
%
% v3 = v2 plus the changes of IMPLEMENTATION_PLAN_V3.md (A1: the options above; A2-A8 add load calibration, CT stress, HiZ bins,
% HV-side faults, over-excitation / recovery inrush, stratified sampling and the extended self-test).
%
% ---- v2 notes (still valid) ----
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

warning('off', 'all');
model = 'TransformerWithCTSaturation_v4';
thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);
datasetsDir = fullfile(projectDir, 'datasets');

selfTest = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'selftest');
closedLoop = nargin >= 1 && (ischar(nSamples) || isstring(nSamples)) && strcmpi(nSamples, 'closedloop');
if nargin < 1 || isempty(nSamples) || selfTest || closedLoop, nSamplesNum = 3040; else, nSamplesNum = nSamples; end
opts = struct('Resume', '', 'Run', '', 'Seed', 20261021, 'StopTime', 1.10, 'Chunk', 0, 'Set', 'main', 'Only', {{}}, 'Range', [], 'OverexcMin', 1.15, 'Indices', [], 'Tag', 'v4');
for k = 1:2:numel(varargin)
    assert(isfield(opts, varargin{k}), 'GenV4:Option', 'Unknown option "%s".', varargin{k});
    opts.(varargin{k}) = varargin{k + 1};
end
seedGiven = any(strcmp(varargin(1:2:end), 'Seed'));
if ~isempty(opts.Resume) && isempty(opts.Run), opts.Run = opts.Resume; end
opts.Set = char(opts.Set);
assert(any(strcmp(opts.Set, {'main', 'OOD'})), 'GenV4:Option', 'Set must be main or OOD.');
if ischar(opts.Only) || isstring(opts.Only), opts.Only = cellstr(opts.Only); end
if ~seedGiven
    if strcmp(opts.Set, 'OOD'), opts.Seed = 20261022; end
    if ~isempty(opts.Only), opts.Seed = opts.Seed + 500000 + sum(double([opts.Only{:}])); end   % own seed range: no duplicates of the main run
end
fileTag = ''; if strcmp(opts.Set, 'OOD'), fileTag = 'OOD'; elseif ~isempty(opts.Only), fileTag = 'Only'; end

cfg = struct();
cfg.version   = 'v4-2026-10-27-pub';
cfg.fs        = 1600;
cfg.stopTime  = opts.StopTime;
cfg.set       = opts.Set;
cfg.oeMin     = opts.OverexcMin;
cfg.only      = strjoin(opts.Only, ',');
cfg.seed      = opts.Seed;
cfg.Srated    = 300e6;
cfg.Inom      = 1.8610 * ones(1, 6);   % rated CT secondary current (A): HV x3, LV x3. probe_ct_truth_v4.m
cfg.ctRatio   = [404.7288 8460.0372];  % effective CT ratios HV / LV, probe_ct_truth_v4.m
cfg.loadTolPct = 10;                    % realised load must be within +/-10 % of the target (or 2 points of rated at very light load)
cfg.timingTol = 0.0125;                                       % allowed |detected - intended| event time (s)

% ---------------------------------------------------------------- model, safely in memory only
if bdIsLoaded(model) && strcmp(get_param(model, 'Dirty'), 'on')
    error('GenV4:Dirty', ['%s is open with UNSAVED changes. Save or close it first: this generator ' ...
        'changes the model in memory and closes it WITHOUT saving.'], model);
end
load_system(fullfile(thisDir, [model '.slx']));
cleanup = onCleanup(@() finishGeneration(model));  %#ok<NASGU>  never saves the .slx, clears the LSTM skip flag

B = locateBlocks(model);
prepareModelForGeneration(B);
cfg.srcZ0 = [str2double(get_param(B.srcZ, 'Resistance')), str2double(get_param(B.srcZ, 'Inductance'))];
assert(abs(cfg.srcZ0(1) - 0.1) < 1e-9 && abs(cfg.srcZ0(2) - 1e-3) < 1e-12, 'GenV4:SrcZ', 'unexpected source impedance %s / %s', get_param(B.srcZ, 'Resistance'), get_param(B.srcZ, 'Inductance'));
cfg.hizBins = jsondecode(fileread(fullfile(thisDir, 'hiz_bins.json')));            % A4: Rf bins of the internal HiZ faults
cfg.blwnStd = sqrt(0.1 / str2double(get_param(B.blwn, 'Ts')));      % BLWN output std (Cov 0.1 per channel)
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
    assert(any(keep), 'GenV4:Only', 'Only = {%s} matches no scenario name, kind or zone.', strjoin(opts.Only, ', '));
    ST = ST(keep);
end
weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
counts(1) = counts(1) + (nSamplesNum - sum(counts));
N = sum(counts);
plan = repelem(1:numel(ST), counts);
blockOf = zeros(1, N);
if strcmp(opts.Set, 'OOD')
    [plan, blockOf, counts, ST] = oodPlan(ST);          % 5 blocks x 60 traces (30 healthy + 30 faults); nSamples is ignored
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
finalFile = fullfile(datasetsDir, sprintf('StressDataset_v4%s_%s.mat', fileTag, runId));
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
        'GenV4:Resume', 'Resume file was made with a different seed or sample count.');
    dataset = P.dataset;
    startAt = find(cellfun(@isempty, dataset.simulationStatus), 1);
    if isempty(startAt), startAt = N + 1; end
end
cfg.N = N; cfg.runId = runId;

fprintf('=== Stress dataset v4 | set %s | run %s | %d samples | %d scenarios | start at %d | chunk %d ===\n', opts.Set, runId, N, numel(ST), startAt, opts.Chunk);
for i = 1:numel(ST), fprintf('  %-26s %4d\n', ST(i).name, counts(i)); end

fingerprints = containers.Map('KeyType', 'char', 'ValueType', 'double');
for j = 1:startAt - 1
    if ~isempty(dataset.fingerprint{j}), fingerprints(dataset.fingerprint{j}) = j; end
end

t0 = tic;
for idx = startAt:N
    sc = ST(plan(idx));
    within = idx - firstOf(plan(idx)) + 1;
    if strcmp(opts.Set, 'OOD'), within = 0; end                      % OOD: plain random draws inside the block ranges
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
    if opts.Chunk > 0 && done >= opts.Chunk && idx < N      % planned restart before MATLAB's heap-corruption crash
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
% name | zone | kind | fA fB fC fG | RfLo RfHi (ohm) | shouldTrip | weight      (weights = trace counts for N = 3040, IMPLEMENTATION_PLAN_V3.md 1.2)
% PHYSICS: the transformer is Y (ungrounded) / Delta; the LV internal fault blocks sit on the 11 kV DELTA terminals, the HV-side ones
% (InternalHV_*) on the 230 kV winding terminals. Single-line-to-ground current on the delta side returns through the grounded-Y LOAD neutral
% and grows with load. Internal HiZ Rf comes from the sensitivity sweep (hiz_bins.json), 3 bins: 87T-visible / AI-only / undetectable.
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
hz = {'AB' [1 1 0 0]; 'BC' [0 1 1 0]; 'AC' [1 0 1 0]; 'ABC' [1 1 1 0]; 'AG' [1 0 0 1]};      % 5 HiZ types x 48 (3 Rf bins x 16)
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
% ctx: struct('hiz', hiz_bins, 'seed0', base seed, 'within', i, 'n', n, 'block', OOD block 0-5, 'sid', scenario id).
%  within > 0 : STRATIFIED draws - each bin of a dimension (load bin, inception-angle class, residual-flux bin, HiZ bin) appears floor/ceil(n/K) times
%               over the n traces of the scenario, in an independent random order per dimension (balancedBin); inside a bin the draw is uniform.
%  within = 0 : plain random draws (self-test and the OOD set).
rng(seed, 'twister');
stress = startsWith(sc.kind, 'ct_stress');
ood = ctx.block;                                       % 0 = main set, 1-5 = OOD block
p.pf = 0.80 + 0.20 * rand();                           % 0.80-1.00 lagging
% --- load, % of RATED current: 4 bins 10-30 / 30-60 / 60-90 / 90-110 (stress: 60-85 / 85-110)
if stress, edges = [60 85 110]; else, edges = [10 30 60 90 110]; end
K = numel(edges) - 1; lb = bin(ctx, 1, K);
loadPct = edges(lb) + diff(edges([lb lb + 1])) * rand();
p.loadBin = lb + 2 * stress;                           % stress traces use the two upper bins (3 and 4)
if ood == 1, if rand() < 0.5, loadPct = 1 + 9 * rand(); p.loadBin = 0; else, loadPct = 110 + 20 * rand(); p.loadBin = 5; end, end   % OOD: 1-10 / 110-130 %
p.loadPu = loadPct / 100;                              % per unit of rated CURRENT (not of the load knob)
p.loadKnob = load_knob_for(loadPct, p.pf);             % ActivePower = knob*300 MVA*pf (calibrate_load.m)
p.srcScale = 0.95 + 0.10 * rand();
% --- noise (% of rated CT secondary current) and CT gain mismatch
lo = 0.05; hi = 1.0; if stress, lo = 1; hi = 3; end
p.noisePct = 10 ^ (log10(lo) + (log10(hi) - log10(lo)) * rand());
mm = 0.02; if stress, mm = 0.05; end
if ood == 5, p.noisePct = 4 + 2 * rand(); mm = 0.08; end                       % OOD: 5 % noise, +/-8 % mismatch
% --- CT burden (x 1 ohm): stress 1-4 x (through-fault & X/R drive saturation), other traces 1-3 x; OOD 4-8 x
if stress, p.ctBurden = 1 + 3 * rand(); else, p.ctBurden = 1 + 2 * rand(); end
if ood == 3, p.ctBurden = 4 + 4 * rand(); end
p.ctGain = 1 + (2 * rand(1, 6) - 1) * mm;
p.noiseSeeds = randi([1 2^31 - 2], 1, 6);
% --- source strength (series Z scale 0.5-2 x, log-uniform; OOD 3 x) and frequency (49.8-50.2 Hz; OOD +/-0.5 Hz)
p.srcZScale = 2 ^ (2 * rand() - 1);
p.freq = 49.8 + 0.4 * rand();
if ood == 2, p.srcZScale = 3 * (0.9 + 0.2 * rand()); p.freq = 50 + sign(rand() - 0.5) * (0.5 + 0.05 * (2 * rand() - 1)); end
if ood == 2 && p.freq == 50, p.freq = 50.5; end
% --- fault resistance
p.hizBin = 0;
if startsWith(sc.name, 'Internal_HiZ_')
    p.hizBin = bin(ctx, 4, 3);                         % 1 = 87T-visible, 2 = AI-only, 3 = below the detect limit (hiz_bins.json)
    bn = ctx.hiz.(sc.name(numel('Internal_HiZ_') + 1:end)).bins;
    r = {bn.visible, bn.ai_only, bn.undetect}; r = sort(r{p.hizBin}(:)');
    p.Rf = 10 ^ (log10(r(1)) + (log10(r(2)) - log10(r(1))) * rand());
elseif sc.RfHi > sc.RfLo
    p.Rf = 10 ^ (log10(sc.RfLo) + (log10(sc.RfHi) - log10(sc.RfLo)) * rand());
else
    p.Rf = sc.RfLo;
end
% --- timing
p.tEnergise = 0; p.tFault = NaN; p.tFault2 = NaN; p.faultClear = NaN;
switch sc.kind
    case 'recovery_inrush'
        p.tFault = 0.30 + 0.15 * rand();                                        % HV-bus fault starts ...
        p.faultClear = p.tFault + 0.040 + 0.060 * rand();                       % ... and clears 40-100 ms later
    case {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext'}
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
if any(strcmp(sc.kind, {'normal', 'overexc'})), p.tEvent = NaN; end
if strcmp(sc.kind, 'recovery_inrush'), p.tEvent = p.faultClear; end              % the interesting event is the voltage recovery
% --- over-excitation level: 1.15-1.45 pu (core saturates above ~1.2 pu); OOD 1.50-1.60 pu
if strcmp(sc.kind, 'overexc'), p.srcScale = ctx.oeMin + (1.45 - ctx.oeMin) * rand(); if ood == 4, p.srcScale = 1.50 + 0.10 * rand(); end, end
% --- point on wave: inception / closing / clearing angle class (4 quadrants + 'worst case' = within 10 deg of 0 or 90 deg), then the source phase
p.angleBin = 0;
if isnan(p.tEvent)
    p.srcPhase = 360 * rand();
else
    p.angleBin = bin(ctx, 2, 5);
    if p.angleBin <= 4
        ang = 90 * (p.angleBin - 1) + 90 * rand();
    else
        ang = mod(90 * randi(2) - 90 + 20 * (rand() - 0.5), 360);                % around 0 or 90 deg
    end
    p.srcPhase = mod(ang - 360 * p.freq * p.tEvent, 360);                          % so that the angle AT the event is `ang`
end
% --- residual flux (inrush-type scenarios): bin of the largest component, 3 fluxes summing to zero; OOD 0.9 pu
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
% Stratum 1..K for dimension `dim`: balanced over the n traces of the scenario (random order), or uniform random when within = 0.
if ctx.within <= 0 || ctx.n <= 0
    b = randi(K); return;
end
b = balancedBin(ctx.seed0, ctx.sid, dim, ctx.within, ctx.n, K);
end

function b = balancedBin(seed0, sid, dim, within, n, K)
% Every bin 1..K appears floor(n/K) or ceil(n/K) times over within = 1..n; the order is an independent random permutation per (scenario, dimension).
rs = RandStream('twister', 'Seed', mod(seed0 * 7919 + sid * 104729 + dim * 1299709, 2 ^ 32 - 1));
perm = randperm(rs, n);
b = mod(perm(within) - 1, K) + 1;
end

function ctx = makeCtx(cfg, sc, within, n, block)
ctx = struct('oeMin', cfg.oeMin, 'hiz', cfg.hizBins, 'seed0', cfg.seed, 'within', within, 'n', n, 'block', block, 'sid', sum(double(sc.name) .* (1:numel(sc.name))));
end

function [plan, blockOf, counts, ST] = oodPlan(ST)
% OOD set (IMPLEMENTATION_PLAN_V3.md 1.3): 5 blocks x 60 traces, half healthy and half faults. Ranges per block are applied in drawParameters.
%   1 extreme load (1-10 %, 110-130 % rated)   2 weak source 3 x + frequency 49.5 / 50.5 Hz   3 CT burden 12-16 x
%   4 over-excitation 1.50-1.60 pu + residual flux 0.9 pu   5 noise 5 % + CT mismatch +/-8 %
L = {
 1, {'Normal' 8; 'External_ABC' 8; 'External_AB' 7; 'Inrush_Loaded' 7}, {'Internal_AB' 8; 'Internal_ABC' 8; 'InternalHV_AB' 7; 'Internal_AG' 7}
 2, {'Normal' 10; 'External_ABC' 10; 'Inrush_Loaded' 10}, {'Internal_AB' 10; 'Internal_ABC' 10; 'InternalHV_AG' 10}
 3, {'Stress_ExtCTSat_ABC' 10; 'Stress_ExtCTSat_AB' 10; 'Stress_ExtCTSat_AG' 10}, {'Stress_CTSat_Int_AB' 10; 'Stress_CTSat_Int_ABC' 10; 'Stress_CTSat_Int_AG' 10}
 4, {'Overexcitation' 12; 'Inrush_NoLoad' 6; 'Inrush_Loaded' 6; 'Recovery_Inrush' 6}, {'Internal_AB' 10; 'Internal_SOTF_AB' 10; 'Stress_FaultInInrush' 10}
 5, {'Normal' 10; 'External_ABC' 10; 'Inrush_Loaded' 10}, {'Internal_AB' 10; 'Internal_ABC' 10; 'InternalHV_AB' 10}};
names = {ST.name}; plan = []; blockOf = [];
for r = 1:size(L, 1)
    for g = 2:3
        for q = 1:size(L{r, g}, 1)
            ix = find(strcmp(names, L{r, g}{q, 1}));
            assert(isscalar(ix), 'GenV4:OOD', 'OOD scenario %s not in the scenario table', L{r, g}{q, 1});
            plan = [plan, repmat(ix, 1, L{r, g}{q, 2})]; %#ok<AGROW>
            blockOf = [blockOf, repmat(L{r, 1}, 1, L{r, g}{q, 2})]; %#ok<AGROW>
        end
    end
end
counts = histcounts(plan, 0.5:1:numel(ST) + 0.5);
end

function L = closedLoopCases(ST, cfg)
% D3: 12 hand-specified cases. Each starts from a seeded random draw (noise, CT mismatch, noise seeds) and then fixes the parameters that define the case.
pick = @(n) ST(strcmp({ST.name}, n));
spec = {
 % label,                              scenario,               pct,  extra overrides (struct)
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
    p.noisePct = 0.3; p.pf = 0.9; p.srcScale = 1.0; p.srcZScale = 1; p.freq = 50; p.ctBurden = 1.5;
    if any(strcmp(sc.kind, {'ct_stress_ext', 'ct_stress_int'})), p.noisePct = 1.5; end
    if strcmp(sc.kind, 'overexc'), p.srcScale = 1.15; end
    p.loadPu = spec{k, 3} / 100; p.loadKnob = load_knob_for(spec{k, 3}, p.pf);
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
% Runs each case through Simulink WITH THE LSTM ACTIVE and records the relay's own trip decision ('Dec_Trip_Signal').
% The breakers are disconnected from the relay (External off) in this generator, so the decision is logged but does not alter the plant.
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
                         findBlock(model, 'Internal_Fault3'), findBlock(model, 'External_Fault'), findBlock(model, 'Internal_Fault_HV'), findBlock(model, 'External_Fault_HV')}, ...
                 'step', {findBlock(model, 'Step3'), findBlock(model, 'Step_Evolve2'), ...
                          findBlock(model, 'Step_Evolve3'), findBlock(model, 'Step4'), findBlock(model, 'Step_HV'), findBlock(model, 'Step_ExtHV')});   % 5 = HV-side internal (A5), 6 = HV-bus external (A6)
B.nmu   = findBlock(model, 'Noise Merging Unit');
B.blwn  = findBlock(B.nmu, 'Band-Limited White Noise');
for k = 1:6
    B.noiseGain{k} = findBlock(B.nmu, sprintf('Noise_Gain_%d', k));
    B.ctGain{k}    = findBlock(B.nmu, sprintf('CT_Gain_Mismatch_%d', k));
end
B.relay = findBlock(model, 'Hybrid 87T Relay');
B.srcZ  = findBlock(model, 'Three-Phase Series RLC Branch');   % source impedance (0.1 ohm + 1 mH), scaled per trace (A7)
B.priV  = findBlock(model, 'Primary_side');     % V-I measurement: TRUE HV line current (for the CT ratio-error check)
B.secV  = findBlock(model, 'Secondary_side');   % V-I measurement: TRUE LV line current
ctNames = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'};
for k = 1:6
    B.ctBurden{k} = findBlock(findBlock(model, ctNames{k}), '1ohm');     % burden resistor of each CT subsystem (1 ohm nominal)
end
end

function blk = findBlock(parent, name)
% Exact block under `parent` (one level), comparing names with whitespace/newlines normalised.
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
normName = @(s) strtrim(regexprep(s, '\s+', ' '));
hit = c(strcmp(cellfun(@(s) normName(get_param(s, 'Name')), c, 'UniformOutput', false), normName(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'GenV4:Block', 'Expected exactly one block "%s" under %s, found %d.', name, parent, numel(hit));
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
            'GenV4:SetParam', '%s: %s should be "%s" but is "%s".', blk, varargin{k}, want, got);
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
        warning('GenV4:Diag', 'Could not set %s (%s); the log will just be longer.', m{1}, ME.message);
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
% 5) Log the TRUE line currents (V-I measurement out2) to measure the CT ratio error per trace (ctRatioErrorMax).
for kk = 1:2
    sideBlk = {B.priV, B.secV}; nm = {'TruePrimI', 'TrueSecI'};
    pp = get_param(sideBlk{kk}, 'PortHandles');
    set_param(pp.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', nm{kk});
end
end

function applyScenario(B, sc, p, cfg)
% --- faults: everything off, every step far in the future
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
    case 'overexc'                                      % healthy, source voltage 1.15-1.45 pu from t = 0 (core saturates above ~1.25 pu): 5th harmonic
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
    case 'recovery_inrush'                              % 3-phase fault on the 230 kV bus (outside the CT zone), cleared by its own switching times
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        setp(B.fault(6).blk, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off', 'FaultResistance', sprintf('%.6g', p.Rf), ...
            'External', 'off', 'SwitchTimes', sprintf('[%.6f %.6f]', p.tFault, p.faultClear));
    case 'internal_hv'                                  % fault on the 230 kV winding terminals, inside the HV CT zone (A5)
        breakersClosed(B); setp(B.xf, 'SetInitialFlux', 'off');
        armFault(B, 5, [sc.fA sc.fB sc.fC sc.fG], p.Rf, p.tFault);
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
        error('GenV4:Kind', 'Unknown scenario kind %s', sc.kind);
end

% --- load (constant-Z, rated 11 kV) and source
S = p.loadKnob * cfg.Srated;
setp(B.load, 'ActivePower', sprintf('%.6g', S * p.pf), ...
             'InductivePower', sprintf('%.6g', max(S * sqrt(max(1 - p.pf ^ 2, 0)), 1)), 'CapacitivePower', '0');
amp = sprintf('%.6g', p.srcScale * 230e3 * sqrt(2) / sqrt(3));
ph0 = [0 -120 120];
for k = 1:3
    setp(B.vs{k}, 'Amplitude', amp, 'Phase', sprintf('%.6g', p.srcPhase + ph0(k)), 'Frequency', sprintf('%.6g', p.freq));
end
setp(B.srcZ, 'Resistance', sprintf('%.6g', cfg.srcZ0(1) * p.srcZScale), 'Inductance', sprintf('%.6g', cfg.srcZ0(2) * p.srcZScale));

% --- CT burden (x nominal 1 ohm, same on all six CTs); remanence cannot be modelled (flux decays in ~25 ms)
for k = 1:6
    setp(B.ctBurden{k}, 'Resistance', sprintf('%.6g', p.ctBurden));
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
             'faultDiffPu', NaN, 'extFaultPu', NaN, 'loadRealisedPct', NaN, 'loadOK', NaN, 'ctRatioErrorMax', NaN, 'harm5Ratio', NaN, 'diffRmsPu', NaN, 'recDiffPeakPu', NaN, 'recH2', NaN, 'fingerprint', '', 'checkPassed', 0, 'message', '');
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
        tol = cfg.timingTol;
        if any(strcmp(sc.kind, {'fault_in_inrush', 'ext_in_inrush'})), tol = 0.030; end   % the fault edge is masked by the inrush it lands in (v2: 84 % passed at 12.5 ms)
        rec.timingOK = double(abs(rec.eventDetected - p.tEvent) <= tol);
    else
        rec.timingOK = NaN;
    end
end
% Recovery inrush: the event is the voltage recovery, which builds over a cycle, so the sharp-edge timing test does not apply. Instead the
% HV-bus fault must visibly reduce the HV current while it is on (constant-impedance load follows the dipped voltage).
if strcmp(sc.kind, 'recovery_inrush')
    rb = mean(sqrt(mean(Ip(t >= p.tFault - 0.04 & t <= p.tFault - 0.005, :) .^ 2, 1)));
    rd = mean(sqrt(mean(Ip(t >= p.tFault + 0.012 & t <= p.faultClear - 0.005, :) .^ 2, 1)));
    hvDipRatio = rd / max(rb, eps);
    rec.timingOK = double(hvDipRatio < 0.85);
    rec.eventVisible = rec.timingOK;
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
if any(strcmp(sc.kind, {'normal', 'overexc'})), healthy = t > 0.12 & t < 1.0; end
if startsWith(sc.kind, 'inrush') || any(strcmp(sc.kind, {'sotf', 'fault_in_inrush', 'ext_in_inrush'})), healthy = false(size(t)); end
if any(healthy)
    q2 = cfg.quantStep ^ 2 / 12;                                  % quantisation noise per channel
    sp = p.noisePct / 100 * cfg.Inom(1:3); ss = p.noisePct / 100 * cfg.Inom(4:6);
    rec.noiseExpected = median(sqrt(2 * (sp .^ 2 + ss .^ 2 + 2 * q2)));
    seg = d(healthy, :); seg32 = seg(33:end, :) - seg(1:end - 32, :);
    rec.noiseMeasured = median(std(seg32));
    resid = 2 * abs(sin(pi * p.freq * 32 / fs)) * sqrt(mean(seg(:) .^ 2));      % |x(t) - x(t - 20 ms)| of a periodic component at f != 50 Hz
    if strcmp(sc.kind, 'overexc'), resid = 2 * max(abs(sin(pi * (1:7) * p.freq * 32 / fs))) * sqrt(mean(seg(:) .^ 2)); end   % saturated core: harmonics 1-7 leak more at f != 50 Hz
    rec.noiseOK = double(rec.noiseMeasured > 0.5 * rec.noiseExpected && rec.noiseMeasured < 2 * rec.noiseExpected + 0.01 + resid);
end

% realised load (% of rated CT-secondary current) on a healthy, settled stretch with the load connected
loadWin = [];
if any(strcmp(sc.kind, {'internal', 'internal_hv', 'external', 'ct_stress_int', 'ct_stress_ext', 'evolving'}))
    loadWin = t > 0.12 & t < min(p.tEvent - 0.03, 0.28);
elseif any(strcmp(sc.kind, {'normal', 'overexc'}))
    loadWin = t > 0.12 & t < 1.0;
elseif strcmp(sc.kind, 'recovery_inrush')
    loadWin = t > 0.12 & t < 0.28;
end
if any(loadWin)
    % TRUE line currents (V-I measurement blocks): independent of CT saturation / burden / mismatch
    lsg0 = out.get('logsout');
    [iP0, tP0] = loggedSignal(lsg0, 'TruePrimI'); [iS0, ~] = loggedSignal(lsg0, 'TrueSecI');
    tHi = t(find(loadWin, 1, 'first')); tLo = t(find(loadWin, 1, 'last'));
    wT = tP0 >= tHi & tP0 <= tLo;
    pH = mean(sqrt(mean(iP0(wT, :) .^ 2, 1))) / 753.06; pL = mean(sqrt(mean(iS0(wT, :) .^ 2, 1))) / 15745.9;
    rec.loadRealisedPct = 100 * 0.5 * (pH + pL);
    if strcmp(sc.kind, 'overexc'), rec.loadRealisedPct = 100 * pL; end      % HV current includes the saturated core's magnetising current
    target = 100 * p.loadPu * p.srcScale;                         % constant-impedance load: current follows the source voltage
    rec.loadOK = double(abs(rec.loadRealisedPct - target) <= max(cfg.loadTolPct / 100 * target, 2));
end

% detectability: rise of the relay's compensated differential (per unit) one cycle after the event
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

% CT ratio error (%): RMS(N*I_ct - I_true)/RMS(I_true) over 5-45 ms after the event, max over the six channels (HV and LV).
% >10 % = the CT visibly saturates / distorts. NaN when there is no event or the true current is below 2 % of rated.
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
            ok = [rP rS] > 0.02 * [753.06 * ones(1, 3), 15745.9 * ones(1, 3)];
            if any(ok), e = [eP eS]; rec.ctRatioErrorMax = 100 * max(e(ok)); end
        end
    end
catch
end

% harmonic signatures of the plant-compensated differential d = Is - Ip*M (the LSTM input): over-excitation (5th) and recovery inrush (2nd)
Mpl = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
dpl = Is - Ip * Mpl;
dft = @(i0) abs(fft(dpl(i0:i0 + 31, :), [], 1));                  % 32-point DFT: bin 2 = 50 Hz, 3 = 100 Hz, 6 = 250 Hz
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

% duplicate waveform?
md = java.security.MessageDigest.getInstance('SHA-1');
md.update(typecast([Ip(:); Is(:)], 'int8'));
rec.fingerprint = lower(reshape(dec2hex(typecast(md.digest(), 'uint8'))', 1, []));
rec.duplicate = double(fingerprints.isKey(rec.fingerprint));

rec.checkPassed = double(rec.timingOK ~= 0 && rec.duplicate == 0 && rec.noiseOK ~= 0);   % NaN counts as not-failed
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
         'noiseOK', 'duplicate', 'faultDiffPu', 'extFaultPu', 'loadRealisedPct', 'loadOK', 'ctRatioErrorMax', 'harm5Ratio', 'diffRmsPu', 'recDiffPeakPu', 'recH2', 'checkPassed', 'loadKnob', 'ctBurden', 'loadBin', 'angleBin', 'fluxBin', 'hizBin', 'sourceZScale', 'frequencyHz', 'oodBlock'}
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
f = fullfile(dir, sprintf('StressDataset_v4%s_%s_PARTIAL.mat', fileTag, runId));
end

% =====================================================================================
% Self-test: 5 cases, prints the checks, saves nothing
% =====================================================================================
function runSelfTest(model, B, ST, cfg, range)
names = {'Normal', 'Internal_AB', 'Internal_HiZ_AB', 'Internal_AG', 'Inrush_NoLoad', 'Inrush_Loaded', 'External_ABC', 'Internal_SOTF_AB', 'Internal_Evolving', ...
         'Stress_ExtCTSat_ABC', 'Stress_ExtCTSat_AG', 'Stress_CTSat_Int_AB', 'InternalHV_AG', 'InternalHV_AB', 'Overexcitation', 'Recovery_Inrush', ...
         'Stress_FaultInInrush', 'Stress_ExtInInrush'};          % one case per scenario kind (18)
if isempty(range), range = [1 numel(names)]; end
sel = range(1):min(range(2), numel(names));
fprintf('\n=== SELF-TEST (nothing is saved) ===\n');
fprintf('Expect: AB / HiZ_AB / SOTF visible and timed; Internal_AG on the delta winding: visible 0, faultDiff ~0.\n');
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
    fprintf('SELF-TEST PASSED. Run: run_stress_v4_generate.bat 3040\n');
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
