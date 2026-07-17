% test_scale_with_noise_reduction.m
% Reduce the noise gain in the model by a factor of 400, run simulation, and check LSTM prediction.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % Scale down the Noise Gain blocks by a factor of 400
    fprintf('Scaling down Noise Gain blocks in Noise Merging Unit...\n');
    base_noise = 0.02566;
    scaled_noise = base_noise / 400;
    
    for ch = 1:6
        block_path = sprintf('%s/Noise Merging Unit/Noise_Gain_%d', model, ch);
        if getSimulinkBlockHandle(block_path) ~= -1
            set_param(block_path, 'Gain', num2str(scaled_noise, '%.8f'));
        end
    end
    
    % Save model
    save_system(model);
    fprintf('✓ Model noise gains updated and saved.\n');
    
    % Run simulation for Case 3 (Internal Fault)
    fprintf('Running simulation of Internal Fault with noise reduction...\n');
    set_param([model '/Step3'], 'Time', '0.50');
    % Close HV and LV breakers
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    set_param(hv, 'External', 'on');
    set_param(hv, 'InitialState', 'closed');
    set_param(hv, 'SwitchTimes', '[]');
    set_param(lv, 'External', 'on');
    set_param(lv, 'InitialState', 'closed');
    set_param(lv, 'SwitchTimes', '[]');
    
    % Set internal fault phase A to ground
    set_param([model '/Internal_Fault1'], ...
        'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on', ...
        'FaultResistance', '0.1');
    
    simOut = sim(model, 'StopTime', '1.0', 'ReturnWorkspaceOutputs', 'on');
    logs = simOut.get('logsout');
    feat_el = logs.get('DWT_Features');
    
    if ~isempty(feat_el)
        feat_data = feat_el.Values.Data;
        feat_time = feat_el.Values.Time;
        save('scaled_features_test.mat', 'feat_data', 'feat_time');
        fprintf('✓ Simulation done. Saved to scaled_features_test.mat.\n');
    else
        fprintf('⚠ Failed to log features!\n');
    end
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end
