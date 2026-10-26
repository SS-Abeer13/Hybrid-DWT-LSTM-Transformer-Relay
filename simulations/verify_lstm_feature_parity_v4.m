function report = verify_lstm_feature_parity_v4()
%VERIFY_LSTM_FEATURE_PARITY_V4 Prove v4 relay computes the 12 features exactly as offline Python/MATLAB code.
%
% Runs Normal and an internal A-G case on TransformerWithCTSaturation_v4, logs the DWT chart output,
% recomputes features offline with per-unit normalisation (I_base = 1.8610 A), and compares them.
% PASS = max abs error < 1e-5 (expected: 0.0 or ~1e-15 float precision).

model = 'TransformerWithCTSaturation_v4';
thisDir = fileparts(mfilename('fullpath'));
if ~bdIsLoaded(model), load_system(fullfile(thisDir, [model '.slx'])); end
relay = [model '/Hybrid 87T Relay'];
ph = get_param([relay '/DWT Feature Extraction'], 'PortHandles');
set_param(ph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'DWT_Features_Row');

cases = {'Normal', false; 'Internal A-G', true};
Mplant = (1/sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];   % row-vector form of K = (1/sqrt3)[1 0 -1;-1 1 0;0 -1 1]
I_base = 1.8610;

report = struct('case', {}, 'maxAbsError', {}, 'bestShift', {}, 'pass', {});
for k = 1:size(cases, 1)
    setInternalFault(model, cases{k, 2});
    out = sim(model, 'StopTime', '1.0', 'ReturnWorkspaceOutputs', 'on');
    R = squeeze(double(out.get('logsout').get('DWT_Features_Row').Values.Data));
    if size(R, 2) ~= 12, R = R.'; end
    Ip = tw(out, 'I_primary_abc'); Is = tw(out, 'I_secondary_abc');
    
    % Step 1.4: Per-unit normalisation by I_base = 1.8610 A
    I_diff_pu = (Ip * Mplant - Is) / I_base;
    T = features12(I_diff_pu);

    best = inf; bestShift = 0;                 % allow +/-3 samples of logging alignment
    n = min(size(R, 1), size(T, 1)) - 10;
    for s = -3:3
        a = T(end-n+1+min(s,0) : end+min(s,0), :);
        b = R(end-n+1-max(s,0) : end-max(s,0), :);
        e = max(abs(a - b), [], 'all');
        if e < best, best = e; bestShift = s; end
    end
    report(k) = struct('case', cases{k, 1}, 'maxAbsError', best, 'bestShift', bestShift, 'pass', best < 1e-5);
    if best < 1e-5, verdict = 'PASS'; else, verdict = 'FAIL'; end
    fprintf('%-14s max |relay - training| = %.3g (shift %+d)  %s\n', cases{k, 1}, best, bestShift, verdict);
end

% Reset fault to off and save clean state
setInternalFault(model, false);
save_system(model);
end

function F = features12(I_diff)
% Verbatim logic of DWT_Feature_Extraction with per-unit inputs
W = 32; n = size(I_diff, 1); F = zeros(n - W, 12);
for t = (W + 1):n
    win = I_diff((t - W + 1):t, :);
    for p = 1:3
        [C, L] = wavedec(win(:, p), 2, 'db4');
        b = (p - 1) * 3 + 1;
        F(t - W, b)     = log(1 + sum(detcoef(C, L, 1).^2));
        F(t - W, b + 1) = log(1 + sum(detcoef(C, L, 2).^2));
        F(t - W, b + 2) = log(1 + sum(appcoef(C, L, 'db4', 2).^2));
        v = abs(fft(win(:, p)));
        F(t - W, 9 + p) = min(v(3) / (v(2) + 1e-4), 2.0);
    end
end
end

function x = tw(out, name)
v = out.get(name);
if isa(v, 'timeseries'), x = double(v.Data);
elseif isstruct(v), x = double(v.signals.values);
else, x = double(v); end
end

function setInternalFault(model, on)
blk = [model '/Internal_Fault1'];
if on
    set_param(blk, 'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on', 'FaultResistance', '0.1');
else
    set_param(blk, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
end
end
