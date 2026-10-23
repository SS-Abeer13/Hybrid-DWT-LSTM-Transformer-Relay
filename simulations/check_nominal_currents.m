% check_nominal_currents.m
% Let's load the model, run normal operation, and print the primary and secondary currents.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Set normal operation (disable faults)
    set_param([model '/Internal_Fault1'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    
    fprintf('Running simulation of Normal Operation...\n');
    simOut = sim(model, 'StopTime', '0.2', 'ReturnWorkspaceOutputs', 'on');
    
    % Get logs
    I_prim = simOut.get('I_primary_abc');
    I_sec = simOut.get('I_secondary_abc');
    
    if ~isempty(I_prim) && ~isempty(I_sec)
        % Calculate RMS of the three phases
        % Since it is logged as timeseries or structure
        if isa(I_prim, 'Simulink.SimulationData.Dataset')
            % Find by name
            error('Dataset format not expected');
        else
            % It might be timeseries or structure with time/signals
            if isstruct(I_prim)
                val_prim = I_prim.signals.values;
                val_sec = I_sec.signals.values;
            else
                val_prim = I_prim.Data;
                val_sec = I_sec.Data;
            end
            
            % Calculate RMS of the last cycle (e.g. last 100 samples)
            n_samples = size(val_prim, 1);
            last_samples = min(200, n_samples);
            rms_prim = rms(val_prim(end-last_samples+1:end, :), 1);
            rms_sec = rms(val_sec(end-last_samples+1:end, :), 1);
            
            fprintf('Primary Line Currents (HV side) RMS:\n');
            disp(rms_prim);
            fprintf('Secondary Line Currents (LV side) RMS:\n');
            disp(rms_sec);
        end
    else
        fprintf('Failed to find I_primary_abc or I_secondary_abc in output!\n');
    end
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end
