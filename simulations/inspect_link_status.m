% inspect_link_status.m
% Check the LinkStatus of the Hybrid 87T Relay subsystem and Manual Switch

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    subsys = [model '/Hybrid 87T Relay'];
    sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
    
    fprintf('Subsystem LinkStatus: "%s"\n', get_param(subsys, 'LinkStatus'));
    fprintf('Manual Switch LinkStatus: "%s"\n', get_param(sw_blk, 'LinkStatus'));
    
    % Try to set sw to 0
    fprintf('\nAttempting to set sw to 0...\n');
    set_param(sw_blk, 'sw', '0');
    fprintf('New sw value: "%s"\n', get_param(sw_blk, 'sw'));
    
catch ME
    disp(['Error: ' ME.message]);
end
