% Step 1: Set working directory to your thesis folder
cd('F:\Downloads\Transformer Thesis')

% Step 2: Generate live_relay_ai.mat from your ONNX model
run('ONNXBUILDER.m')

% Step 3: Verify the file was created
if exist('live_relay_ai.mat','file')
    disp('✓ live_relay_ai.mat created successfully.')
    load('live_relay_ai.mat','net');
    disp(net)
else
    error('ONNXBUILDER.m did not produce live_relay_ai.mat — see fallback below.')
end