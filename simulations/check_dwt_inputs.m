function check_dwt_inputs()
% check_dwt_inputs.m
% Run Normal Operation and print the input to the DWT block.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Set normal operation
    set_param([model '/Internal_Fault1'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    
    subsys = [model '/Hybrid 87T Relay'];
    
    % Add To Workspace blocks to log I_diff and DWT inputs
    t1 = add_block('built-in/ToWorkspace', [subsys '/ToWorkspace_Idiff_check']);
    set_param(t1, 'VariableName', 'I_diff_val_log', 'SaveFormat', 'Array');
    
    % Get port handles
    diff_block = [subsys '/I_diff'];
    ph_diff = get_param(diff_block, 'PortHandles');
    ph_t1 = get_param(t1, 'PortHandles');
    
    add_line(subsys, ph_diff.Outport(1), ph_t1.Inport(1), 'autorouting', 'on');
    
    fprintf('Running simulation of Normal Operation...\n');
    simOut = sim(model, 'StopTime', '0.2', 'ReturnWorkspaceOutputs', 'on');
    
    % Clean up temporary blocks
    delete_line(get_param(ph_t1.Inport(1), 'Line'));
    delete_block(t1);
    
    I_diff_val = simOut.get('I_diff_val_log');
    
    % Extract data
    if isa(I_diff_val, 'double')
        if size(I_diff_val, 2) == 4
            val = I_diff_val(:, 2:4);
        else
            val = I_diff_val;
        end
    else
        val = I_diff_val.Data;
    end
    
    n_samples = size(val, 1);
    fprintf('Simulation finished. Total samples: %d\n', n_samples);
    fprintf('First 5 samples of I_diff:\n');
    for i = 1:min(5, n_samples)
        fprintf('  t=%d: [%.6f, %.6f, %.6f]\n', i, val(i, 1), val(i, 2), val(i, 3));
    end
    fprintf('Last 5 samples of I_diff:\n');
    for i = max(1, n_samples-4):n_samples
        fprintf('  t=%d: [%.6f, %.6f, %.6f]\n', i, val(i, 1), val(i, 2), val(i, 3));
    end
    
    % Also check if the DWT Feature Extraction block outputs large values
    DWT_Features = simOut.get('logsout').get('DWT_Features').Values.Data;
    fprintf('DWT Features at last step (t=0.2s):\n');
    disp(DWT_Features(end, :, end));
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end

end
