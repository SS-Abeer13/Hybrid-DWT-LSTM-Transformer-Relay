%% =========================================================================
%% COMBINE DATASETS  +  EXTRACT DWT FEATURES  (single-pass script)
%% =========================================================================
%
% PURPOSE
%   Merges ALL raw dataset files found in the current directory AND in any
%   'datasets' subfolder, then runs a full 2-level db4 wavelet feature
%   extraction to produce one ready-to-train LSTM feature file.
%
%   Handles three source types automatically:
%     StressTestDataset_*.mat        — ControlPanel_StressTest (full distribution)
%     StressTestDataset_TOPUP_*.mat  — ControlPanel_StressTest_Topup (gap-fill)
%     TransformerProtection_Dataset_*— ControlPanel2 / ControlPanel3 (legacy)
%     InrushDataset_*.mat            — ControlPanel_Inrush (inrush only)
%
%   TOPUP files are matched first so they get the correct type tag even
%   though their name also matches the wider StressTestDataset_*.mat glob.
%
% OUTPUT
%   LSTM_Features_Combined_YYYYMMDD_HHMMSS.mat
%
%   Variables:
%     X_LSTM   (N, T, 9)   float64, log1p-normalised DWT energies
%     Y_LSTM   (N,)        binary  0=NoTrip  1=Trip
%     Y_class  (N,)        5-class 1=Normal 2=Inrush 3=Internal
%                                  4=External 5=Unknown
%     metadata             struct  — ALL per-sample parameters for analysis
%
%   metadata fields (one value per valid sample):
%     .zone              cell   — 'Normal'/'Inrush'/'Internal'/'External'
%     .faultType         cell   — 'AG','BG','ABG',...,'None'
%     .scenarioName      cell   — full scenario tag e.g. 'Internal_HiZ_ABG'
%     .shouldTrip        logical
%     .faultResistance   double — Ω  (0 for Normal/Inrush)
%     .inceptionAngle    double — degrees  (0 for Normal)
%     .inceptionTime     double — seconds  (fault or energisation time)
%     .energisationTime  double — seconds  (inrush samples)
%     .noiseLevel        double — fraction (0.003–0.25)
%     .ctMismatch        cell   — [6×1] gain vector per sample
%     .secondaryMode     cell   — 'noload'/'loaded'/'none'
%     .simulationStatus  cell   — 'Success' / 'Failed: ...'
%     .isHiZ             logical — Rf > 10 Ω  (high-impedance fault)
%     .isStress          logical — CT-sat, evolving, or fault-during-inrush
%     .isEvolving        logical — evolving-fault scenario
%     .isFaultInInrush   logical — internal fault superimposed on inrush
%     .isExtInInrush     logical — external fault during inrush (no-trip)
%     .classLabel        double  — same as Y_class
%     .binaryLabel       double  — same as Y_LSTM
%     .extractionConfig  struct  — wavelet / window parameters
%
%% =========================================================================

clear; clc; close all;

disp('╔═══════════════════════════════════════════════════════════╗');
disp('║   COMBINE DATASETS  +  EXTRACT DWT FEATURES              ║');
disp('╚═══════════════════════════════════════════════════════════╝');
disp(' ');

%% ═══════════════════════════════════════════════════════════════════════
%% 1.  FIND ALL RAW DATASET FILES
%% ═══════════════════════════════════════════════════════════════════════

searchPaths = {pwd};
datasetSubdir = fullfile(pwd, 'datasets');
if isfolder(datasetSubdir)
    searchPaths{end+1} = datasetSubdir;
end

% Column 1: glob pattern   Column 2: human-readable type tag
% IMPORTANT: TOPUP pattern must come BEFORE the wider StressTestDataset_* pattern
% so TOPUP files are correctly tagged and not double-counted.
patterns = {
    'StressTestDataset_TOPUP_*.mat',      'StressTest-TOPUP (gap-fill)';
    'StressTestDataset_*.mat',            'StressTest (ControlPanel_StressTest)';
    'TransformerProtection_Dataset_*.mat','Mixed (ControlPanel2/3)';
    'InrushDataset_*.mat',                'Inrush (ControlPanel_Inrush)';
};

foundFiles = struct('path',{}, 'type',{}, 'datenum',{});
seenPaths  = {};   % duplicate guard

for sp = 1:numel(searchPaths)
    for k = 1:size(patterns,1)
        hits = dir(fullfile(searchPaths{sp}, patterns{k,1}));
        for h = 1:numel(hits)
            fpath = fullfile(hits(h).folder, hits(h).name);
            % Skip if already added by an earlier (more specific) pattern
            if any(strcmp(seenPaths, fpath)), continue; end
            e.path    = fpath;
            e.type    = patterns{k,2};
            e.datenum = hits(h).datenum;
            foundFiles(end+1) = e; %#ok<AGROW>
            seenPaths{end+1}  = fpath; %#ok<AGROW>
        end
    end
end

if isempty(foundFiles)
    error(['No dataset files found.\nSearched:\n  %s\n\n' ...
           'Generate data with ControlPanel_StressTest first.'], ...
           strjoin(searchPaths, '\n  '));
end

% Sort newest first within each type, but keep TOPUP files listed last
% (they are additive top-ups, so visually grouped after the base batches)
[~, si] = sort([foundFiles.datenum], 'descend');
foundFiles = foundFiles(si);

fprintf(' Files found (%d):\n', numel(foundFiles));
nBase  = sum(contains({foundFiles.type}, 'StressTest ('));
nTopup = sum(contains({foundFiles.type}, 'TOPUP'));
nLeg   = numel(foundFiles) - nBase - nTopup;
fprintf('   Base batches  : %d file(s)\n', nBase);
fprintf('   Top-up batches: %d file(s)\n', nTopup);
if nLeg > 0, fprintf('   Legacy batches: %d file(s)\n', nLeg); end
fprintf('\n');
for k = 1:numel(foundFiles)
    fprintf('   [%d] %-46s\n       → %s\n', k, foundFiles(k).type, foundFiles(k).path);
end
disp(' ');

%% ═══════════════════════════════════════════════════════════════════════
%% 2.  LOAD AND MERGE ALL DATASETS
%% ═══════════════════════════════════════════════════════════════════════

disp(' Merging datasets...');
combined      = [];
perFileStats  = struct('file',{},'type',{},'nRaw',{},'nValid',{});

for k = 1:numel(foundFiles)
    [~, fname, fext] = fileparts(foundFiles(k).path);
    shortName = [fname fext];
    fprintf('   Loading [%d/%d] %s ...\n', k, numel(foundFiles), shortName);
    try
        raw = load(foundFiles(k).path, 'dataset');
        if ~isfield(raw,'dataset')
            warning('   No ''dataset'' variable — skipping: %s', shortName);
            continue;
        end
        ds = raw.dataset;
    catch ME
        warning('   Load failed: %s — skipping. (%s)', shortName, ME.message);
        continue;
    end

    n = numel(ds.zone);
    fprintf('     %d samples  |  type: %s\n', n, foundFiles(k).type);

    % ── Tag source file and batch type on every sample ───────────────────
    if ~isfield(ds,'scenarioName') || isempty(ds.scenarioName{1})
        ds.scenarioName = repmat({'(legacy)'}, n, 1);
    end
    % sourceFile: short filename for provenance tracking
    ds.sourceFile  = repmat({shortName},          n, 1);
    % batchType:  'base' | 'topup' | 'legacy' — for analysis grouping
    if contains(foundFiles(k).type,'TOPUP')
        btype = 'topup';
    elseif contains(foundFiles(k).type,'StressTest')
        btype = 'base';
    else
        btype = 'legacy';
    end
    ds.batchType   = repmat({btype}, n, 1);

    % ── Quick per-file valid count (simulationStatus check) ───────────────
    if isfield(ds,'simulationStatus')
        nV = sum(strcmp(ds.simulationStatus,'Success'));
    else
        nV = sum(cellfun(@(x) ~isempty(x), ds.primaryCurrent));
    end
    st.file   = shortName;
    st.type   = foundFiles(k).type;
    st.nRaw   = n;
    st.nValid = nV;
    perFileStats(end+1) = st; %#ok<AGROW>
    fprintf('     Valid: %d / %d (%.0f%%)\n', nV, n, nV/n*100);

    if isempty(combined)
        combined = ds;
    else
        combined = mergeDatasets(combined, ds);
    end
end

if isempty(combined)
    error('No valid dataset structs loaded. Aborting.');
end

numSamples = numel(combined.zone);
disp(' ');
disp(' Merged dataset summary:');
fprintf('   Total samples : %d\n', numSamples);
fprintf('   Normal        : %d\n', sum(strcmp(combined.zone,'Normal')));
fprintf('   Inrush        : %d\n', sum(strcmp(combined.zone,'Inrush')));
fprintf('   Internal      : %d\n', sum(strcmp(combined.zone,'Internal')));
fprintf('   External      : %d\n', sum(strcmp(combined.zone,'External')));
fprintf('   shouldTrip=1  : %d\n', sum(combined.shouldTrip));
fprintf('   shouldTrip=0  : %d\n', sum(~combined.shouldTrip));

% ── Per-file contribution table ─────────────────────────────────────────
fprintf('\n   Per-file contribution:\n');
fprintf('   %-42s  %-28s  %6s  %6s  %5s\n', ...
        'File','Type','Raw','Valid','OK%');
fprintf('   %s\n', repmat('-',1,95));
for k = 1:numel(perFileStats)
    pct = perFileStats(k).nValid / max(perFileStats(k).nRaw,1) * 100;
    fprintf('   %-42s  %-28s  %6d  %6d  %4.0f%%\n', ...
            perFileStats(k).file, perFileStats(k).type, ...
            perFileStats(k).nRaw, perFileStats(k).nValid, pct);
end
fprintf('   %s\n', repmat('-',1,95));

% ── Per-scenario breakdown ───────────────────────────────────────────────
if isfield(combined,'scenarioName') && ~isempty(combined.scenarioName)
    uScen = unique(combined.scenarioName);
    uScen = uScen(~cellfun(@isempty, uScen));
    fprintf('\n   Per-scenario raw counts (before validity filter) — %d types:\n', numel(uScen));
    for s = 1:numel(uScen)
        cnt = sum(strcmp(combined.scenarioName, uScen{s}));
        fprintf('     %-35s : %d\n', uScen{s}, cnt);
    end
end

if isempty(combined.primaryCurrent{1})
    error('Primary current is empty in first sample. Check simulation outputs.');
end
[numSteps, numPhases] = size(combined.primaryCurrent{1});
fprintf('\n   Time steps / sample : %d\n', numSteps);
fprintf('   Phases              : %d\n\n', numPhases);

%% ═══════════════════════════════════════════════════════════════════════
%% 3.  FEATURE EXTRACTION CONFIGURATION  (2-level db4, 32-sample window)
%% ═══════════════════════════════════════════════════════════════════════

WindowSize   = 32;                    % 1 cycle @ 1600 Hz (50 Hz × 32 = 20 ms)
nLevels      = 2;
wname        = 'db4';
numFeatures  = numPhases * 3;         % 9 = [E_D1, E_D2, E_A2] × 3 phases
numTimeSteps = numSteps - WindowSize; % 1601 - 32 = 1569

featureNames = {'E_D1_A','E_D2_A','E_A2_A', ...
                'E_D1_B','E_D2_B','E_A2_B', ...
                'E_D1_C','E_D2_C','E_A2_C'};

disp(' Feature extraction settings:');
fprintf('   Wavelet       : %s  (Daubechies-4)\n', wname);
fprintf('   Window size   : %d samples  (1 cycle @ 1600 Hz)\n', WindowSize);
fprintf('   Decomp levels : %d  →  D1(400-800 Hz) D2(200-400 Hz) A2(0-200 Hz)\n', nLevels);
fprintf('   Features/step : %d\n', numFeatures);
fprintf('   Time steps    : %d\n\n', numTimeSteps);

%% ═══════════════════════════════════════════════════════════════════════
%% 4.  VALIDATE SAMPLES
%% ═══════════════════════════════════════════════════════════════════════

validMask = true(numSamples,1);
for i = 1:numSamples
    ok = ~isempty(combined.primaryCurrent{i}) && ...
         ~isempty(combined.secondaryCurrent{i});
    if ok
        % Also check simulation was successful
        if isfield(combined,'simulationStatus') && ...
           ~isempty(combined.simulationStatus{i}) && ...
           ~strcmp(combined.simulationStatus{i},'Success')
            ok = false;
        end
    end
    validMask(i) = ok;
end
numValid = sum(validMask);

nFailed = numSamples - numValid;
if nFailed > 0
    warning('%d / %d samples skipped (empty waveforms or failed simulation).', ...
            nFailed, numSamples);
end
fprintf('   Valid samples : %d / %d  (%.1f%% success)\n\n', ...
        numValid, numSamples, numValid/numSamples*100);

% ── Per-scenario failure rate diagnostic ─────────────────────────────────
if nFailed > 0 && isfield(combined,'scenarioName')
    fprintf('── Per-scenario failure analysis ──\n');
    uScen = unique(combined.scenarioName);
    uScen = uScen(~cellfun(@isempty, uScen));
    anyFail = false;
    for s = 1:numel(uScen)
        sc      = uScen{s};
        scMask  = strcmp(combined.scenarioName, sc);
        total   = sum(scMask);
        nFail_s = sum(scMask & ~validMask);
        if nFail_s > 0
            failPct = nFail_s / total * 100;
            flag    = '';
            if failPct >= 50, flag = '  ← HIGH FAILURE'; end
            if failPct >= 75, flag = '  ← CRITICAL'; end
            fprintf('  %-35s : %3d / %3d failed (%5.1f%%)%s\n', ...
                    sc, nFail_s, total, failPct, flag);
            anyFail = true;
        end
    end
    if ~anyFail
        fprintf('  All scenarios: 0 failures\n');
    end
    fprintf('\n  Root cause hints:\n');
    fprintf('  1. If Internal_Fault2/3 scenarios dominate: resetFaultBlocks\n');
    fprintf('     was arming FaultB/FaultC — update ControlPanel_StressTest.m\n');
    fprintf('     (set all phases OFF in resetFaultBlocks).\n');
    fprintf('  2. If HiZ scenarios dominate: reduce max Rf to 200 Ohm or\n');
    fprintf('     increase solver iteration limit in powergui.\n');
    fprintf('  3. If Evolving scenarios dominate: check Step_Evolve2/3\n');
    fprintf('     are set to Time=10 before each non-evolving simulation.\n');
    fprintf('\n');
end

%% ═══════════════════════════════════════════════════════════════════════
%% 5.  PREALLOCATE OUTPUT TENSORS
%% ═══════════════════════════════════════════════════════════════════════

X_LSTM  = zeros(numValid, numTimeSteps, numFeatures, 'single');
Y_LSTM  = zeros(numValid, 1);
Y_class = zeros(numValid, 1);

%% ═══════════════════════════════════════════════════════════════════════
%% 6.  MAIN EXTRACTION LOOP
%% ═══════════════════════════════════════════════════════════════════════

disp(' Starting feature extraction...');
wb = waitbar(0,'Extracting wavelet features...','Name','CombineAndExtract');
tic;

validIdx = 0;
validOrigIdx = zeros(numValid,1);  % map validIdx → original sample index

for i = 1:numSamples

    if ~validMask(i), continue; end

    Ip = combined.primaryCurrent{i};
    Is = combined.secondaryCurrent{i};

    if size(Ip,1) ~= numSteps || size(Is,1) ~= numSteps
        warning('Sample %d: wrong shape (%d rows) — skipping.', i, size(Ip,1));
        continue;
    end

    validIdx = validIdx + 1;
    validOrigIdx(validIdx) = i;

    if mod(validIdx,50)==0 || validIdx==1
        el  = toc;
        eta = (el/validIdx)*(numValid-validIdx);
        waitbar(validIdx/numValid, wb, ...
                sprintf('Sample %d/%d  |  ETA %.0fs', validIdx, numValid, eta));
    end

    % ── Differential current ─────────────────────────────────────────────
    if isfield(combined,'diffCurrent') && ~isempty(combined.diffCurrent{i})
        I_diff = combined.diffCurrent{i};
    else
        I_diff = Ip - Is;
    end

    % ── Sliding-window 2-level DWT ────────────────────────────────────────
    for t = (WindowSize+1) : numSteps
        outIdx     = t - WindowSize;
        sig_window = I_diff((t-WindowSize+1):t, :);   % [32 × 3]

        feat = zeros(1, numFeatures);
        for ph = 1:numPhases
            [C,L]    = wavedec(sig_window(:,ph), nLevels, wname);
            E_D1     = sum(detcoef(C,L,1).^2);
            E_D2     = sum(detcoef(C,L,2).^2);
            E_A2     = sum(appcoef(C,L,wname,2).^2);
            base     = (ph-1)*3 + 1;
            feat(base)   = E_D1;
            feat(base+1) = E_D2;
            feat(base+2) = E_A2;
        end
        X_LSTM(validIdx, outIdx, :) = feat;
    end

    % ── Labels ───────────────────────────────────────────────────────────
    Y_LSTM(validIdx)  = double(combined.shouldTrip(i));
    Y_class(validIdx) = zoneToClass(combined.zone{i});
end

close(wb);
processingTime = toc;

% Trim to actual rows written
X_LSTM         = X_LSTM(1:validIdx,:,:);
Y_LSTM         = Y_LSTM(1:validIdx);
Y_class        = Y_class(1:validIdx);
validOrigIdx   = validOrigIdx(1:validIdx);

fprintf('\n✓ Extraction complete in %.1f s  (%d samples)\n\n', processingTime, validIdx);

%% ═══════════════════════════════════════════════════════════════════════
%% 7.  LOG1P NORMALISATION
%% ═══════════════════════════════════════════════════════════════════════

disp(' Applying log1p normalisation...');
X_LSTM = log1p(double(X_LSTM));
disp('   ✓ Done.');

%% ═══════════════════════════════════════════════════════════════════════
%% 8.  TENSOR VALIDATION
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp(' Validation:');
fprintf('   Tensor shape  : [%d, %d, %d]\n', size(X_LSTM,1), size(X_LSTM,2), size(X_LSTM,3));

if size(X_LSTM,2)~=numTimeSteps || size(X_LSTM,3)~=numFeatures
    error('Dimension mismatch — expected [N,%d,%d].', numTimeSteps, numFeatures);
end
disp('   ✓ Dimensions correct');

if any(isnan(X_LSTM(:))) || any(isinf(X_LSTM(:)))
    warning('⚠ Tensor contains NaN/Inf — check simulation outputs.');
else
    disp('   ✓ No NaN / Inf values');
end

disp(' ');
disp(' Label distribution:');
fprintf('   Trip  (1) : %d\n', sum(Y_LSTM==1));
fprintf('   No-Trip(0): %d\n', sum(Y_LSTM==0));
fprintf('   Positive rate : %.1f%%\n', mean(Y_LSTM)*100);
disp(' ');
disp(' 5-class distribution:');
classNames = {'Normal','Inrush','Internal','External','Unknown'};
for c = 1:5
    n = sum(Y_class==c);
    if n > 0
        fprintf('   %s (%d) : %d  (%.1f%%)\n', classNames{c}, c, n, n/validIdx*100);
    end
end

%% ═══════════════════════════════════════════════════════════════════════
%% 9.  BUILD FULL METADATA STRUCT
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp(' Building metadata...');

vi = validOrigIdx;   % shorthand

metadata = struct();

% ── Core per-sample identification ──────────────────────────────────────
metadata.zone             = combined.zone(vi);
metadata.faultType        = getCellField(combined, 'faultType',    vi);
metadata.scenarioName     = getCellField(combined, 'scenarioName', vi);
metadata.simulationStatus = getCellField(combined, 'simulationStatus', vi);

% ── Electrical parameters ────────────────────────────────────────────────
metadata.shouldTrip        = logical(combined.shouldTrip(vi));
metadata.faultResistance   = getNumField(combined, 'faultResistance',  vi);
metadata.inceptionAngle    = getNumField(combined, 'inceptionAngle',   vi);
metadata.inceptionTime     = getNumField(combined, 'inceptionTime',    vi);
metadata.energisationTime  = getNumField(combined, 'energisationTime', vi);
metadata.noiseLevel        = getNumField(combined, 'noiseLevel',       vi);

% ── CT mismatch — store as cell of [6×1] vectors ─────────────────────────
if isfield(combined,'ctMismatch') && ~isempty(combined.ctMismatch)
    metadata.ctMismatch = combined.ctMismatch(vi);
else
    metadata.ctMismatch = repmat({ones(6,1)}, numel(vi), 1);
end

% ── Secondary mode (noload / loaded / none) ──────────────────────────────
metadata.secondaryMode = getCellField(combined, 'secondaryMode', vi);

% ── Dataset provenance — which file and batch type each sample came from ──
metadata.sourceFile = getCellField(combined, 'sourceFile', vi);
metadata.batchType  = getCellField(combined, 'batchType',  vi);

% ── Derived flags for parameter-wise analysis ────────────────────────────
Rf   = metadata.faultResistance;
scen = metadata.scenarioName;

metadata.isHiZ          = logical(Rf > 10);
metadata.isStress       = cellfun(@(s) ...
    ~isempty(regexpi(s,'CTSat|Evolving|InInrush','once')), scen);
metadata.isEvolving     = cellfun(@(s) ...
    ~isempty(regexpi(s,'Evolv','once')), scen);
metadata.isFaultInInrush= cellfun(@(s) ...
    ~isempty(regexpi(s,'FaultInInrush','once')), scen);
metadata.isExtInInrush  = cellfun(@(s) ...
    ~isempty(regexpi(s,'ExtInInrush','once')), scen);

% ── Mirrored labels (for convenience in Python analysis) ─────────────────
metadata.binaryLabel = Y_LSTM;
metadata.classLabel  = Y_class;

% ── CT mismatch summary per sample (mean of 6 channels) ─────────────────
metadata.ctMismatchMean = cellfun(@(v) ...
    mean(double(v(:))), metadata.ctMismatch);

% ── Extraction configuration ─────────────────────────────────────────────
metadata.extractionConfig.windowSize      = WindowSize;
metadata.extractionConfig.nLevels         = nLevels;
metadata.extractionConfig.waveletName     = wname;
metadata.extractionConfig.samplingRate_Hz = 1600;
metadata.extractionConfig.features        = featureNames;
metadata.extractionConfig.freqBands       = struct( ...
    'D1_Hz','400-800', 'D2_Hz','200-400', 'A2_Hz','0-200');
metadata.extractionConfig.normalization   = 'log1p';
metadata.extractionConfig.tensorShape     = ...
    sprintf('[%d, %d, %d]', validIdx, numTimeSteps, numFeatures);
metadata.extractionConfig.extractedDate   = datetime('now');
metadata.extractionConfig.sourceFiles     = {foundFiles.path};

% ── Class mapping ────────────────────────────────────────────────────────
metadata.classMap = struct('class1','Normal',  'class2','Inrush', ...
                            'class3','Internal','class4','External', ...
                            'class5','Unknown');

% ── Dataset-level statistics ─────────────────────────────────────────────
metadata.stats.nTotal        = validIdx;
metadata.stats.nTrip         = sum(metadata.shouldTrip);
metadata.stats.nNoTrip       = sum(~metadata.shouldTrip);
metadata.stats.posWeight     = sum(~metadata.shouldTrip) / max(sum(metadata.shouldTrip),1);
metadata.stats.nHiZ          = sum(metadata.isHiZ);
metadata.stats.nStress       = sum(metadata.isStress);
metadata.stats.nEvolving     = sum(metadata.isEvolving);
metadata.stats.nFaultInInrush= sum(metadata.isFaultInInrush);
metadata.stats.nExtInInrush  = sum(metadata.isExtInInrush);
metadata.stats.RfMin         = min(Rf(Rf>0));
metadata.stats.RfMax         = max(Rf);
metadata.stats.noiseLevelMin = min(metadata.noiseLevel);
metadata.stats.noiseLevelMax = max(metadata.noiseLevel);

fprintf('   ✓ Metadata built  (%d fields at sample level)\n', ...
        numel(fieldnames(metadata)) - 3);  % exclude config/classMap/stats

%% ═══════════════════════════════════════════════════════════════════════
%% 10.  METADATA VERIFICATION REPORT
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp('╔══════════════════════════════════════════════════════════╗');
disp('║             METADATA VERIFICATION REPORT                ║');
disp('╚══════════════════════════════════════════════════════════╝');
fprintf('  Samples            : %d\n', validIdx);
fprintf('  Trip               : %d  (%.1f%%)\n', ...
        metadata.stats.nTrip, metadata.stats.nTrip/validIdx*100);
fprintf('  No-Trip            : %d  (%.1f%%)\n', ...
        metadata.stats.nNoTrip, metadata.stats.nNoTrip/validIdx*100);
fprintf('  pos_weight (rec.)  : %.4f\n', metadata.stats.posWeight);
fprintf('  HiZ faults (Rf>10Ω): %d\n', metadata.stats.nHiZ);
fprintf('  Stress scenarios   : %d\n', metadata.stats.nStress);
fprintf('  Evolving faults    : %d\n', metadata.stats.nEvolving);
fprintf('  Fault-in-Inrush    : %d\n', metadata.stats.nFaultInInrush);
fprintf('  Ext-in-Inrush      : %d\n', metadata.stats.nExtInInrush);
fprintf('  Rf range           : %.4f – %.1f Ω\n', ...
        metadata.stats.RfMin, metadata.stats.RfMax);
fprintf('  Noise level range  : %.3f – %.3f\n', ...
        metadata.stats.noiseLevelMin, metadata.stats.noiseLevelMax);

% ── Per-scenario sample counts with source breakdown ─────────────────────
fprintf('\n  Per-scenario valid sample counts:\n');
fprintf('  %-35s  %5s  %5s  %5s  %s\n','Scenario','Total','Base','Topup','Flag');
fprintf('  %s\n',repmat('-',1,72));
uScen = unique(metadata.scenarioName);
uScen = uScen(~cellfun(@isempty,uScen));
MIN_SAMPLES = 50;   % minimum per scenario for reliable training
nUnder = 0;
for s = 1:numel(uScen)
    sc    = uScen{s};
    scMsk = strcmp(metadata.scenarioName, sc);
    cnt   = sum(scMsk);
    nBase = sum(scMsk & strcmp(metadata.batchType,'base'));
    nTop  = sum(scMsk & strcmp(metadata.batchType,'topup'));
    flag  = '';
    if cnt < MIN_SAMPLES
        flag = sprintf(' ← LOW (%d < %d)', cnt, MIN_SAMPLES);
        nUnder = nUnder + 1;
    end
    fprintf('  %-35s  %5d  %5d  %5d  %s\n', sc, cnt, nBase, nTop, flag);
end
fprintf('  %s\n',repmat('-',1,72));

% ── Coverage completeness summary ────────────────────────────────────────
fprintf('\n  Coverage completeness:\n');
fprintf('    Scenarios ≥ %d samples : %d / %d\n', MIN_SAMPLES, ...
        numel(uScen)-nUnder, numel(uScen));
if nUnder > 0
    fprintf('    ⚠ %d scenario(s) below threshold — consider running\n', nUnder);
    fprintf('      ControlPanel_StressTest_Topup.m for additional samples.\n');
else
    fprintf('    ✓ All scenarios meet the minimum sample threshold.\n');
end

% ── Batch type contribution summary ──────────────────────────────────────
uTypes = unique(metadata.batchType);
fprintf('\n  Samples by batch type:\n');
for t = 1:numel(uTypes)
    bt = uTypes{t};
    nc = sum(strcmp(metadata.batchType, bt));
    fprintf('    %-10s : %d  (%.1f%%)\n', bt, nc, nc/validIdx*100);
end

%% ═══════════════════════════════════════════════════════════════════════
%% 11.  SAVE
%% ═══════════════════════════════════════════════════════════════════════

disp(' ');
disp(' Saving...');

timestamp      = datestr(now,'yyyymmdd_HHMMSS');
outputFilename = sprintf('LSTM_Features_Combined_%s.mat', timestamp);

save(outputFilename, 'X_LSTM','Y_LSTM','Y_class','metadata', '-v7.3');

disp(' ');
disp('╔═══════════════════════════════════════════════════════════╗');
disp('║                     COMPLETE                             ║');
disp('╚═══════════════════════════════════════════════════════════╝');
fprintf('✅ Saved: %s\n', outputFilename);
fprintf('   X_LSTM  : [%d × %d × %d]  float64, log1p-normalised\n', ...
        size(X_LSTM,1), size(X_LSTM,2), size(X_LSTM,3));
fprintf('   Y_LSTM  : [%d × 1]  binary\n', numel(Y_LSTM));
fprintf('   Y_class : [%d × 1]  5-class\n', numel(Y_class));
disp(' ');
disp(' Python load:');
fprintf('   import scipy.io\n');
fprintf('   d = scipy.io.loadmat(''%s'', simplify_cells=True)\n', outputFilename);
fprintf('   X  = d[''X_LSTM'']        # (%d, %d, %d)\n', ...
        size(X_LSTM,1), size(X_LSTM,2), size(X_LSTM,3));
fprintf('   Y  = d[''Y_LSTM'']        # (%d,)  binary\n',  numel(Y_LSTM));
fprintf('   Yc = d[''Y_class'']       # (%d,)  5-class\n', numel(Y_class));
fprintf('   Rf = d[''metadata''][''faultResistance'']   # per-sample Rf\n');
fprintf('   nl = d[''metadata''][''noiseLevel'']        # per-sample noise\n');
fprintf('   sc = d[''metadata''][''scenarioName'']      # per-sample scenario\n');

%% =========================================================================
%% LOCAL FUNCTIONS
%% =========================================================================

function merged = mergeDatasets(A, B)
%MERGEDATASETS  Concatenate two dataset structs field by field.

    merged = A;

    % All cell fields from either struct
    % sourceFile and batchType are added by the load loop; include here
    cellFields = {'zone','faultType','scenarioName','primaryCurrent', ...
                  'secondaryCurrent','diffCurrent','restCurrent','tripSignal', ...
                  'simulationStatus','ctMismatch','secondaryMode', ...
                  'sourceFile','batchType'};
    for f = 1:numel(cellFields)
        fn = cellFields{f};
        colA = getCellField(A, fn, []);
        colB = getCellField(B, fn, []);
        merged.(fn) = [colA; colB];
    end

    % Numeric fields
    numFields = {'faultResistance','inceptionAngle','inceptionTime', ...
                 'energisationTime','noiseLevel'};
    for f = 1:numel(numFields)
        fn = numFields{f};
        merged.(fn) = [getNumField(A,fn,[]) ; getNumField(B,fn,[])];
    end

    % Logical
    merged.shouldTrip = [logical(A.shouldTrip(:)); logical(B.shouldTrip(:))];
end


function col = getCellField(ds, fn, vi)
%GETCELLFIELD  Extract cell column, optionally indexed by vi.
    if isfield(ds,fn) && ~isempty(ds.(fn))
        c = ds.(fn)(:);
    else
        c = repmat({''}, numel(ds.zone), 1);
    end
    if ~isempty(vi)
        col = c(vi);
    else
        col = c;
    end
end


function vec = getNumField(ds, fn, vi)
%GETNUMFIELD  Extract numeric column, optionally indexed by vi.
    if isfield(ds,fn) && ~isempty(ds.(fn))
        v = double(ds.(fn)(:));
    else
        v = zeros(numel(ds.zone),1);
    end
    if ~isempty(vi)
        vec = v(vi);
    else
        vec = v;
    end
end


function c = zoneToClass(zoneStr)
    switch lower(strtrim(zoneStr))
        case 'normal',   c = 1;
        case 'inrush',   c = 2;
        case 'internal', c = 3;
        case 'external', c = 4;
        otherwise,       c = 5;
    end
end
