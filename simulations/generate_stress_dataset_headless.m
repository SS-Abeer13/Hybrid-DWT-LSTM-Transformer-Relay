function generate_stress_dataset_headless(nSamples, stopTime)
%GENERATE_STRESS_DATASET_HEADLESS Generate dataset headlessly with live console progress.
%
% Usage:
%   generate_stress_dataset_headless(600, '1.10')

if nargin < 1 || isempty(nSamples)
    nSamples = 600;
end
if nargin < 2 || isempty(stopTime)
    stopTime = '1.10';
end

model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);
datasetsDir = fullfile(projectDir, 'datasets');

if ~isfolder(datasetsDir)
    mkdir(datasetsDir);
end

addpath(fullfile(projectDir, 'control_panels'));
addpath(fullfile(projectDir, 'datasets'));
addpath(thisDir);

fprintf('===========================================================\n');
fprintf('   HEADLESS POST-CALIBRATION DATASET GENERATOR            \n');
fprintf('===========================================================\n');
fprintf(' Model        : %s\n', model);
fprintf(' Total Samples: %d\n', nSamples);
fprintf(' Stop Time    : %s s\n', stopTime);
fprintf(' Output Dir   : %s\n', datasetsDir);
fprintf('===========================================================\n\n');

if ~bdIsLoaded(model)
    load_system(fullfile(thisDir, [model '.slx']));
end

repair_hybrid_relay_for_lstm_verification(false);

% Build scenario table
ST = buildScenarioTable();

% Compute counts per scenario
weights = [ST.weight];
counts = max(1, round(nSamples * weights / sum(weights)));
counts(1) = counts(1) + (nSamples - sum(counts));
totalActual = sum(counts);

fprintf('Scenario breakdown (%d scenario types, %d total samples):\n', numel(ST), totalActual);
for i = 1:numel(ST)
    fprintf('  [%2d] %-30s : %d samples\n', i, ST(i).name, counts(i));
end
fprintf('\nStarting simulation batch execution...\n\n');

chkFile = fullfile(datasetsDir, 'StressTestDataset_POSTCALIB_CHECKPOINT.mat');
if exist(chkFile, 'file')
    fprintf('Found checkpoint file: %s\nLoading existing progress...\n', chkFile);
    loaded = load(chkFile);
    dataset = loaded.dataset;
    if ~isfield(dataset, 'dwtFeatures')
        dataset.dwtFeatures = cell(totalActual, 1);
    end
    completedIdx = 0;
    for cIdx = 1:numel(dataset.simulationStatus)
        if ~isempty(dataset.simulationStatus{cIdx}) && strcmp(dataset.simulationStatus{cIdx}, 'Success')
            completedIdx = cIdx;
        end
    end
    fprintf('Resuming dataset generation from sample %d of %d...\n\n', completedIdx + 1, totalActual);
else
    dataset = preallocateDataset(totalActual, model);
    completedIdx = 0;
end

globalIdx = 0;
startTime = tic;

for si = 1:numel(ST)
    sc = ST(si);
    cnt = counts(si);
    
    fprintf('\n---> Scenario [%2d/%2d] %s (%d samples)\n', si, numel(ST), sc.name, cnt);
    
    for k = 1:cnt
        globalIdx = globalIdx + 1;
        
        if globalIdx <= completedIdx
            continue;
        end
        
        [t_fault, t_energise, Rf, noiseLevel, ctMismatch, secMode, angle_deg] = ...
            randomiseParams(sc, k, cnt);
            
        configureScenario(model, sc, t_fault, t_energise, Rf, secMode);
        injectNoiseCT(model, noiseLevel, ctMismatch);
        
        dataset.zone{globalIdx}            = sc.zone;
        dataset.faultType{globalIdx}       = sc.faultTag;
        dataset.faultResistance(globalIdx) = Rf;
        dataset.inceptionAngle(globalIdx)  = angle_deg;
        dataset.inceptionTime(globalIdx)   = t_fault;
        dataset.energisationTime(globalIdx)= t_energise;
        dataset.shouldTrip(globalIdx)      = sc.shouldTrip;
        dataset.scenarioName{globalIdx}    = sc.name;
        dataset.noiseLevel(globalIdx)      = noiseLevel;
        dataset.ctMismatch{globalIdx}      = ctMismatch;
        dataset.secondaryMode{globalIdx}   = secMode;
        
        try
            simOut = sim(model, 'StopTime', stopTime);
            iDiffData = safeGet(simOut, 'I_diff');
            dataset.diffCurrent{globalIdx}      = iDiffData;
            dataset.restCurrent{globalIdx}      = safeGet(simOut, 'I_rest');
            dataset.tripSignal{globalIdx}       = safeGet(simOut, 'TripSignal');
            dataset.dwtFeatures{globalIdx}      = safeGet(simOut, 'DWT_Features');
            
            pCurr = safeGet(simOut, 'I_primary_abc');
            if isempty(pCurr), pCurr = iDiffData; end
            sCurr = safeGet(simOut, 'I_secondary_abc');
            if isempty(sCurr), sCurr = iDiffData; end
            
            dataset.primaryCurrent{globalIdx}   = pCurr;
            dataset.secondaryCurrent{globalIdx} = sCurr;
            dataset.simulationStatus{globalIdx} = 'Success';
            statusStr = 'OK';
        catch ME
            errMsg = ME.message;
            if ~isempty(ME.cause)
                for cIdx = 1:numel(ME.cause)
                    errMsg = sprintf('%s | Cause %d: %s', errMsg, cIdx, ME.cause{cIdx}.message);
                end
            end
            dataset.simulationStatus{globalIdx} = sprintf('Failed: %s', errMsg);
            statusStr = sprintf('FAILED (%s)', errMsg);
        end
        
        elapsed = toc(startTime);
        eta = (elapsed / (globalIdx - completedIdx)) * (totalActual - globalIdx);
        fprintf('Progress: [%3d/%3d] (%5.1f%%) | %-25s | Status: %s | Elapsed: %.0fs | ETA: %.0fs\n', ...
            globalIdx, totalActual, (globalIdx/totalActual)*100, sc.name, statusStr, elapsed, eta);

        % Save intermediate checkpoint every 20 samples
        if mod(globalIdx, 20) == 0 || globalIdx == totalActual
            chkFile = fullfile(datasetsDir, 'StressTestDataset_POSTCALIB_CHECKPOINT.mat');
            save(chkFile, 'dataset', '-v7.3');
        end
    end
end

% Save raw dataset
timestampStr = datestr(now, 'yyyymmdd_HHMMSS');
rawFile = fullfile(datasetsDir, ['StressTestDataset_POSTCALIB_' timestampStr '.mat']);
save(rawFile, 'dataset', '-v7.3');
fprintf('\nSaved raw post-calibration dataset: %s\n', rawFile);

% Extract features
fprintf('\nStarting feature extraction (CombineAndExtractFeatures)...\n');
cd(datasetsDir);
CombineAndExtractFeatures;

fprintf('\n===========================================================\n');
fprintf('   DATASET GENERATION AND FEATURE EXTRACTION COMPLETE      \n');
fprintf('===========================================================\n');
end

% -------------------------------------------------------------------------
% Helper functions from ControlPanel_StressTest.m
% -------------------------------------------------------------------------
function ST = buildScenarioTable()
rows = {
  'Normal'               'Normal'   'none'          0  0  0  0   0.00   0.00  false  10
  'Inrush_NoLoad'        'Inrush'   'inrush'        0  0  0  0   0.00   0.00  false   6
  'Inrush_Loaded'        'Inrush'   'inrush_load'   0  0  0  0   0.00   0.00  false   4
  'Internal_AG'          'Internal' 'Internal_Fault1' 1  0  0  1  0.01   2.0   true    5
  'Internal_BG'          'Internal' 'Internal_Fault1' 0  1  0  1  0.01   2.0   true    4
  'Internal_CG'          'Internal' 'Internal_Fault1' 0  0  1  1  0.01   2.0   true    4
  'Internal_ABG'         'Internal' 'Internal_Fault1' 1  1  0  1  0.01   2.0   true    4
  'Internal_BCG'         'Internal' 'Internal_Fault1' 0  1  1  1  0.01   2.0   true    3
  'Internal_ACG'         'Internal' 'Internal_Fault1' 1  0  1  1  0.01   2.0   true    3
  'Internal_AB'          'Internal' 'Internal_Fault1' 1  1  0  0  0.01   2.0   true    2
  'Internal_BC'          'Internal' 'Internal_Fault1' 0  1  1  0  0.01   2.0   true    2
  'Internal_AC'          'Internal' 'Internal_Fault1' 1  0  1  0  0.01   2.0   true    2
  'Internal_ABC'         'Internal' 'Internal_Fault1' 1  1  1  0  0.01   2.0   true    4
  'Internal_ABCG'        'Internal' 'Internal_Fault1' 1  1  1  1  0.01   2.0   true    4
  'Internal_HiZ_AG'      'Internal' 'Internal_Fault1' 1  0  0  1  50.0   300   true    3
  'Internal_HiZ_BG'      'Internal' 'Internal_Fault1' 0  1  0  1  50.0   300   true    2
  'Internal_HiZ_CG'      'Internal' 'Internal_Fault1' 0  0  1  1  50.0   300   true    2
  'Internal_HiZ_ABG'     'Internal' 'Internal_Fault1' 1  1  0  1  50.0   300   true    3
  'Internal_HiZ_BCG'     'Internal' 'Internal_Fault1' 0  1  1  1  50.0   300   true    2
  'Internal_HiZ_ACG'     'Internal' 'Internal_Fault1' 1  0  1  1  50.0   300   true    2
  'Internal_HiZ_AB'      'Internal' 'Internal_Fault1' 1  1  0  0  50.0   300   true    1
  'Internal_HiZ_BC'      'Internal' 'Internal_Fault1' 0  1  1  0  50.0   300   true    1
  'Internal_HiZ_AC'      'Internal' 'Internal_Fault1' 1  0  1  0  50.0   300   true    1
  'Internal_HiZ_ABC'     'Internal' 'Internal_Fault1' 1  1  1  0  50.0   300   true    2
  'Internal_HiZ_ABCG'    'Internal' 'Internal_Fault1' 1  1  1  1  50.0   300   true    2
  'Internal_Evolving'    'Internal' 'evolving'       1  0  0  1  0.01   0.5   true    4
  'External_AG'          'External' 'External_Fault' 1  0  0  1  0.01   5.0   false   8
  'External_BG'          'External' 'External_Fault' 0  1  0  1  0.01   5.0   false   6
  'External_CG'          'External' 'External_Fault' 0  0  1  1  0.01   5.0   false   6
  'External_ABG'         'External' 'External_Fault' 1  1  0  1  0.01   5.0   false   6
  'External_BCG'         'External' 'External_Fault' 0  1  1  1  0.01   5.0   false   6
  'External_ACG'         'External' 'External_Fault' 1  0  1  1  0.01   5.0   false   6
  'External_AB'          'External' 'External_Fault' 1  1  0  0  0.01   5.0   false   6
  'External_ABC'         'External' 'External_Fault' 1  1  1  0  0.01   5.0   false   12
  'External_ABCG'        'External' 'External_Fault' 1  1  1  1  0.01   5.0   false   12
  'External_HiZ_AG'      'External' 'External_Fault' 1  0  0  1  20.0   100   false   4
  'External_HiZ_ABG'     'External' 'External_Fault' 1  1  0  1  20.0   100   false   4
  'External_HiZ_ABCG'    'External' 'External_Fault' 1  1  1  1  20.0   100   false   4
  'Stress_FaultInInrush' 'Internal' 'fault_inrush'   1  1  0  1  0.01   1.0   true    3
  'Stress_ExtInInrush'   'Inrush'   'ext_inrush'     1  0  0  1  0.01   5.0   false   4
  'Stress_CTSat'         'Internal' 'Internal_Fault1' 1  0  0  1  0.01   0.1   true    3
  'Stress_ExtCTSat'      'External' 'External_Fault' 1  1  1  0  0.001  0.05  false   15
};
ST = struct();
for i = 1:size(rows,1)
    ST(i).name       = rows{i,1};
    ST(i).zone       = rows{i,2};
    ST(i).block      = rows{i,3};
    ST(i).fA         = rows{i,4};
    ST(i).fB         = rows{i,5};
    ST(i).fC         = rows{i,6};
    ST(i).fG         = rows{i,7};
    ST(i).Rf_lo      = rows{i,8};
    ST(i).Rf_hi      = rows{i,9};
    ST(i).shouldTrip = rows{i,10};
    ST(i).weight     = rows{i,11};
    ST(i).faultTag   = buildFaultTag(rows{i,4},rows{i,5},rows{i,6},rows{i,7});
end
end

function [t_fault, t_energise, Rf, noiseLevel, ctMismatch, secMode, angle_deg] = randomiseParams(sc, k, cnt)
T_cycle = 1/50;
t_energise = 0;
angle_deg  = 0;
secMode    = 'none';

if strcmp(sc.block,'inrush') || strcmp(sc.block,'inrush_load') || strcmp(sc.block,'fault_inrush')
    binWidth   = 0.70 / cnt;
    t_energise = 0.10 + (k-1)*binWidth + rand()*binWidth;
    angle_deg  = mod(t_energise, T_cycle) / T_cycle * 360;
    if strcmp(sc.block,'inrush')
        secMode = 'noload';
    else
        secMode = 'loaded';
    end
end

t_fault = 0.30 + 0.45*rand();

if sc.Rf_lo >= sc.Rf_hi
    Rf = sc.Rf_lo;
else
    logLo = log10(max(sc.Rf_lo, 1e-4));
    logHi = log10(sc.Rf_hi);
    Rf    = 10^(logLo + (logHi-logLo)*rand());
end

noiseLevel = 0.003 + 0.147*rand();
if strcmp(sc.name,'Stress_CTSat')
    noiseLevel = 0.10 + 0.15*rand();
end

ctMismatch = ones(6,1);
for p = 1:6
    ctMismatch(p) = 1.0 + (rand()-0.5)*2.0*noiseLevel;
end
end

function configureScenario(model, sc, t_fault, t_energise, Rf, secMode)
resetFaultBlocks(model);

switch sc.block
    case 'none'
        configureBreakersClosed(model, 0.05);
    case 'inrush'
        configureInrushSample(model, t_energise, secMode);
    case 'inrush_load'
        configureInrushSample(model, t_energise, secMode);
    case 'Internal_Fault1'
        configureBreakersClosed(model, 0.05);
        set_param([model '/Step3'], 'Time', num2str(t_fault,'%.6f'));
        applyFaultConfig(model, [model '/Internal_Fault1'], sc.fA, sc.fB, sc.fC, sc.fG, Rf, t_fault);
    case 'External_Fault'
        configureBreakersClosed(model, 0.05);
        set_param([model '/Step4'], 'Time', num2str(t_fault,'%.6f'));
        applyFaultConfig(model, [model '/External_Fault'], sc.fA, sc.fB, sc.fC, sc.fG, Rf, t_fault);
    case 'evolving'
        configureBreakersClosed(model, 0.05);
        set_param([model '/Step3'], 'Time', num2str(t_fault,'%.6f'));
        applyFaultConfig(model, [model '/Internal_Fault1'], 1, 0, 0, 1, Rf, t_fault);
    case 'fault_inrush'
        configureInrushSample(model, t_energise, 'loaded');
        t_f = t_energise + 0.05 + 0.30*rand();
        set_param([model '/Step3'], 'Time', num2str(t_f,'%.6f'));
        applyFaultConfig(model, [model '/Internal_Fault1'], sc.fA, sc.fB, sc.fC, sc.fG, Rf, t_f);
    case 'ext_inrush'
        configureInrushSample(model, t_energise, 'loaded');
        t_f = t_energise + 0.05 + 0.30*rand();
        set_param([model '/Step4'], 'Time', num2str(t_f,'%.6f'));
        applyFaultConfig(model, [model '/External_Fault'], sc.fA, sc.fB, sc.fC, sc.fG, Rf, t_f);
end
end

function configureBreakersClosed(model, t_close)
try
    set_param([model '/Three-Phase Breaker '], 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[]');
catch
end
try
    set_param([model '/Three-Phase Breaker1 '], 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[]');
catch
end
try
    set_param([model '/Step_down_Transformer'], 'SetInitialFlux', 'off');
catch
end
end

function configureInrushSample(model, t_energise, secMode)
try
    set_param([model '/Three-Phase Breaker '], 'External', 'off', 'InitialState', 'open', 'SwitchTimes', sprintf('[%.6f]', t_energise));
catch
end
try
    if strcmp(secMode, 'noload')
        set_param([model '/Three-Phase Breaker1 '], 'External', 'off', 'InitialState', 'open', 'SwitchTimes', '[]');
    else
        set_param([model '/Three-Phase Breaker1 '], 'External', 'off', 'InitialState', 'open', 'SwitchTimes', sprintf('[%.6f]', t_energise));
    end
catch
end
try
    fluxA = -0.8 + 1.6*rand();
    fluxB = -0.8 + 1.6*rand();
    fluxC = -(fluxA + fluxB);
    set_param([model '/Step_down_Transformer'], 'SetInitialFlux', 'on', ...
        'InitialFluxes', sprintf('[%.4f %.4f %.4f]', fluxA, fluxB, fluxC));
catch
end
end

function applyFaultConfig(model, blockName, fA, fB, fC, fG, Rf, t_fault)
onOff = @(v) ifelse(v==1, 'on', 'off');
try
    if nargin < 8 || isempty(t_fault)
        t_fault = 0.50;
    end
    set_param(blockName, 'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), ...
        'GroundFault', onOff(fG), 'FaultResistance', num2str(Rf, '%.6f'), ...
        'SwitchTimes', sprintf('[%.6f 1.10]', t_fault));
catch
end
end

function injectNoiseCT(model, noiseLevel, ctMismatch)
% Optional parameter noise injection placeholder
end

function resetFaultBlocks(model)
set_param([model '/Step3'], 'Time', '10');
set_param([model '/Step4'], 'Time', '10');
try
    set_param([model '/Internal_Fault1'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', ...
        'GroundFault', 'off', 'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
catch
end
try
    set_param([model '/External_Fault'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', ...
        'GroundFault', 'off', 'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
catch
end
end

function dataset = preallocateDataset(N, model)
dataset = struct();
dataset.zone               = cell(N, 1);
dataset.faultType          = cell(N, 1);
dataset.faultResistance    = zeros(N, 1);
dataset.inceptionAngle     = zeros(N, 1);
dataset.inceptionTime      = zeros(N, 1);
dataset.energisationTime   = zeros(N, 1);
dataset.shouldTrip         = false(N, 1);
dataset.scenarioName       = cell(N, 1);
dataset.noiseLevel         = zeros(N, 1);
dataset.ctMismatch         = cell(N, 1);
dataset.secondaryMode      = cell(N, 1);
dataset.simulationStatus   = cell(N, 1);

dataset.primaryCurrent     = cell(N, 1);
dataset.secondaryCurrent   = cell(N, 1);
dataset.diffCurrent        = cell(N, 1);
dataset.restCurrent        = cell(N, 1);
dataset.tripSignal         = cell(N, 1);
end

function tag = buildFaultTag(fA, fB, fC, fG)
str = '';
if fA, str = [str 'A']; end
if fB, str = [str 'B']; end
if fC, str = [str 'C']; end
if fG, str = [str 'G']; end
if isempty(str), str = 'None'; end
tag = str;
end

function val = safeGet(simOut, varName)
val = [];
try
    logs = simOut.get('logsout');
    el = logs.get(varName);
    val = el.Values.Data;
catch
    try
        val = simOut.get(varName);
    catch
    end
end
end

function val = ifelse(cond, a, b)
if cond, val = a; else, val = b; end
end
