function repair_hybrid_relay_for_lstm_verification(saveChanges)
%REPAIR_HYBRID_RELAY_FOR_LSTM_VERIFICATION Restore the LSTM path and gate trip.
%
% The final verification trip is:
%   conventional 87T vote AND LSTM probability >= AI_Threshold
%
% The -1 lstm_conf fallback still allows pure 87T operation when explicitly
% requested, but normal LSTM verification always uses the AI veto.

if nargin < 1
    saveChanges = true;
end

model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);
networkFile = fullfile(projectDir, 'lstm_models', 'live_relay_ai.mat');
if ~isfile(networkFile)
    networkFile = fullfile(thisDir, 'live_relay_ai.mat');
end
assert(isfile(networkFile), 'HybridRelay:MissingNetwork', ...
    'Missing network MAT file: %s', networkFile);

if ~bdIsLoaded(model)
    load_system(fullfile(thisDir, [model '.slx']));
end

subsys = [model '/Hybrid 87T Relay'];
reshapeBlock = [subsys '/Reshape '];
lstmBlock = [subsys '/LSTM Predict'];
decisionBlock = [subsys '/Supervisory Override with Hardware Fallback'];

configureSamplingAndSequence(model, subsys);
restoreLstmFunctionBlock(lstmBlock);
connectLstmPath(subsys, reshapeBlock, lstmBlock, decisionBlock);

if saveChanges
    save_system(model);
    fprintf('Saved %s with restored LSTM path and AI-gated trip logic.\n', [model '.slx']);
else
    fprintf('Repaired the loaded model only; no model file was saved.\n');
end
end

function configureSamplingAndSequence(model, subsys)
iDiffBuffer = [subsys '/I_diff_window'];
featureBuffer = [subsys '/Feature Window'];
reshapeBlock = [subsys '/Reshape '];
rawReshapeBlock = [subsys '/Reshape 1'];
zohBlock = [subsys '/ZOH_1600'];

cfg = relay_config();
set_param(iDiffBuffer, 'N', '32', 'V', '31');
set_param(featureBuffer, 'N', num2str(cfg.N_WINDOW), 'V', num2str(cfg.V_WINDOW));
set_param(reshapeBlock, 'OutputDimensions', sprintf('[1, %d, %d]', cfg.N_WINDOW, cfg.N_FEATURES));

if getSimulinkBlockHandle(zohBlock) == -1
    add_block('built-in/ZeroOrderHold', zohBlock, ...
        'Position', [455 280 505 310], ...
        'SampleTime', '6.25e-4');
else
    set_param(zohBlock, 'SampleTime', '6.25e-4');
end

ensureSingleLine(rawReshapeBlock, 1, zohBlock, 1);
ensureSingleLine(zohBlock, 1, iDiffBuffer, 1);

set_param(model, 'SignalLogging', 'on');
end

function restoreLstmFunctionBlock(lstmBlock)
if getSimulinkBlockHandle(lstmBlock) == -1
    add_block('simulink/User-Defined Functions/MATLAB Function', lstmBlock, ...
        'Position', [760 325 900 385]);
end

rt = sfroot;
chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', lstmBlock);
assert(~isempty(chart), 'HybridRelay:MissingLSTMChart', ...
    'Unable to find MATLAB Function chart for %s.', lstmBlock);

chart.Script = [ ...
    'function probability = LSTM_Predict(featureSequence)' newline ...
    '%#codegen' newline ...
    '% Simulation-only wrapper around live_relay_ai.' newline ...
    'coder.extrinsic(''lstm_predict_wrapper'');' newline ...
    'probability = 0.0;' newline ...
    'probability = lstm_predict_wrapper(featureSequence);' newline ...
    'end' newline];
end

function connectLstmPath(subsys, reshapeBlock, lstmBlock, decisionBlock)
ensureSingleLine(reshapeBlock, 1, lstmBlock, 1);

% Connect LSTM Predict output to Supervisory Decision chart input 3 (lstm_conf)
disconnectInport(decisionBlock, 3);
ensureSingleLine(lstmBlock, 1, decisionBlock, 3);

% Enable DataLogging on LSTM Predict outport line
portsLstm = get_param(lstmBlock, 'PortHandles');
set_param(portsLstm.Outport(1), 'DataLogging', 'on');
lineLstm = get_param(portsLstm.Outport(1), 'Line');
if lineLstm ~= -1
    set_param(lineLstm, 'Name', 'LSTM_Prediction');
end

% Enable DataLogging on S-R Latch outport line (TripSignal)
latchBlock = [subsys '/' sprintf('S-R\nLatch')];
if getSimulinkBlockHandle(latchBlock) ~= -1
    portsLatch = get_param(latchBlock, 'PortHandles');
    set_param(portsLatch.Outport(1), 'DataLogging', 'on');
    lineLatch = get_param(portsLatch.Outport(1), 'Line');
    if lineLatch ~= -1
        set_param(lineLatch, 'Name', 'TripSignal');
    end
end
end



function ensureSingleLine(srcBlock, srcPort, dstBlock, dstPort)
disconnectInport(dstBlock, dstPort);

srcPorts = get_param(srcBlock, 'PortHandles');
dstPorts = get_param(dstBlock, 'PortHandles');
srcLine = get_param(srcPorts.Outport(srcPort), 'Line');
if srcLine ~= -1
    dstHandles = get_param(srcLine, 'DstPortHandle');
    for idx = numel(dstHandles):-1:1
        if dstHandles(idx) == dstPorts.Inport(dstPort)
            return;
        end
    end
end

parent = get_param(srcBlock, 'Parent');
add_line(parent, ...
    [get_param(srcBlock, 'Name') '/' num2str(srcPort)], ...
    [get_param(dstBlock, 'Name') '/' num2str(dstPort)], ...
    'autorouting', 'on');
end

function disconnectInport(blockPath, portNumber)
ports = get_param(blockPath, 'PortHandles');
if numel(ports.Inport) < portNumber
    return;
end
lineHandle = get_param(ports.Inport(portNumber), 'Line');
if lineHandle ~= -1
    delete_line(lineHandle);
end
end

function disconnectOutport(blockPath, portNumber)
if getSimulinkBlockHandle(blockPath) == -1
    return;
end
ports = get_param(blockPath, 'PortHandles');
if numel(ports.Outport) < portNumber
    return;
end
lineHandle = get_param(ports.Outport(portNumber), 'Line');
if lineHandle ~= -1
    delete_line(lineHandle);
end
end
