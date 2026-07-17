% inspect_switch_mask.m
% Inspect the mask parameters and initialization commands of the Manual Switch block

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    blk = [model '/Hybrid 87T Relay/Manual Switch'];
    
    fprintf('Block: %s\n', blk);
    fprintf('Mask: %s\n', get_param(blk, 'Mask'));
    
    names = get_param(blk, 'MaskNames');
    vals = get_param(blk, 'MaskValues');
    
    fprintf('\nMask Parameters:\n');
    for i = 1:numel(names)
        fprintf('  %s = "%s"\n', names{i}, vals{i});
    end
    
    fprintf('\nMask Initialization:\n');
    disp(get_param(blk, 'MaskInitialization'));
    
catch ME
    disp(['Error: ' ME.message]);
end
