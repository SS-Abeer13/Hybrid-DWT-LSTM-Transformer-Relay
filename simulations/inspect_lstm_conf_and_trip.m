% inspect_lstm_conf_and_trip.m
% Run normal simulation with LSTM enabled and log the decision block signals

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup
    run('modelsetup.m');
    setBreakersClosed(model);
    resetFaultBlocks(model);
    
    % Set network path
    lstm_predict_blk = [model '/Hybrid 87T Relay/LSTM Predict'];
    set_param(lstm_predict_blk, 'NetworkFilePath', 'live_relay_ai_20260712.mat');
    set_param(lstm_predict_blk, 'InputDataFormats', "{'input','BTC'}");
    set_param(lstm_predict_blk, 'MiniBatchSize', '1');
    set_param(lstm_predict_blk, 'Predictions', 'on');
    
    % Configure Manual Switch to LSTM (sw = 0)
    sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
    set_param(sw_blk, 'sw', '0');
    
    % Log outputs of source blocks feeding the decision block
    ph_dec = get_param([model '/Hybrid 87T Relay/Supervisory Override with Hardware Fallback'], 'PortHandles');
    ph_mux2 = get_param([model '/Hybrid 87T Relay/Mux2'], 'PortHandles');
    ph_mux3 = get_param([model '/Hybrid 87T Relay/Mux3'], 'PortHandles');
    ph_sw = get_param([model '/Hybrid 87T Relay/Manual Switch'], 'PortHandles');
    
    % Enable DataLogging on output ports
    set_param(ph_mux2.Outport(1), 'DataLogging', 'on');
    set_param(ph_mux3.Outport(1), 'DataLogging', 'on');
    set_param(ph_sw.Outport(1), 'DataLogging', 'on');
    set_param(ph_dec.Outport(1), 'DataLogging', 'on');
    
    % Programmatically name the lines
    lh_mux2 = get_param(ph_mux2.Outport(1), 'Line');
    if lh_mux2 ~= -1, set_param(lh_mux2, 'Name', 'Idiff_rms'); end
    
    lh_mux3 = get_param(ph_mux3.Outport(1), 'Line');
    if lh_mux3 ~= -1, set_param(lh_mux3, 'Name', 'Irest_rms'); end
    
    lh_sw = get_param(ph_sw.Outport(1), 'Line');
    if lh_sw ~= -1, set_param(lh_sw, 'Name', 'lstm_conf'); end
    
    lh_dec = get_param(ph_dec.Outport(1), 'Line');
    if lh_dec ~= -1, set_param(lh_dec, 'Name', 'Dec_Trip_Signal'); end
    
    fprintf('Running normal simulation with LSTM enabled...\n');
    simOut = sim(model, 'StopTime', '0.05', 'ReturnWorkspaceOutputs', 'on');
    
    logs = simOut.get('logsout');
    
    % Retrieve logs using line names
    t = logs.get('lstm_conf').Values.Time;
    conf = logs.get('lstm_conf').Values.Data;
    idiff = logs.get('Idiff_rms').Values.Data;
    irest = logs.get('Irest_rms').Values.Data;
    trip = logs.get('Dec_Trip_Signal').Values.Data;
    
    fprintf('\nTime (s)  |  Idiff_rms (A,B,C)  |  Irest_rms (A,B,C)  |  lstm_conf  |  Trip_Signal\n');
    fprintf('%s\n', repmat('-', 1, 80));
    
    % Print first 15 steps
    for i = 1:min(15, numel(t))
        fprintf('%.4f    |  [%5.2f, %5.2f, %5.2f]  |  [%5.2f, %5.2f, %5.2f]  |  %.4f     |  %d\n', ...
            t(i), idiff(i,1,1), idiff(i,2,1), idiff(i,3,1), ...
            irest(i,1,1), irest(i,2,1), irest(i,3,1), ...
            conf(i), trip(i));
    end
    
    % Print any step where Trip_Signal becomes 1
    trip_idx = find(trip > 0.5);
    if ~isempty(trip_idx)
        fprintf('\nFirst trip detected at step %d (t = %.4f s):\n', trip_idx(1), t(trip_idx(1)));
        fprintf('  Idiff_rms: [%.4f, %.4f, %.4f]\n', idiff(trip_idx(1),1,1), idiff(trip_idx(1),2,1), idiff(trip_idx(1),3,1));
        fprintf('  Irest_rms: [%.4f, %.4f, %.4f]\n', irest(trip_idx(1),1,1), irest(trip_idx(1),2,1), irest(trip_idx(1),3,1));
        fprintf('  lstm_conf: %.4f\n', conf(trip_idx(1)));
        fprintf('  Trip_Signal: %d\n', trip(trip_idx(1)));
    else
        fprintf('\nNo trip detected during the first 0.05s.\n');
    end
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end

function setBreakersClosed(model)
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try, set_param(hv, 'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]'); catch, end
    try, set_param(lv, 'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]'); catch, end
end

function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
    try, set_param([model '/Internal_Fault1'], 'FaultA','off','FaultB','off','FaultC','off','GroundFault','off'); catch, end
    try, set_param([model '/External_Fault'], 'FaultA','off','FaultB','off','FaultC','off','GroundFault','off'); catch, end
end
