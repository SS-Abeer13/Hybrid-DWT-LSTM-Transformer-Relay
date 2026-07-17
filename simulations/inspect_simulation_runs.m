% inspect_simulation_runs.m
% Run a short simulation and print all variables in the output object

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup
    run('modelsetup.m');
    setBreakersClosed(model);
    set_param([model '/Step3'], 'Time', '0.08');
    set_param([model '/Internal_Fault1'], 'FaultA','on','FaultB','off','FaultC','off','GroundFault','on','FaultResistance','0.1');
    
    fprintf('Running simulation...\n');
    simOut = sim(model, 'StopTime', '0.15', 'ReturnWorkspaceOutputs', 'on');
    fprintf('Simulation completed.\n\n');
    
    % 1. Print variables in simOut
    disp('=== Variables in simOut ===');
    vars = simOut.who();
    for i = 1:numel(vars)
        val = simOut.get(vars{i});
        fprintf('  Variable name: "%s", Class: %s\n', vars{i}, class(val));
    end
    
    % 2. Print elements in logsout
    if simOut.who().contains('logsout')
        logs = simOut.get('logsout');
        fprintf('\n=== Elements in logsout (%d total) ===\n', logs.numElements);
        for i = 1:logs.numElements
            el = logs.get(i);
            fprintf('  [%d] Name: "%s", BlockPath: "%s"\n', i, el.Name, el.BlockPath.getBlock(1));
        end
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
