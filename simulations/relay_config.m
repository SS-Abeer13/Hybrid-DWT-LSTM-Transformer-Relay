function cfg = relay_config(ver)
%RELAY_CONFIG Single Source of Truth for Hybrid Relay Parameters
%
% Returns configuration structure for sequence lengths, sampling rates,
% and simulation timing across MATLAB and Python scripts.

if nargin < 1 || isempty(ver), ver = 'v4'; end

cfg = struct();
cfg.N_WINDOW   = 32;       % 32 frames = 20 ms sliding feature window (1 cycle at 50Hz)
cfg.N_FEATURES = 12;       % 12 features (9 DWT wavelet energies + 3 2nd harmonic ratios)
cfg.T_STOP     = 1.10;     % Total simulation duration (seconds)
cfg.FS         = 1600;     % Sampling frequency (Hz)
cfg.TS         = 6.25e-4;  % Sampling time (seconds)
cfg.V_WINDOW   = cfg.N_WINDOW - 1; % Simulink Buffer delay parameter (31)
cfg.AI_DWELL   = 20;       % AI trip confirmation: score >= threshold for 20 samples (12.5 ms)
                           % Must match runs\<deployed run>\decision_dwell.txt (used in tuning/testing)

if strcmpi(ver, 'v3') || contains(ver, 'TransformerWithCTSaturation.slx')
    cfg.I_RATED_SEC = 0.9302;  % rated CT-secondary current (A), BOTH sides: effective CT ratios HV 809.6:1 / LV 16925:1
    cfg.LOAD_KNOB_PER_RATED = struct('pf', [0.8 0.9 1], ...
        'knob', [0.02 0.028827 0.041549 0.059885 0.086314 0.12441 0.17931 0.25845 0.37251 0.5369 0.77385 1.1154 1.6076 2.3171 3.3397 4.8136 6.938 10], ...
        'pctRated', [2.171 3.023 4.238 5.961 8.387 11.768 16.412 22.661 30.838 41.138 53.487 67.413 82.046 96.304 109.212 120.154 128.939 135.704;2.152 3.001 4.212 5.927 8.337 11.685 16.266 22.403 30.39 40.402 52.363 65.849 80.083 94.091 106.959 118.058 127.131 134.232;2.094 2.943 4.155 5.87 8.276 11.61 16.156 22.218 30.071 39.867 51.529 64.667 78.576 92.364 105.173 116.37 125.653 133.015]);
else
    cfg.I_RATED_SEC = 1.8610;  % rated CT-secondary current (A), BOTH sides: effective CT ratios HV 404.73:1 / LV 8460.04:1 (probe_ct_truth_v4.m)
    cfg.LOAD_KNOB_PER_RATED = struct('pf', [0.8 0.9 1], ...
        'knob', [0.02 0.028827 0.041549 0.059885 0.086314 0.12441 0.17931 0.25845 0.37251 0.5369 0.77385 1.1154 1.6076 2.3171 3.3397 4.8136 6.938 10], ...
        'pctRated', [2.193 3.066 4.343 6.17 8.739 12.465 17.856 25.593 36.631 52.379 74.731 106.205 150.199 210.842 290.219 345.372 395.143 435.646;2.172 3.057 4.331 6.15 8.71 12.462 17.866 25.61 36.679 52.432 74.803 106.342 150.441 211.228 290.588 347.996 391.217 438.978;2.145 3.01 4.262 6.099 8.721 12.484 17.952 25.71 36.875 52.841 75.471 107.613 152.59 214.935 295.395 351.664 402.778 439.853]);
end
end
