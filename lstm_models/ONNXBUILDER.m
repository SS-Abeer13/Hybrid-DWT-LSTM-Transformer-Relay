disp('1. Parsing ONNX weights into MATLAB environment...');

% Import PyTorch ONNX as dlnetwork, not DAGNetwork.
% This is required for LSTM/attention-style ONNX graphs.
real_net = importONNXNetwork( ...
    'wt_lstm_relay.onnx', ...
    'TargetNetwork', 'dlnetwork');

disp('2. Packaging for Simulink execution...');

% Simulink Predict block expects a variable named net.
net = real_net;

save('live_relay_ai.mat', 'net');
simDir = fullfile(fileparts(mfilename('fullpath')), '..', 'simulations');
save(fullfile(simDir, 'live_relay_ai.mat'), 'net');

disp('Success! WT-LSTM network saved into lstm_models and simulations live_relay_ai.mat.');
