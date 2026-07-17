% test_logging_only.m
% Modify the model to bypass the LSTM Predict block and enable signal logging on Feature Window.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    subsys = [model '/Hybrid 87T Relay'];
    lstm_path = [subsys '/LSTM Predict'];
    term_path = [subsys '/Terminator_LSTM'];
    
    % Disable/delete LSTM Predict block to prevent MATLAB crash
    if getSimulinkBlockHandle(lstm_path) ~= -1
        fprintf('Bypassing LSTM Predict block to prevent crash...\n');
        ph_l = get_param(lstm_path, 'PortHandles');
        line_in = get_param(ph_l.Inport(1), 'Line');
        if line_in ~= -1, delete_line(line_in); end
        line_out = get_param(ph_l.Outport(1), 'Line');
        if line_out ~= -1, delete_line(line_out); end
        delete_block(lstm_path);
    end
    
    % Add Terminator block for Feature Window output
    if getSimulinkBlockHandle(term_path) == -1
        fprintf('Adding Terminator block...\n');
        add_block('built-in/Terminator', term_path);
        add_line(subsys, 'Feature Window/1', 'Terminator_LSTM/1');
    end
    
    % Enable signal logging on Feature Window output port
    fprintf('Enabling signal logging on Feature Window...\n');
    ph_fw = get_param([subsys '/Feature Window'], 'PortHandles');
    set_param(ph_fw.Outport(1), 'DataLogging', 'on');
    set_param(ph_fw.Outport(1), 'DataLoggingNameMode', 'Custom');
    set_param(ph_fw.Outport(1), 'DataLoggingName', 'DWT_Features');
    
    % Save the model
    save_system(model);
    fprintf('✓ Model updated and saved successfully.\n');
    
    % Run a test 1.0s simulation of Case 3 (Internal Fault) to verify stability
    fprintf('Running test simulation (Internal Fault) for 1.0s...\n');
    resetFaultBlocks(model);
    setBreakersClosed(model);
    set_param([model '/Step3'], 'Time', '0.50');
    set_param([model '/Internal_Fault1'], ...
        'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on', ...
        'FaultResistance', '0.1');
    
    simOut = sim(model, 'StopTime', '1.0', 'ReturnWorkspaceOutputs', 'on');
    fprintf('✓ Simulation completed successfully without crash!\n');
    
    % Check logged signals
    logs = simOut.get('logsout');
    feat_el = logs.get('DWT_Features');
    if ~isempty(feat_el)
        feat_data = feat_el.Values.Data;
        feat_time = feat_el.Values.Time;
        fprintf('✓ Logged DWT Features successfully! Data shape: %s\n', mat2str(size(feat_data)));
        
        % Save logged features to a MAT file for Python evaluation
        save('test_logged_features.mat', 'feat_data', 'feat_time');
        fprintf('✓ Saved features to test_logged_features.mat\n');
    else
        fprintf('⚠ DWT_Features signal not found in logsout!\n');
    end
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end
