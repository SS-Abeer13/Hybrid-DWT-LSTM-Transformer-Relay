function result = run_hybrid_preflight(caseName)
%RUN_HYBRID_PREFLIGHT Run one verification case with concise telemetry.
%
% Usage:
%   run_hybrid_preflight('Normal')
%   run_hybrid_preflight('Inrush')
%   run_hybrid_preflight('Internal')
%   run_hybrid_preflight('External')

if nargin < 1 || isempty(caseName)
    caseName = 'Normal';
end

caseName = validatestring(caseName, {'Normal', 'Inrush', 'Internal', 'External'});
model = 'TransformerWithCTSaturation';

if ~bdIsLoaded(model)
    load_system(model);
end

repair_hybrid_relay_for_lstm_verification(false);
resetFaultBlocks(model);

switch caseName
    case 'Normal'
        setBreakersClosed(model);
        expectedTrip = false;
        faultTime = 0.0;
    case 'Inrush'
        setInrushEnergization(model);
        expectedTrip = false;
        faultTime = 0.05;
    case 'Internal'
        setBreakersClosed(model);
        faultTime = 0.05;
        set_param([model '/Step3'], 'Time', num2str(faultTime, '%.6f'));
        set_param([model '/Internal_Fault1'], ...
            'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', ...
            'GroundFault', 'on', 'FaultResistance', '0.100000');
        expectedTrip = true;
    case 'External'
        setBreakersClosed(model);
        faultTime = 0.05;
        set_param([model '/Step4'], 'Time', num2str(faultTime, '%.6f'));
        set_param([model '/External_Fault'], ...
            'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', ...
            'GroundFault', 'off', 'FaultResistance', '0.100000');
        expectedTrip = false;
end

enableVerificationLogs(model);

fprintf('Running preflight case: %s\n', caseName);
simOut = sim(model, 'StopTime', '1.10', 'ReturnWorkspaceOutputs', 'on');
logs = simOut.get('logsout');

[~, idiff] = readFirstLog(logs, {'Idiff_rms'});
[~, irest] = readFirstLog(logs, {'Irest_rms'});
[~, lstmProb] = readFirstLog(logs, {'LSTM_Prediction'});
[tripTimeVec, tripData] = readFirstLog(logs, {'TripSignal', 'Trip_Signal', 'Dec_Trip_Signal'});

if isempty(lstmProb)
    maxProb = NaN;
else
    maxProb = max(lstmProb(:));
end

tripIdx = find(tripData > 0.5, 1, 'first');
tripped = ~isempty(tripIdx);
if tripped
    tripTime = tripTimeVec(tripIdx);
else
    tripTime = NaN;
end

result = struct( ...
    'caseName', caseName, ...
    'expectedTrip', expectedTrip, ...
    'tripped', tripped, ...
    'tripTime', tripTime, ...
    'faultTime', faultTime, ...
    'maxProbability', maxProb, ...
    'passed', tripped == expectedTrip);

fprintf('case=%s\n', result.caseName);
fprintf('expected_trip=%d\n', result.expectedTrip);
fprintf('actual_trip=%d\n', result.tripped);
fprintf('max_lstm_probability=%.6f\n', result.maxProbability);
if ~isempty(idiff)
    fprintf('max_idiff_rms=%.6f\n', max(idiff(:)));
end
if ~isempty(irest)
    fprintf('max_irest_rms=%.6f\n', max(irest(:)));
end
if result.tripped
    fprintf('trip_time=%.6f\n', result.tripTime);
    fprintf('trip_delay_ms=%.3f\n', (result.tripTime - result.faultTime) * 1000);
end
fprintf('passed=%d\n', result.passed);
end

function enableVerificationLogs(model)
subsys = [model '/Hybrid 87T Relay'];

lstmBlock = [subsys '/LSTM Predict'];
ports = get_param(lstmBlock, 'PortHandles');
set_param(ports.Outport(1), 'DataLogging', 'on');
lineHandle = get_param(ports.Outport(1), 'Line');
if lineHandle ~= -1
    set_param(lineHandle, 'Name', 'LSTM_Prediction');
end

decisionBlock = [subsys '/Supervisory Override with Hardware Fallback'];
ports = get_param(decisionBlock, 'PortHandles');
set_param(ports.Outport(1), 'DataLogging', 'on');
lineHandle = get_param(ports.Outport(1), 'Line');
if lineHandle ~= -1
    set_param(lineHandle, 'Name', 'Dec_Trip_Signal');
end

latchBlock = [subsys '/' sprintf('S-R\nLatch')];
if getSimulinkBlockHandle(latchBlock) ~= -1
    ports = get_param(latchBlock, 'PortHandles');
    set_param(ports.Outport(2), 'DataLogging', 'on');
    lineHandle = get_param(ports.Outport(2), 'Line');
    if lineHandle ~= -1
        set_param(lineHandle, 'Name', 'TripSignal');
    end
end
end

function [time, data] = readFirstLog(logs, names)
time = [];
data = [];
for idx = 1:numel(names)
    try
        element = logs.get(names{idx});
        if ~isempty(element)
            time = element.Values.Time;
            data = element.Values.Data;
            return;
        end
    catch
    end
end
end

function setBreakersClosed(model)
try
    set_param([model '/Three-Phase Breaker '], ...
        'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]');
catch ME
    warning('Preflight:HVBreaker', '%s', ME.message);
end
try
    set_param([model '/Three-Phase Breaker1 '], ...
        'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]');
catch ME
    warning('Preflight:LVBreaker', '%s', ME.message);
end
try
    set_param([model '/Step_down_Transformer'], 'SetInitialFlux', 'off');
catch ME
    warning('Preflight:XfmrFlux', '%s', ME.message);
end
end

function setInrushEnergization(model)
try
    set_param([model '/Three-Phase Breaker '], ...
        'External', 'off', 'InitialState', 'open', 'SwitchTimes', '[0.050]');
catch ME
    warning('Preflight:HVBreaker', '%s', ME.message);
end
try
    set_param([model '/Three-Phase Breaker1 '], ...
        'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]');
catch ME
    warning('Preflight:LVBreaker', '%s', ME.message);
end
try
    set_param([model '/Step_down_Transformer'], ...
        'SetInitialFlux', 'on', 'InitialFluxes', '[-0.6 0.4 0.15]');
catch ME
    warning('Preflight:XfmrFlux', '%s', ME.message);
end
end

function resetFaultBlocks(model)
set_param([model '/Step3'], 'Time', '10');
set_param([model '/Step4'], 'Time', '10');
try
    set_param([model '/Internal_Fault1'], ...
        'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', ...
        'GroundFault', 'off', 'FaultResistance', '0.01', ...
        'SwitchTimes', '[0.05 1]');
catch
end
try
    set_param([model '/External_Fault'], ...
        'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', ...
        'GroundFault', 'off', 'FaultResistance', '0.01', ...
        'SwitchTimes', '[0.05 1]');
catch
end
end
