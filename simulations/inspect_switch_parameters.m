% inspect_switch_parameters.m
% Inspect all parameters of the Manual Switch block

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    blk = [model '/Hybrid 87T Relay/Manual Switch'];
    params = get_param(blk, 'ObjectParameters');
    fields = fieldnames(params);
    
    fprintf('Block: %s\n', blk);
    fprintf('Parameters and their values:\n');
    fprintf('%s\n', repmat('-', 1, 50));
    
    for i = 1:numel(fields)
        name = fields{i};
        try
            val = get_param(blk, name);
            if ischar(val) || isnumeric(val) || islogical(val)
                fprintf('  %-25s: %s\n', name, cellstr(num2str(val)));
            else
                fprintf('  %-25s: [non-printable type]\n', name);
            end
        catch
        end
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
