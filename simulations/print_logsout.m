% print_logsout.m
% Simple script to print the logged element names in logsout after a simulation run

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Setup and run
    run('modelsetup.m');
    set_param([model '/Step3'], 'Time', '0.08');
    set_param([model '/Internal_Fault1'], 'FaultA','on','FaultB','off','FaultC','off','GroundFault','on','FaultResistance','0.1');
    simOut = sim(model, 'StopTime', '0.15', 'ReturnWorkspaceOutputs', 'on');
    
    % Print logsout
    logs = simOut.get('logsout');
    fprintf('logsout elements:\n');
    for i = 1:logs.numElements
        el = logs.get(i);
        fprintf('  Element %d: "%s", BlockPath: "%s"\n', i, el.Name, el.BlockPath.getBlock(1));
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
