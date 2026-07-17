% print_compiled_sample_times.m
% Compile the model and query the actual compiled sample times of the blocks in the DWT-LSTM chain

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Start model compilation (required to query CompiledSampleTime)
    fprintf('Compiling model using feval...\n');
    feval(model, [], [], [], 'compile');
    
    % Subsystem port 1
    subsys = [model '/Hybrid 87T Relay'];
    ph_subsys = get_param(subsys, 'PortHandles');
    st_subsys = get_param(ph_subsys.Inport(1), 'CompiledSampleTime');
    
    % Buffer block port 1
    b1 = [model '/Hybrid 87T Relay/I_diff_window'];
    ph_b1 = get_param(b1, 'PortHandles');
    st_b1 = get_param(ph_b1.Inport(1), 'CompiledSampleTime');
    
    % Stateflow chart port 1
    dwt = [model '/Hybrid 87T Relay/DWT Feature Extraction'];
    ph_dwt = get_param(dwt, 'PortHandles');
    st_dwt = get_param(ph_dwt.Inport(1), 'CompiledSampleTime');
    
    % Terminate model compilation
    feval(model, [], [], [], 'term');
    fprintf('Model compilation terminated.\n\n');
    
    % Helper to print sample time
    print_st('Hybrid 87T Relay Inport 1', st_subsys);
    print_st('I_diff_window Inport 1    ', st_b1);
    print_st('DWT Chart Inport 1        ', st_dwt);
    
catch ME
    % Make sure we terminate compilation if it failed
    try
        feval(model, [], [], [], 'term');
    catch
    end
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end

function print_st(label, st)
    if iscell(st)
        fprintf('%s: Cell of size %s\n', label, mat2str(size(st)));
        for i = 1:numel(st)
            print_st(sprintf('%s{%d}', label, i), st{i});
        end
    elseif isnumeric(st)
        if numel(st) == 1
            fprintf('%s: %.6f s (%.1f Hz)\n', label, st, 1/st);
        elseif numel(st) == 2
            fprintf('%s: [%.6f, %.6f] s (%.1f Hz)\n', label, st(1), st(2), 1/st(1));
        else
            fprintf('%s: %s\n', label, mat2str(st));
        end
    else
        fprintf('%s: unknown type\n', label);
    end
end
