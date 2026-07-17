% run_normal_full_logs.m
% Run normal operation simulation and save all time steps to a MAT file

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup
    run('modelsetup.m');
    setBreakersClosed(model);
    resetFaultBlocks(model);
    
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
    
    fprintf('Running normal simulation...\n');
    % Force breakers to stay closed without external trip control
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10]');
    set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10]');
    
    simOut = sim(model, 'StopTime', '0.15', 'ReturnWorkspaceOutputs', 'on');
    
    logs = simOut.get('logsout');
    
    % Retrieve logs using line names
    t = logs.get('lstm_conf').Values.Time;
    conf = logs.get('lstm_conf').Values.Data;
    idiff = logs.get('Idiff_rms').Values.Data;
    irest = logs.get('Irest_rms').Values.Data;
    trip = logs.get('Dec_Trip_Signal').Values.Data;
    
    save('normal_full_run.mat', 't', 'conf', 'idiff', 'irest', 'trip');
    fprintf('Saved normal_full_run.mat successfully.\n');
    
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
