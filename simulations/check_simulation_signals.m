function check_simulation_signals()
% check_simulation_signals.m
% Run Normal Operation with breakers in default External=on state, and print compensated per-unit currents and differential current.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Set normal operation (disable faults)
    set_param([model '/Internal_Fault1'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    
    % Use default External=on for breakers
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    set_param(hv, 'External', 'on');
    set_param(hv, 'InitialState', 'closed');
    set_param(hv, 'SwitchTimes', '[]');
    set_param(lv, 'External', 'on');
    set_param(lv, 'InitialState', 'closed');
    set_param(lv, 'SwitchTimes', '[]');
    
    % Get Yd1 Compensation block port handles
    subsys = [model '/Hybrid 87T Relay'];
    comp_block = [subsys '/Yd1 Compensation'];
    ph = get_param(comp_block, 'PortHandles');
    
    % Add To Workspace blocks INSIDE the subsystem to log the outputs of Yd1 Compensation
    t1 = add_block('built-in/ToWorkspace', [subsys '/ToWorkspace_HV_comp']);
    set_param(t1, 'VariableName', 'I_hv_comp_log', 'SaveFormat', 'Array');
    t2 = add_block('built-in/ToWorkspace', [subsys '/ToWorkspace_LV_comp']);
    set_param(t2, 'VariableName', 'I_lv_comp_log', 'SaveFormat', 'Array');
    
    ph_t1 = get_param(t1, 'PortHandles');
    ph_t2 = get_param(t2, 'PortHandles');
    
    add_line(subsys, ph.Outport(1), ph_t1.Inport(1), 'autorouting', 'on');
    add_line(subsys, ph.Outport(2), ph_t2.Inport(1), 'autorouting', 'on');
    
    % Also log the output of I_diff Sum block
    diff_block = [subsys '/I_diff'];
    ph_diff = get_param(diff_block, 'PortHandles');
    t3 = add_block('built-in/ToWorkspace', [subsys '/ToWorkspace_I_diff']);
    set_param(t3, 'VariableName', 'I_diff_relay_log', 'SaveFormat', 'Array');
    ph_t3 = get_param(t3, 'PortHandles');
    add_line(subsys, ph_diff.Outport(1), ph_t3.Inport(1), 'autorouting', 'on');
    
    fprintf('Running simulation of Normal Operation with breakers in default External=on...\n');
    simOut = sim(model, 'StopTime', '0.2', 'ReturnWorkspaceOutputs', 'on');
    
    % Clean up temporary blocks inside subsystem
    delete_line(get_param(ph_t1.Inport(1), 'Line'));
    delete_line(get_param(ph_t2.Inport(1), 'Line'));
    delete_line(get_param(ph_t3.Inport(1), 'Line'));
    delete_block(t1);
    delete_block(t2);
    delete_block(t3);
    
    I_hv_comp = simOut.get('I_hv_comp_log');
    I_lv_comp = simOut.get('I_lv_comp_log');
    I_diff_relay = simOut.get('I_diff_relay_log');
    
    val_hv = extract_data(I_hv_comp);
    val_lv = extract_data(I_lv_comp);
    val_diff = extract_data(I_diff_relay);
    
    n_samples = size(val_hv, 1);
    last_samples = min(200, n_samples);
    
    rms_hv = rms(val_hv(end-last_samples+1:end, :), 1);
    rms_lv = rms(val_lv(end-last_samples+1:end, :), 1);
    rms_diff = rms(val_diff(end-last_samples+1:end, :), 1);
    
    fprintf('\nRMS Compensated Currents (p.u.):\n');
    fprintf('  HV Compensated Phase RMS: [%.4f, %.4f, %.4f]\n', rms_hv(1), rms_hv(2), rms_hv(3));
    fprintf('  LV Compensated Phase RMS: [%.4f, %.4f, %.4f]\n', rms_lv(1), rms_lv(2), rms_lv(3));
    fprintf('  Relay I_diff Phase RMS:   [%.4f, %.4f, %.4f]\n', rms_diff(1), rms_diff(2), rms_diff(3));
    fprintf('  Max Relay I_diff Peak:   [%.4f, %.4f, %.4f]\n', ...
        max(abs(val_diff(end-last_samples+1:end, 1))), ...
        max(abs(val_diff(end-last_samples+1:end, 2))), ...
        max(abs(val_diff(end-last_samples+1:end, 3))));
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end

end

% Helper function to extract numerical matrix
function val = extract_data(var)
    if isa(var, 'double')
        if size(var, 2) == 4
            val = var(:, 2:4);
        else
            val = var;
        end
    else
        val = var.Data;
    end
end
