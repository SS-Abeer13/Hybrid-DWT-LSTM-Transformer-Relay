% inspect_simulation_features.m
% Run a short simulation, log the DWT features, and save them to a MAT file

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup
    run('modelsetup.m');
    
    % Enable logging on the output port of DWT Feature Extraction
    dwt_blk = [model '/Hybrid 87T Relay/DWT Feature Extraction'];
    ph = get_param(dwt_blk, 'PortHandles');
    set_param(ph.Outport(1), 'DataLogging', 'on');
    lh = get_param(ph.Outport(1), 'Line');
    if lh ~= -1
        set_param(lh, 'Name', 'DWT_Features');
    end
    
    % Configure a normal case
    setBreakersClosed(model);
    resetFaultBlocks(model);
    
    fprintf('Running normal simulation...\n');
    simOut = sim(model, 'StopTime', '0.15', 'ReturnWorkspaceOutputs', 'on');
    
    % Save logged features
    logs = simOut.get('logsout');
    dwt_el = logs.get('DWT_Features');
    if ~isempty(dwt_el)
        feat_data = dwt_el.Values.Data;
        feat_time = dwt_el.Values.Time;
        save('sim_features.mat', 'feat_data', 'feat_time');
        fprintf('Saved sim_features.mat successfully. Data size: %s\n', num2str(size(feat_data)));
    else
        fprintf('DWT_Features not found in logsout.\n');
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
