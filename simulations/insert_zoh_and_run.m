% insert_zoh_and_run.m
% Add a Zero-Order Hold block to downsample the DWT input to 1600 Hz, compile, and run simulation.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    subsys = [model '/Hybrid 87T Relay'];
    zoh_path = [subsys '/ZOH_1600'];
    reshape_path = [subsys '/Reshape 1'];
    buffer_path = [subsys '/I_diff_window'];
    
    % Check if ZOH block already exists. If so, delete it first to ensure clean state.
    if getSimulinkBlockHandle(zoh_path) ~= -1
        fprintf('ZOH block already exists. Deleting it to re-insert...\n');
        % First find and delete lines connected to ZOH
        ph_z = get_param(zoh_path, 'PortHandles');
        line_in = get_param(ph_z.Inport(1), 'Line');
        if line_in ~= -1, delete_line(line_in); end
        line_out = get_param(ph_z.Outport(1), 'Line');
        if line_out ~= -1, delete_line(line_out); end
        delete_block(zoh_path);
    end
    
    % Delete direct connection between Reshape 1 and I_diff_window
    ph_r = get_param(reshape_path, 'PortHandles');
    line_r = get_param(ph_r.Outport(1), 'Line');
    if line_r ~= -1
        fprintf('Deleting direct line between Reshape 1 and I_diff_window...\n');
        delete_line(line_r);
    end
    
    % Add Zero-Order Hold block
    fprintf('Adding Zero-Order Hold block...\n');
    add_block('built-in/ZeroOrderHold', zoh_path);
    set_param(zoh_path, 'SampleTime', '6.25e-4'); % 1600 Hz
    
    % Connect Reshape 1 -> ZOH -> I_diff_window
    fprintf('Connecting Reshape 1 -> ZOH -> I_diff_window...\n');
    add_line(subsys, 'Reshape 1/1', 'ZOH_1600/1');
    add_line(subsys, 'ZOH_1600/1', 'I_diff_window/1');
    
    % Compile model to verify compiled sample times
    fprintf('\nCompiling model to verify sample times...\n');
    feval(model, [], [], [], 'compile');
    
    st_subsys = get_param(get_param(subsys, 'PortHandles').Inport(1), 'CompiledSampleTime');
    st_b1 = get_param(get_param(buffer_path, 'PortHandles').Inport(1), 'CompiledSampleTime');
    st_dwt = get_param(get_param([subsys '/DWT Feature Extraction'], 'PortHandles').Inport(1), 'CompiledSampleTime');
    st_lstm = get_param(get_param([subsys '/LSTM Predict'], 'PortHandles').Inport(1), 'CompiledSampleTime');
    
    feval(model, [], [], [], 'term');
    fprintf('Model compilation terminated.\n\n');
    
    fprintf('Compiled Sample Times after ZOH insertion:\n');
    fprintf('  Subsystem Inport 1   : %.6f s (%.1f Hz)\n', st_subsys(1), 1/st_subsys(1));
    fprintf('  I_diff_window Inport 1: %.6f s (%.1f Hz)\n', st_b1(1), 1/st_b1(1));
    fprintf('  DWT Chart Inport 1    : %.6f s (%.1f Hz)\n', st_dwt(1), 1/st_dwt(1));
    fprintf('  LSTM Predict Inport 1 : %.6f s (%.1f Hz)\n', st_lstm(1), 1/st_lstm(1));
    
    % Save model
    save_system(model);
    fprintf('✓ Model saved successfully with ZOH block.\n\n');
    
    % Now let's run test cases using test_hybrid_relay.m
    fprintf('Running simulation test cases...\n');
    run('test_hybrid_relay');
    
catch ME
    % Terminate if failed during compilation
    try feval(model, [], [], [], 'term'); catch; end
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end
