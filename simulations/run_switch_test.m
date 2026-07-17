% run_switch_test.m
% Run simulation with sw = 0 and sw = 1 and log switch outputs to verify switch logic

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup
    run('modelsetup.m');
    setBreakersClosed(model);
    resetFaultBlocks(model);
    
    lstm_blk = [model '/Hybrid 87T Relay/LSTM Predict'];
    off_blk = [model '/Hybrid 87T Relay/OFF'];
    sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
    
    % Configure LSTM
    set_param(lstm_blk, 'NetworkFilePath', 'live_relay_ai_20260712.mat');
    set_param(lstm_blk, 'InputDataFormats', "{'input','BTC'}");
    set_param(lstm_blk, 'MiniBatchSize', '1');
    set_param(lstm_blk, 'Predictions', 'on');
    
    % Get port handles
    ph_lstm = get_param(lstm_blk, 'PortHandles');
    ph_off = get_param(off_blk, 'PortHandles');
    ph_sw = get_param(sw_blk, 'PortHandles');
    
    % Enable logging
    set_param(ph_lstm.Outport(1), 'DataLogging', 'on');
    set_param(ph_off.Outport(1), 'DataLogging', 'on');
    set_param(ph_sw.Outport(1), 'DataLogging', 'on');
    
    % Name lines
    lh_in1 = get_param(ph_lstm.Outport(1), 'Line');
    if lh_in1 ~= -1, set_param(lh_in1, 'Name', 'Switch_In1'); end
    lh_in2 = get_param(ph_off.Outport(1), 'Line');
    if lh_in2 ~= -1, set_param(lh_in2, 'Name', 'Switch_In2'); end
    lh_out = get_param(ph_sw.Outport(1), 'Line');
    if lh_out ~= -1, set_param(lh_out, 'Name', 'Switch_Out'); end
    
    % Test sw = 0
    fprintf('--- TESTING sw = 0 ---\n');
    set_param(sw_blk, 'sw', '0');
    save_system(model);
    simOut0 = sim(model, 'StopTime', '0.005', 'ReturnWorkspaceOutputs', 'on');
    logs0 = simOut0.get('logsout');
    t0 = logs0.get('Switch_Out').Values.Time;
    out0 = logs0.get('Switch_Out').Values.Data;
    fprintf('  Logged steps: %d\n', numel(t0));
    fprintf('  Time range: %.4f to %.4f s\n', t0(1), t0(end));
    fprintf('  First 3 outputs: [%.6f, %.6f, %.6f]\n', out0(1), out0(min(2,end)), out0(min(3,end)));
    
    % Test sw = 1
    fprintf('\n--- TESTING sw = 1 ---\n');
    set_param(sw_blk, 'sw', '1');
    save_system(model);
    simOut1 = sim(model, 'StopTime', '0.005', 'ReturnWorkspaceOutputs', 'on');
    logs1 = simOut1.get('logsout');
    t1 = logs1.get('Switch_Out').Values.Time;
    out1 = logs1.get('Switch_Out').Values.Data;
    fprintf('  Logged steps: %d\n', numel(t1));
    fprintf('  Time range: %.4f to %.4f s\n', t1(1), t1(end));
    fprintf('  First 3 outputs: [%.6f, %.6f, %.6f]\n', out1(1), out1(min(2,end)), out1(min(3,end)));
    
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
