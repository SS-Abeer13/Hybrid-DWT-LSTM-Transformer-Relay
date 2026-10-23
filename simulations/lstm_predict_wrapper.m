function probability = lstm_predict_wrapper(featureSequence)
%LSTM_PREDICT_WRAPPER Run the imported WT-LSTM network in simulation.
%
% Output = CONFIRMED trip probability: the minimum of the last cfg.AI_DWELL raw
% network outputs (one per 1600 Hz sample). The decision chart's test
% "probability >= AI_Threshold" is therefore true only when the raw score has
% stayed above the threshold for AI_DWELL consecutive samples (20 = 12.5 ms).
% This is the exact persistence rule used to tune and test the model in
% lstm_models/train_trace_split.py (--dwell). It stops short spikes, such as the
% 8-14 sample spike seen at inrush onset, from tripping. Raw outputs are still
% written to lstm_diagnostics.txt.

% Dataset generation (generate_stress_dataset_v2.m) sets this flag: the LSTM output is not
% needed there, so return at once instead of running the network 1,761 times per simulation.
if isappdata(0, 'HybridRelaySkipLSTM') && isequal(getappdata(0, 'HybridRelaySkipLSTM'), true)
    probability = 0.0;
    return;
end

% Use simulation time to detect run boundaries and reset state
t_now = 0;
try
    t_now = get_param(bdroot, 'SimulationTime');
catch
end

persistent net last_t sampleCount callCounter hist
if isempty(last_t)
    last_t = -1;
end
if isempty(sampleCount)
    sampleCount = 0;
end

if t_now < 0.005
    net = [];
    sampleCount = 0;
    last_t = -1;
    callCounter = 0;
    hist = [];
end

if isempty(net)
    thisDir = fileparts(mfilename('fullpath'));
    projectDir = fileparts(thisDir);
    addpath(fullfile(projectDir, 'lstm_models'));
    addpath(thisDir);
    
    onnxFile = fullfile(projectDir, 'lstm_models', 'wt_lstm_relay.onnx');
    fprintf('Loading fresh ONNX model directly: %s\n', onnxFile);
    net = importONNXNetwork(onnxFile, 'TargetNetwork', 'dlnetwork');
end

x = single(featureSequence);
cfg = relay_config();
dwell = 1;
if isfield(cfg, 'AI_DWELL'), dwell = max(1, round(cfg.AI_DWELL)); end
if isempty(hist) || numel(hist) ~= dwell
    hist = zeros(1, dwell);
end

if t_now < last_t || t_now < 0.005
    sampleCount = 0;
end
last_t = t_now;

sampleCount = sampleCount + 1;

% Zero-feature guard: negligible differential current energy means zero fault probability
if max(abs(x(:))) < 1e-4
    hist = [hist(2:end), 0.0];
    probability = min(hist);
    return;
end

% Ensure x has exact 3D shape [1, 32, 12] (Batch=1, Time=32, Channels=12)
if ismatrix(x)
    if size(x, 1) == cfg.N_WINDOW && size(x, 2) == cfg.N_FEATURES
        x = reshape(x, [1, cfg.N_WINDOW, cfg.N_FEATURES]);
    elseif size(x, 1) == cfg.N_FEATURES && size(x, 2) == cfg.N_WINDOW
        x = reshape(x.', [1, cfg.N_WINDOW, cfg.N_FEATURES]);
    end
elseif ndims(x) == 3
    if size(x, 1) == cfg.N_FEATURES && size(x, 2) == cfg.N_WINDOW
        x = permute(x, [3, 2, 1]);
    end
end

try
    dlX = dlarray(x, 'BTC');
    dlY = predict(net, dlX);
    % The exported ONNX already ends in a Sigmoid (export_onnx.py SimulinkWrapper),
    % so its output IS the trip probability. Applying sigmoid again (as before
    % 2026-10-18) squeezed every output into 0.50-0.73, so a 0.99 threshold could
    % never be reached. 'logit' is kept only as a name for the diagnostics below.
    probability = double(extractdata(dlY));
    probability = probability(1);
    logit = log(max(probability, 1e-12) / max(1 - probability, 1e-12));
    
    % Print diagnostic feature stats once in a while or when requested
    if isempty(callCounter), callCounter = 0; end
    callCounter = callCounter + 1;
    if callCounter == 100 || callCounter == 1000
        fprintf('[LSTM Debug Step %d] Feature min=%.4f max=%.4f mean=%.4f -> Logit=%.4f Prob=%.4f\n', ...
            callCounter, min(x(:)), max(x(:)), mean(x(:)), logit, probability);
    end
catch
    probability = 0.0;
end

if ~isfinite(probability)
    probability = 0.0;
end
probability = min(max(probability, 0.0), 1.0);

% Persistence (dwell): confirmed score = minimum of the last AI_DWELL raw outputs.
rawProbability = probability;
hist = [hist(2:end), rawProbability];
probability = min(hist);

% Write diagnostics next to this script (simulations/lstm_diagnostics.txt)
try
    diagDir = fileparts(mfilename('fullpath'));
    fid_diag = fopen(fullfile(diagDir, 'lstm_diagnostics.txt'), 'a');
    if fid_diag ~= -1
        fprintf(fid_diag, '[t=%.6f, step=%d] logit=%.6f, prob=%.6f, confirmed=%.6f, std=%.6f, max_val=%.6f\n', ...
            t_now, sampleCount, logit, rawProbability, probability, std(x(:)), max(x(:)));
        fclose(fid_diag);
    end
catch
end
end
