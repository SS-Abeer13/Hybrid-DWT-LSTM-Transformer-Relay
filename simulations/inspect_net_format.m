% inspect_net_format.m
% Inspect the input layers and formats of the imported net in live_relay_ai_20260712.mat

try
    load('live_relay_ai_20260712.mat','net');
    
    fprintf('Network Inputs:\n');
    disp(net.InputNames);
    
    % Get properties of the first layer
    layer1 = net.Layers(1);
    fprintf('\nFirst layer properties:\n');
    disp(layer1);
    
    % Let's see if there is any other property or information on expected format
    try
        fprintf('Network Input Sizes:\n');
        disp(net.InputSizes);
    catch
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
