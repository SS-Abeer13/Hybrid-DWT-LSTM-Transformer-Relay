function configure_lstm_onnx_for_simulink(saveChanges)
%CONFIGURE_LSTM_ONNX_FOR_SIMULINK Configure the 20260712 9-feature LSTM.
%
% The imported network expects one complete feature sequence with shape
% [batch, timesteps, features] = [1, 1569, 9].  Its 1,569 timesteps are
% generated from the 32-sample, one-sample-hop DWT windows used in training.
%
% Run from this folder:
%   configure_lstm_onnx_for_simulink(true)
%
% Passing true saves the model.  The default only changes the loaded model,
% which is useful for a non-persistent verification run.

if nargin < 1
    saveChanges = false;
end

model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
networkFile = fullfile(thisDir, 'live_relay_ai_20260712.mat');
assert(isfile(networkFile), 'SimulinkLSTM:MissingNetwork', ...
    'Network file not found: %s', networkFile);

if ~bdIsLoaded(model)
    load_system(fullfile(thisDir, [model '.slx']));
end

iDiffBuffer = [model '/Hybrid 87T Relay/I_diff_window'];
featureBuffer = [model '/Hybrid 87T Relay/Feature Window'];
reshapeBlock = [model '/Hybrid 87T Relay/Reshape '];
predictBlock = [model '/Hybrid 87T Relay/LSTM Predict'];

% First stage: a 32-current-sample DWT window with a one-sample hop.
set_param(iDiffBuffer, 'N', '32', 'V', '31');

% Second stage: the complete 1,569-step feature sequence used in training.
set_param(featureBuffer, 'N', '1569', 'V', '1568');
set_param(reshapeBlock, 'OutputDimensions', '[1, 1569, 9]');

set_param(predictBlock, 'NetworkFilePath', networkFile);
set_param(predictBlock, 'InputDataFormats', "{'input','BTC'}");
set_param(predictBlock, 'MiniBatchSize', '1');
set_param(predictBlock, 'Predictions', 'on');

% Keep the LSTM score available in logsout for verification.
ports = get_param(predictBlock, 'PortHandles');
set_param(ports.Outport(1), 'DataLogging', 'on');
lineHandle = get_param(ports.Outport(1), 'Line');
if lineHandle ~= -1
    set_param(lineHandle, 'Name', 'LSTM_Prediction');
end

assert(strcmp(get_param(iDiffBuffer, 'N'), '32') && strcmp(get_param(iDiffBuffer, 'V'), '31'));
assert(strcmp(get_param(featureBuffer, 'N'), '1569') && strcmp(get_param(featureBuffer, 'V'), '1568'));
assert(strcmp(get_param(reshapeBlock, 'OutputDimensions'), '[1, 1569, 9]'));

if saveChanges
    save_system(model);
    fprintf('Saved %s with the 20260712 LSTM configuration.\n', [model '.slx']);
else
    fprintf('Configured the loaded model only; no model file was saved.\n');
end
fprintf('Network: %s\n', networkFile);
fprintf('LSTM input: [1, 1569, 9] in BTC format.\n');
end
