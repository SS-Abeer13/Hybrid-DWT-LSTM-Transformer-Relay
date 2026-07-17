% test_predict_format.m
% Test network prediction with different formats in MATLAB to see what formats are supported

try
    load('live_relay_ai_20260712.mat','net');
    
    % Let's check the InputDataFormats property of net if it exists
    try
        fprintf('Network InputDataFormats:\n');
        disp(net.InputDataFormats);
    catch
    end
    
    % Test 1: [1, 1569, 9] in BTC format
    fprintf('\nTest 1: Input size [1, 1569, 9] (dlarray with format "BTC")...\n');
    try
        x1 = dlarray(ones(1, 1569, 9), 'BTC');
        y1 = predict(net, x1);
        fprintf('  Success! Output size: %s, format: "%s"\n', mat2str(size(y1)), y1.dims);
    catch ME
        fprintf('  Failed: %s\n', ME.message);
    end
    
    % Test 2: [9, 1569, 1] in CTB format
    fprintf('\nTest 2: Input size [9, 1569, 1] (dlarray with format "CTB")...\n');
    try
        x2 = dlarray(ones(9, 1569, 1), 'CTB');
        y2 = predict(net, x2);
        fprintf('  Success! Output size: %s, format: "%s"\n', mat2str(size(y2)), y2.dims);
    catch ME
        fprintf('  Failed: %s\n', ME.message);
    end
    
    % Test 3: [9, 1569] in CT format
    fprintf('\nTest 3: Input size [9, 1569] (dlarray with format "CT")...\n');
    try
        x3 = dlarray(ones(9, 1569), 'CT');
        y3 = predict(net, x3);
        fprintf('  Success! Output size: %s, format: "%s"\n', mat2str(size(y3)), y3.dims);
    catch ME
        fprintf('  Failed: %s\n', ME.message);
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
