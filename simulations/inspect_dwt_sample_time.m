% inspect_dwt_sample_time.m
% Inspect the sample times of the DWT feature extraction chain in Simulink

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    b1 = [model '/Hybrid 87T Relay/I_diff_window'];
    dwt = [model '/Hybrid 87T Relay/DWT Feature Extraction'];
    b2 = [model '/Hybrid 87T Relay/Feature Window'];
    lstm = [model '/Hybrid 87T Relay/LSTM Predict'];
    
    fprintf('Block SampleTimes:\n');
    fprintf('  I_diff_window: "%s"\n', get_param(b1, 'SampleTime'));
    fprintf('  DWT Chart    : "%s"\n', get_param(dwt, 'SampleTime'));
    fprintf('  Feature Window: "%s"\n', get_param(b2, 'SampleTime'));
    fprintf('  LSTM Predict  : "%s"\n', get_param(lstm, 'SampleTime'));
    
catch ME
    disp(['Error: ' ME.message]);
end
