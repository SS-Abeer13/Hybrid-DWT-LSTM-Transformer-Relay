load_system('TransformerWithCTSaturation');

blk = 'TransformerWithCTSaturation/Hybrid 87T Relay/LSTM Predict';

load('live_relay_ai_20260712.mat','net');
disp(net.InputNames)
set_param(blk, 'NetworkFilePath', 'live_relay_ai_20260712.mat');
set_param(blk, 'InputDataFormats', "{'input','BTC'}");
set_param(blk, 'MiniBatchSize', '1');

