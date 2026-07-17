% verify_switch_logic.m
% Save the model with sw = 0 and run simulation to verify the output of Manual Switch

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
    fprintf('Saved sw = %s\n', get_param(sw_blk, 'sw'));
    
    % Save system to disk!
    save_system(model);
    fprintf('Model saved to disk.\n');
    
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
    
    % Save again after enabling logging
    save_system(model);
    
    fprintf('Running simulation...\n');
    simOut = sim(model, 'StopTime', '0.05', 'ReturnWorkspaceOutputs', 'on');
    
    logs = simOut.get('logsout');
    t = logs.get('lstm_conf').Values.Time;
    conf = logs.get('lstm_conf').Values.Data;
    
    fprintf('Logged lstm_conf first 10 steps:\n');
    for i = 1:min(10, numel(t))
        fprintf('  t = %.4f s: %.4f\n', t(i), conf(i));
    end
    
catch ME
    disp(['Error: ' ME.message]);
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
