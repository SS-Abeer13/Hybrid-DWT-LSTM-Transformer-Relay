% inspect_buffers.m
% Get parameters of buffer blocks in the model

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    b1 = [model '/Hybrid 87T Relay/I_diff_window'];
    b2 = [model '/Hybrid 87T Relay/Feature Window'];
    
    fprintf('Block "%s":\n', b1);
    fprintf('  N (Buffer size): %s\n', get_param(b1, 'N'));
    fprintf('  V (Overlap): %s\n', get_param(b1, 'V'));
    
    fprintf('Block "%s":\n', b2);
    fprintf('  N (Buffer size): %s\n', get_param(b2, 'N'));
    fprintf('  V (Overlap): %s\n', get_param(b2, 'V'));
    
catch ME
    disp(['Error: ' ME.message]);
end
