% inspect_switch_block_connections.m
% Log the inputs and outputs of the Manual Switch block directly to see what is going on

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup
    run('modelsetup.m');
    setBreakersClosed(model);
    resetFaultBlocks(model);
    
    % Get blocks
    lstm_blk = [model '/Hybrid 87T Relay/LSTM Predict'];
    off_blk = [model '/Hybrid 87T Relay/OFF'];
    sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
    
    % Set network path
    set_param(lstm_blk, 'NetworkFilePath', 'live_relay_ai_20260712.mat');
    set_param(lstm_blk, 'InputDataFormats', "{'input','BTC'}");
    set_param(lstm_blk, 'MiniBatchSize', '1');
    set_param(lstm_blk, 'Predictions', 'on');
    
    % Set sw = 0
    set_param(sw_blk, 'sw', '0');
    save_system(model);
    
    % Get output port handles of feeding blocks and switch block
    ph_lstm = get_param(lstm_blk, 'PortHandles');
    ph_off = get_param(off_blk, 'PortHandles');
    ph_sw = get_param(sw_blk, 'PortHandles');
    
    % Enable DataLogging on output ports
    set_param(ph_lstm.Outport(1), 'DataLogging', 'on');
    set_param(ph_off.Outport(1), 'DataLogging', 'on');
    set_param(ph_sw.Outport(1), 'DataLogging', 'on');
    
    % Programmatically name the lines
    lh_in1 = get_param(ph_lstm.Outport(1), 'Line');
    if lh_in1 ~= -1, set_param(lh_in1, 'Name', 'Switch_In1'); end
    
    lh_in2 = get_param(ph_off.Outport(1), 'Line');
    if lh_in2 ~= -1, set_param(lh_in2, 'Name', 'Switch_In2'); end
    
    lh_out = get_param(ph_sw.Outport(1), 'Line');
    if lh_out ~= -1, set_param(lh_out, 'Name', 'Switch_Out'); end
    
    save_system(model);
    
    fprintf('Running simulation...\n');
    simOut = sim(model, 'StopTime', '0.01', 'ReturnWorkspaceOutputs', 'on');
    
    logs = simOut.get('logsout');
    
    t = logs.get('Switch_Out').Values.Time;
    in1 = logs.get('Switch_In1').Values.Data;
    in2 = logs.get('Switch_In2').Values.Data;
    out = logs.get('Switch_Out').Values.Data;
    
    fprintf('\nTime (s)  |  Switch Input 1 (LSTM)  |  Switch Input 2 (OFF)  |  Switch Output\n');
    fprintf('%s\n', repmat('-', 1, 75));
    for i = 1:min(10, numel(t))
        fprintf('%.4f    |  %.6f              |  %.6f             |  %.6f\n', ...
            t(i), in1(i), in2(i), out(i));
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
