% verify_logging.m
% Verify if the logging is enabled on the LSTM Predict block's output port

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    blk = [model '/Hybrid 87T Relay/LSTM Predict'];
    ph = get_param(blk, 'PortHandles');
    
    fprintf('Block Outport Count: %d\n', numel(ph.Outport));
    for i = 1:numel(ph.Outport)
        fprintf('  Port %d:\n', i);
        fprintf('    DataLogging: %s\n', get_param(ph.Outport(i), 'DataLogging'));
        fprintf('    Name: "%s"\n', get_param(ph.Outport(i), 'Name'));
        fprintf('    SignalNameFromLabel: "%s"\n', get_param(ph.Outport(i), 'SignalNameFromLabel'));
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
