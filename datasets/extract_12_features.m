%% FAST MULTI-FILE 12-FEATURE EXTRACTOR
% Extracts 9 DWT energies + 3 2nd Harmonic Ratios (12 features) across all source datasets

clc; clear; fprintf('=== Fast 12-Feature Extractor (Full Benchmark Set) ===\n');

dataDir = fileparts(mfilename('fullpath')); % datasets dir = this script's own folder
fileList = { ...
    fullfile(dataDir, 'StressTestDataset_POSTCALIB_20260730_072010.mat'), ...
    fullfile(dataDir, 'StressTestDataset_POSTCALIB_20260723_014046.mat'), ...
    fullfile(dataDir, 'StressTestDataset_POSTCALIB_CHECKPOINT.mat') ...
};

all_X = {};
all_Y = {};

WindowSize = 32;
nLevels = 2;
wname = 'db4';
numPhases = 3;

totalTraces = 0;
tic;

for fIdx = 1:length(fileList)
    matFile = fileList{fIdx};
    if ~exist(matFile, 'file')
        continue;
    end
    fprintf('Processing [%d/%d]: %s...\n', fIdx, length(fileList), matFile);
    raw = load(matFile);
    
    if isfield(raw, 'dataset')
        ds = raw.dataset;
    elseif isfield(raw, 'combined')
        ds = raw.combined;
    else
        continue;
    end
    
    numSamples = length(ds.primaryCurrent);
    validCount = 0;
    
    for i = 1:numSamples
        Ip = ds.primaryCurrent{i};
        Is = ds.secondaryCurrent{i};
        
        if isempty(Ip) || isempty(Is)
            continue;
        end
        
        % Ensure [TimeSteps x 3 Phases] orientation
        if size(Ip, 1) < size(Ip, 2)
            Ip = Ip';
        end
        if size(Is, 1) < size(Is, 2)
            Is = Is';
        end
        
        I_diff = Ip - Is; % [1761 x 3]
        
        numSteps = size(I_diff, 1);
        if numSteps < WindowSize + 1
            continue;
        end
        
        numTimeSteps = numSteps - WindowSize;
        featMatrix = zeros(numTimeSteps, 12, 'single');
        
        for t = (WindowSize+1) : numSteps
            outIdx = t - WindowSize;
            sig_window = I_diff((t-WindowSize+1):t, :); % [32 x 3]
            
            for ph = 1:numPhases
                [C, L] = wavedec(sig_window(:, ph), nLevels, wname);
                d1 = detcoef(C, L, 1);
                d2 = detcoef(C, L, 2);
                a2 = appcoef(C, L, wname, 2);
                
                E_D1 = sum(d1.^2);
                E_D2 = sum(d2.^2);
                E_A2 = sum(a2.^2);
                
                base = (ph-1)*3 + 1;
                featMatrix(outIdx, base)   = log(1 + E_D1);
                featMatrix(outIdx, base+1) = log(1 + E_D2);
                featMatrix(outIdx, base+2) = log(1 + E_A2);
                
                % 2nd Harmonic Ratio (Bin 3 = 100 Hz, Bin 2 = 50 Hz @ 1600 Hz / 32 samples)
                fft_vals = abs(fft(sig_window(:, ph)));
                ratio_2nd = fft_vals(3) / (fft_vals(2) + 1e-4);
                featMatrix(outIdx, 9 + ph) = min(ratio_2nd, 2.0);
            end
        end
        
        all_X{end+1} = featMatrix; %#ok<AGROW>
        all_Y{end+1} = double(ds.shouldTrip(i)); %#ok<AGROW>
        validCount = validCount + 1;
        totalTraces = totalTraces + 1;
    end
    fprintf('  Loaded %d valid traces from file %d.\n', validCount, fIdx);
end

fprintf('Extracted %d valid traces in %.1fs. Packaging 3D tensors...\n', totalTraces, toc);

numTraces = length(all_X);
if numTraces == 0
    error('No valid traces found across dataset files!');
end

numTimeSteps = size(all_X{1}, 1);
numFeatures = 12;

X_LSTM = zeros(numTraces, numTimeSteps, numFeatures, 'single');
Y_LSTM = zeros(numTraces, 1, 'single');

for i = 1:numTraces
    X_LSTM(i, :, :) = all_X{i};
    Y_LSTM(i) = all_Y{i};
end

timestampStr = datestr(now, 'yyyymmdd_HHMMSS');
outFile = fullfile(dataDir, sprintf('LSTM_Features_Combined_%s.mat', timestampStr));
fprintf('Saving 12-feature MAT dataset to %s...\n', outFile);
save(outFile, 'X_LSTM', 'Y_LSTM', '-v7.3');
fprintf('✓ Complete! Saved %d traces x %d steps x %d features to %s in %.1fs.\n', ...
    numTraces, numTimeSteps, numFeatures, outFile, toc);
