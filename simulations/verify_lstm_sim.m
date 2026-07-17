% verify_lstm_sim.m
% Simple script to run a single simulation and inspect the logged signals

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Configure model setup (loads live_relay_ai.mat)
    run('modelsetup.m');
    
    % Set to a known scenario (e.g., Internal A-G fault)
    % Set fault blocks
    set_param([model '/Internal_Fault1'], 'FaultA','on','FaultB','off','FaultC','off','GroundFault','on');
    set_param([model '/External_Fault'], 'FaultA','off','FaultB','off','FaultC','off','GroundFault','off');
    set_param([model '/Step3'], 'Time', '0.05'); % Fault incepts at 0.05s
    set_param([model '/Step4'], 'Time', '10');   % External fault inactive
    
    % Run simulation
    disp('Running simulation...');
    simOut = sim(model, 'StopTime', '0.15', 'ReturnWorkspaceOutputs', 'on');
    disp('Simulation finished successfully.');
    
    % Inspect logsout
    if isprop(simOut, 'logsout') || isfield(simOut, 'logsout')
        logs = simOut.get('logsout');
        fprintf('Number of logged elements in logsout: %d\n', logs.numElements);
        for i = 1:logs.numElements
            el = logs.get(i);
            fprintf('  [%d] Name: "%s", Class: %s, Dimensions: %s\n', ...
                i, el.Name, class(el.Values), num2str(size(el.Values.Data)));
            
            % If it's the LSTM output or the Trip signal, let's show some stats!
            if contains(el.Name, 'Predict') || contains(el.Name, 'Trip') || contains(el.Name, 'lstm') || contains(el.Name, 'supervisory')
                data = el.Values.Data;
                time = el.Values.Time;
                fprintf('      -> Data range: [%.4f, %.4f]\n', min(data(:)), max(data(:)));
                % If it tripped, show first trip time
                trip_indices = find(data > 0.5);
                if ~isempty(trip_indices)
                    fprintf('      -> Tripped at t = %.4f s (Index %d)\n', time(trip_indices(1)), trip_indices(1));
                else
                    fprintf('      -> Did not trip (always <= 0.5)\n');
                end
            end
        end
    else
        disp('logsout not found in simulation outputs.');
    end
    
catch ME
    fprintf('Error occurred: %s\n', ME.message);
    disp(ME.getReport());
end
