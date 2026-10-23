function check_ct_physical_ratios()
% check_ct_physical_ratios.m
% Let's load the model, run normal operation, print variable types, and calculate ratios.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Set normal operation
    set_param([model '/Internal_Fault1'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    
    ph = get_param([model '/Hybrid 87T Relay'], 'PortHandles');
    l_hv = get_param(ph.Inport(1), 'Line');
    src_port_hv = get_param(l_hv, 'SrcPortHandle');
    l_lv = get_param(ph.Inport(2), 'Line');
    src_port_lv = get_param(l_lv, 'SrcPortHandle');
    
    % Add To Workspace blocks in the root
    t1 = add_block('built-in/ToWorkspace', [model '/ToWorkspace_HV_sec']);
    set_param(t1, 'VariableName', 'I_sec_hv_log', 'SaveFormat', 'Array');
    t2 = add_block('built-in/ToWorkspace', [model '/ToWorkspace_LV_sec']);
    set_param(t2, 'VariableName', 'I_sec_lv_log', 'SaveFormat', 'Array');
    
    ph_t1 = get_param(t1, 'PortHandles');
    ph_t2 = get_param(t2, 'PortHandles');
    
    add_line(model, src_port_hv, ph_t1.Inport(1), 'autorouting', 'on');
    add_line(model, src_port_lv, ph_t2.Inport(1), 'autorouting', 'on');
    
    fprintf('Running simulation of Normal Operation...\n');
    simOut = sim(model, 'StopTime', '0.2', 'ReturnWorkspaceOutputs', 'on');
    
    % Delete temporary blocks
    delete_line(get_param(ph_t1.Inport(1), 'Line'));
    delete_line(get_param(ph_t2.Inport(1), 'Line'));
    delete_block(t1);
    delete_block(t2);
    
    I_prim = simOut.get('I_primary_abc');
    I_sec = simOut.get('I_secondary_abc');
    I_sec_hv = simOut.get('I_sec_hv_log');
    I_sec_lv = simOut.get('I_sec_lv_log');
    
    fprintf('Variable Types:\n');
    fprintf('  I_primary_abc: %s, size: %s\n', class(I_prim), mat2str(size(I_prim)));
    fprintf('  I_secondary_abc: %s, size: %s\n', class(I_sec), mat2str(size(I_sec)));
    fprintf('  I_sec_hv_log: %s, size: %s\n', class(I_sec_hv), mat2str(size(I_sec_hv)));
    fprintf('  I_sec_lv_log: %s, size: %s\n', class(I_sec_lv), mat2str(size(I_sec_lv)));
    
    val_prim = extract_data(I_prim);
    val_sec = extract_data(I_sec);
    val_sec_hv = extract_data(I_sec_hv);
    val_sec_lv = extract_data(I_sec_lv);
    
    n_samples = size(val_prim, 1);
    last_samples = min(200, n_samples);
    
    rms_prim = rms(val_prim(end-last_samples+1:end, :), 1);
    rms_sec = rms(val_sec(end-last_samples+1:end, :), 1);
    rms_sec_hv = rms(val_sec_hv(end-last_samples+1:end, :), 1);
    rms_sec_lv = rms(val_sec_lv(end-last_samples+1:end, :), 1);
    
    fprintf('\nRMS Current Values:\n');
    fprintf('  Primary HV line RMS: %.4f A\n', mean(rms_prim));
    fprintf('  Primary LV line RMS: %.4f A\n', mean(rms_sec));
    fprintf('  CT Secondary HV RMS: %.4f A\n', mean(rms_sec_hv));
    fprintf('  CT Secondary LV RMS: %.4f A\n', mean(rms_sec_lv));
    
    fprintf('\nCalculated CT Ratios:\n');
    fprintf('  HV CT Ratio: %.4f (Expected: 400.0)\n', mean(rms_prim) / mean(rms_sec_hv));
    fprintf('  LV CT Ratio: %.4f (Expected: 8363.636 or 18400.0)\n', mean(rms_sec) / mean(rms_sec_lv));
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end

end

% Helper function to extract numerical matrix
function val = extract_data(var)
    if isa(var, 'timeseries')
        val = var.Data;
    elseif isstruct(var)
        val = var.signals.values;
    elseif isa(var, 'double')
        % For 'Array' format, column 1 is time if it is 2D and has 4 columns (time + 3 phases)
        if size(var, 2) == 4
            val = var(:, 2:4);
        else
            val = var;
        end
    else
        error('Unknown type: %s', class(var));
    end
end
