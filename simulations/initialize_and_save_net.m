% initialize_and_save_net.m
% Replaces the sequence input layer with MinLength = 1, initializes the dlnetwork, and saves it

try
    load('live_relay_ai_20260712.mat','net');
    
    % Replace input layer to remove sequence length restriction
    new_layer = sequenceInputLayer(9, 'Name', 'input', 'MinLength', 1);
    net = replaceLayer(net, 'input', new_layer);
    
    % Try initializing with CTB format (default for MATLAB sequence layers)
    fprintf('Attempting to initialize with CTB format (size [9, 32, 1])...\n');
    try
        x_ctb = dlarray(zeros(9, 32, 1), 'CTB');
        net_ctb = initialize(net, x_ctb);
        fprintf('  Success! Network initialized with CTB.\n');
        net = net_ctb;
    catch ME
        fprintf('  Failed CTB initialization: %s\n', ME.message);
        
        % Try initializing with BTC format
        fprintf('\nAttempting to initialize with BTC format (size [1, 32, 9])...\n');
        try
            x_btc = dlarray(zeros(1, 32, 9), 'BTC');
            net_btc = initialize(net, x_btc);
            fprintf('  Success! Network initialized with BTC.\n');
            net = net_btc;
        catch ME2
            fprintf('  Failed BTC initialization: %s\n', ME2.message);
        end
    end
    
    % Save the initialized network back to the MAT file
    save('live_relay_ai_20260712.mat', 'net');
    fprintf('\nSaved initialized network to live_relay_ai_20260712.mat.\n');
    
catch ME
    disp(['Error: ' ME.message]);
end
