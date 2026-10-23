function extract_lstm_features_postcalib(datasetMatFile, outputFile)
%EXTRACT_LSTM_FEATURES_POSTCALIB Extract 32-frame sliding window DWT features from dataset
%
% Usage:
%   extract_lstm_features_postcalib('datasets/StressTestDataset_POSTCALIB_600.mat')

thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);
datasetsDir = fullfile(projectDir, 'datasets');

if nargin < 1 || isempty(datasetMatFile)
    datasetFiles = dir(fullfile(datasetsDir, 'StressTestDataset_POSTCALIB_*.mat'));
    if isempty(datasetFiles)
        error('No StressTestDataset_POSTCALIB_*.mat found in %s', datasetsDir);
    end
    [~, latestIdx] = max([datasetFiles.datenum]);
    datasetMatFile = fullfile(datasetsDir, datasetFiles(latestIdx).name);
end

if nargin < 2 || isempty(outputFile)
    outputFile = fullfile(datasetsDir, 'LSTM_Features_Combined_600.mat');
end

cfg = relay_config();
fprintf('===========================================================\n');
fprintf('   POST-CALIBRATION DWT FEATURE EXTRACTOR (N_WINDOW = %d)  \n', cfg.N_WINDOW);
fprintf('===========================================================\n');
fprintf(' Input Dataset : %s\n', datasetMatFile);
fprintf(' Output File   : %s\n', outputFile);
fprintf(' Sliding Window: %d frames (%.1f ms)\n', cfg.N_WINDOW, cfg.N_WINDOW * 0.625);
fprintf('===========================================================\n\n');

loaded = load(datasetMatFile);
if isfield(loaded, 'dataset')
    ds = loaded.dataset;
else
    ds = loaded;
end

nSamples = numel(ds.shouldTrip);
X_LSTM_list = cell(5 * nSamples, 1);
Y_LSTM = zeros(5 * nSamples, 1);
scenarioNames = cell(5 * nSamples, 1);

validCount = 0;
for i = 1:nSamples
    if isfield(ds, 'simulationStatus') && ~isempty(ds.simulationStatus{i})
        if ~strcmp(ds.simulationStatus{i}, 'Success') && ~strcmp(ds.simulationStatus{i}, 'OK')
            continue;
        end
    end
    
    dwtData = [];
    if isfield(ds, 'dwtFeatures') && ~isempty(ds.dwtFeatures{i})
        dwtData = ds.dwtFeatures{i};
    end
    
    if isempty(dwtData) && isfield(ds, 'diffCurrent') && ~isempty(ds.diffCurrent{i})
        % Fallback: compute 2-level db4 DWT sliding window features matching chart_11
        rawIdiff = ds.diffCurrent{i};
        if size(rawIdiff, 2) >= 3
            dwtData = computeFallbackDWT(rawIdiff);
        end
    end
    
    if isempty(dwtData)
        continue;
    end
    
    % dwtData logged from Simulink is [32, 9, N_steps]
    if ndims(dwtData) == 3
        N_steps = size(dwtData, 3);
        t_fault = 0.30;
        if isfield(ds, 'faultTime') && ~isempty(ds.faultTime{i}) && isnumeric(ds.faultTime{i})
            t_fault = ds.faultTime{i};
        end
        k_fault = round(t_fault / 6.25e-4) + 1;
        
        if ds.shouldTrip(i) == 0
            % Sample steady non-fault steps PLUS inrush/external onset steps
            stepIndices = [min(400, N_steps), min(800, N_steps), min(1200, N_steps), min(1600, N_steps)];
            if isfield(ds, 'faultTime') && ~isempty(ds.faultTime{i}) && isnumeric(ds.faultTime{i})
                t_f = ds.faultTime{i};
                k_f = round(t_f / 6.25e-4) + 1;
                stepIndices = [stepIndices, k_f + 4, k_f + 12, k_f + 20, k_f + 32];
            end
            for idx = stepIndices
                k_idx = min(N_steps, max(32, round(idx)));
                validCount = validCount + 1;
                X_LSTM_list{validCount} = squeeze(dwtData(:, :, k_idx)); % [32, 9]
                Y_LSTM(validCount) = 0;
                scenarioNames{validCount} = ds.scenarioName{i};
            end
        else
            % Pre-fault windows (label 0: normal steady operation)
            k_pre_steps = [k_fault - 200, k_fault - 100, k_fault - 50, k_fault - 20];
            for k_pr = k_pre_steps
                k_idx = min(N_steps, max(32, round(k_pr)));
                validCount = validCount + 1;
                X_LSTM_list{validCount} = squeeze(dwtData(:, :, k_idx));
                Y_LSTM(validCount) = 0;
                scenarioNames{validCount} = ds.scenarioName{i};
            end
            
            % Post-fault windows (label 1: fast fault onset + steady fault)
            k_post_steps = [k_fault + 4, k_fault + 12, k_fault + 20, k_fault + 32, k_fault + 80, k_fault + 160];
            for k_p = k_post_steps
                k_idx = min(N_steps, max(32, round(k_p)));
                validCount = validCount + 1;
                X_LSTM_list{validCount} = squeeze(dwtData(:, :, k_idx));
                Y_LSTM(validCount) = 1;
                scenarioNames{validCount} = ds.scenarioName{i};
            end
        end
    else
        % 2D fallback: [N_frames, 9]
        dwtMatrix = squeeze(dwtData);
        if size(dwtMatrix, 1) == 9 && size(dwtMatrix, 2) > 9
            dwtMatrix = dwtMatrix';
        end
        
        N_frames = size(dwtMatrix, 1);
        if N_frames < cfg.N_WINDOW
            dwtMatrix = padarray(dwtMatrix, [cfg.N_WINDOW - N_frames, 0], 'replicate', 'pre');
        end
        
        windowData = dwtMatrix(end-cfg.N_WINDOW+1:end, :); % [32, 9]
        validCount = validCount + 1;
        X_LSTM_list{validCount} = windowData;
        Y_LSTM(validCount) = double(ds.shouldTrip(i));
        scenarioNames{validCount} = ds.scenarioName{i};
    end
end

X_LSTM_list = X_LSTM_list(1:validCount);
Y_LSTM = Y_LSTM(1:validCount);
scenarioNames = scenarioNames(1:validCount);

% Stack into [N_samples, N_WINDOW, N_FEATURES] tensor
X_LSTM = zeros(validCount, cfg.N_WINDOW, cfg.N_FEATURES, 'single');
for i = 1:validCount
    X_LSTM(i, :, :) = single(X_LSTM_list{i});
end

metadata = struct();
metadata.scenarioName = scenarioNames;
metadata.N_WINDOW = cfg.N_WINDOW;
metadata.N_FEATURES = cfg.N_FEATURES;
metadata.extractionDate = datestr(now, 'yyyy-mm-dd HH:MM:SS');

save(outputFile, 'X_LSTM', 'Y_LSTM', 'metadata', '-v7.3');
fprintf('✓ Extracted %d valid sample feature tensors of shape [%d, %d, %d].\n', ...
    validCount, validCount, cfg.N_WINDOW, cfg.N_FEATURES);
fprintf('✓ Saved feature dataset to %s.\n\n', outputFile);

% Also update simulated_test_features.mat for test suites
testFeatFile = fullfile(datasetsDir, 'simulated_test_features.mat');
save(testFeatFile, 'X_LSTM', 'Y_LSTM', 'metadata', '-v7.3');
fprintf('✓ Updated simulated_test_features.mat.\n');

end

function dwtMat = computeFallbackDWT(I_diff)
% Helper to compute DWT features matching chart_11 for fallback
N_samples = size(I_diff, 1);
dwtMat = zeros(N_samples, 9);
for t = 32:N_samples
    win = I_diff(t-31:t, 1:3);
    feat = zeros(1, 9);
    for ph = 1:3
        sig = win(:, ph);
        [C, L] = wavedec(sig, 2, 'db4');
        d1 = detcoef(C, L, 1);
        d2 = detcoef(C, L, 2);
        a2 = appcoef(C, L, 'db4', 2);
        base = (ph - 1)*3 + 1;
        feat(base)   = log(1 + sum(d1.^2));
        feat(base+1) = log(1 + sum(d2.^2));
        feat(base+2) = log(1 + sum(a2.^2));
    end
    dwtMat(t, :) = feat;
end
end
