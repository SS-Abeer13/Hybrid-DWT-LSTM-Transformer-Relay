% check_switch_and_off.m
% Check the Manual Switch block position and OFF block value

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
    off_blk = [model '/Hybrid 87T Relay/OFF'];
    
    fprintf('Manual Switch block position (sw): "%s"\n', get_param(sw_blk, 'sw'));
    fprintf('OFF constant block value: "%s"\n', get_param(off_blk, 'Value'));
    
catch ME
    disp(['Error: ' ME.message]);
end
