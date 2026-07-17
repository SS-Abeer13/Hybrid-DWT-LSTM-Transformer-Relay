% print_detailed_error.m
% Run simulation and print the entire error report recursively to find the exact line causing MLFB compile error

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    run('modelsetup.m');
    setBreakersClosed(model);
    resetFaultBlocks(model);
    
    % Set network path
    lstm_blk = [model '/Hybrid 87T Relay/LSTM Predict'];
    set_param(lstm_blk, 'NetworkFilePath', 'live_relay_ai_20260712.mat');
    set_param(lstm_blk, 'InputDataFormats', "{'input','BTC'}");
    set_param(lstm_blk, 'MiniBatchSize', '1');
    set_param(lstm_blk, 'ForceInterpretedSim', 'on');
    set_param(lstm_blk, 'Predictions', 'on');
    
    % Ensure sw = 1
    sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
    set_param(sw_blk, 'sw', '1');
    
    sim(model, 'StopTime', '0.01');
    
catch ME
    fprintf('====================================================\n');
    fprintf('DETAILED ERROR REPORT:\n');
    fprintf('====================================================\n');
    disp(ME.message);
    fprintf('\nReport:\n');
    disp(ME.getReport());
    
    % Print causes
    print_causes(ME, 1);
end

function print_causes(err, depth)
    for i = 1:numel(err.cause)
        cause = err.cause{i};
        fprintf('\n%s Cause %d:\n', repmat('  ', 1, depth), i);
        fprintf('%s Message: %s\n', repmat('  ', 1, depth), cause.message);
        fprintf('%s Identifier: %s\n', repmat('  ', 1, depth), cause.identifier);
        if ~isempty(cause.cause)
            print_causes(cause, depth + 1);
        end
    end
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
