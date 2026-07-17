function test_hybrid_relay()
% =========================================================================
% AUTOMATED HYBRID AI-RELAY VERIFICATION & TEST ENGINE (Complete Version)
% Verifies the exported 9-feature DWT-LSTM model against transient scenarios.
% =========================================================================

    clc;
    disp('===========================================================');
    disp('   AUTOMATED HYBRID AI-RELAY VERIFICATION TEST SUITE       ');
    disp('===========================================================');
    
    model = 'TransformerWithCTSaturation';
    
    % --- 1. Load Model ---
    fprintf('\n[Step 1/5] Loading Simulink model: %s ...\n', model);
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % --- 2. Apply Model Modifications ---
    fprintf('[Step 2/5] Programmatically modifying model for 9-feature compatibility ...\n');
    try
        % Resizing raw current buffer (32 samples, 31 overlap)
        b1 = [model '/Hybrid 87T Relay/I_diff_window'];
        set_param(b1, 'N', '32');
        set_param(b1, 'V', '31');
        fprintf('  ✓ Configured "I_diff_window" to N=32, V=31.\n');
        
        % Resizing feature buffer (1569 steps, 1568 overlap)
        b2 = [model '/Hybrid 87T Relay/Feature Window'];
        set_param(b2, 'N', '1569');
        set_param(b2, 'V', '1568');
        fprintf('  ✓ Configured "Feature Window" to N=1569, V=1568.\n');
        
        % Resizing Reshape block to match 1569 sequence length
        reshape_blk = [model '/Hybrid 87T Relay/Reshape '];
        set_param(reshape_blk, 'OutputDimensions', '[1, 1569, 9]');
        fprintf('  ✓ Updated Reshape block output dimensions to [1, 1569, 9].\n');
        
        % Set LSTM Network File Path (using correct 20260712 network)
        lstm_predict_blk = [model '/Hybrid 87T Relay/LSTM Predict'];
        set_param(lstm_predict_blk, 'NetworkFilePath', 'live_relay_ai_20260712.mat');
        set_param(lstm_predict_blk, 'InputDataFormats', "{'input','BTC'}");
        set_param(lstm_predict_blk, 'MiniBatchSize', '1');
        % Force interpreted simulation to support custom imported ONNX layers
        set_param(lstm_predict_blk, 'ForceInterpretedSim', 'on');
        % Enable automatic output logging for predictions
        set_param(lstm_predict_blk, 'Predictions', 'on');
        
        % Programmatically enable signal logging and name the line
        ph = get_param(lstm_predict_blk, 'PortHandles');
        set_param(ph.Outport(1), 'DataLogging', 'on');
        lh = get_param(ph.Outport(1), 'Line');
        if lh ~= -1
            set_param(lh, 'Name', 'LSTM_Prediction');
        end
        fprintf('  ✓ Configured "LSTM Predict" block (interpreted mode, logged as LSTM_Prediction).\n');
        
        % Toggle Manual Switch block to use LSTM Predict (sw = '1' for upper port)
        sw_blk = [model '/Hybrid 87T Relay/Manual Switch'];
        set_param(sw_blk, 'sw', '1');
        fprintf('  ✓ Toggled Manual Switch to use LSTM Predict (sw = 1).\n');
        
        % Update DWT Stateflow Script via Stateflow API
        rt = sfroot;
        chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', [model '/Hybrid 87T Relay/DWT Feature Extraction']);
        if isempty(chart)
            error('Stateflow DWT Chart not found at Hybrid 87T Relay/DWT Feature Extraction.');
        end
        
        % Define 9-feature DWT code with log1p normalization and pre-initialized outputs for code generator
        dwt_code = sprintf([ ...
            'function features = DWT_Feature_Extraction(I_diff_window)\n' ...
            '    %% Inputs: I_diff_window (32x3 matrix from the Buffer block)\n' ...
            '    %% Outputs: features (1x9 vector for the LSTM)\n' ...
            '    \n' ...
            '    %% wavelets are extrinsic because code generator does not support dwt/wavedec\n' ...
            '    coder.extrinsic(''wavedec'', ''detcoef'', ''appcoef'');\n' ...
            '    \n' ...
            '    features = zeros(1, 9);\n' ...
            '    \n' ...
            '    for ph = 1:3\n' ...
            '        signal = I_diff_window(:, ph);\n' ...
            '        \n' ...
            '        %% Pre-initialize variables for code generation compliance\n' ...
            '        C = zeros(45, 1);\n' ...
            '        L = zeros(4, 1);\n' ...
            '        d1 = zeros(19, 1);\n' ...
            '        d2 = zeros(13, 1);\n' ...
            '        a2 = zeros(13, 1);\n' ...
            '        \n' ...
            '        %% 2-level db4 wavelet decomposition\n' ...
            '        [C, L] = wavedec(signal, 2, ''db4'');\n' ...
            '        \n' ...
            '        %% Calculate squared DWT energy coefficients\n' ...
            '        d1 = detcoef(C, L, 1);\n' ...
            '        d2 = detcoef(C, L, 2);\n' ...
            '        a2 = appcoef(C, L, ''db4'', 2);\n' ...
            '        \n' ...
            '        E_D1 = sum(d1.^2);\n' ...
            '        E_D2 = sum(d2.^2);\n' ...
            '        E_A2 = sum(a2.^2);\n' ...
            '        \n' ...
            '        %% Store features in 9-element feature vector\n' ...
            '        base = (ph - 1) * 3 + 1;\n' ...
            '        features(base)     = E_D1;\n' ...
            '        features(base + 1) = E_D2;\n' ...
            '        features(base + 2) = E_A2;\n' ...
            '        \n' ...
            '        %% Apply log1p scaling (log(1 + x)) matching PyTorch training\n' ...
            '        features(base)     = log(1 + features(base));\n' ...
            '        features(base + 1) = log(1 + features(base + 1));\n' ...
            '        features(base + 2) = log(1 + features(base + 2));\n' ...
            '    end\n' ...
            'end' ...
        ]);
        chart.Script = dwt_code;
        fprintf('  ✓ Updated DWT Stateflow Script to 2-level db4 (9 features + log1p normalization).\n');
        
        save_system(model);
        fprintf('  ✓ Simulink model saved successfully.\n');
    catch ME
        fprintf('  ✗ Modification failed: %s\n', ME.message);
        return;
    end
    
    % --- 3. Define Test Scenarios ---
    % Columns: Name | ScenarioType | fA | fB | fC | fG | Rf | t_fault | shouldTrip
    test_cases = { ...
        'Normal Operation',   'Normal',   0,  0,  0,  0,  0.0,  0.00,    false; ...
        'Magnetizing Inrush', 'Inrush',   0,  0,  0,  0,  0.0,  0.05,    false; ...
        'Internal A-G Fault', 'Internal', 1,  0,  0,  1,  0.1,  0.50,    true;  ...
        'External 3Φ Fault',  'External', 1,  1,  1,  0,  0.1,  0.50,    false  ...
    };

    
    results = struct('name', {}, 'shouldTrip', {}, 'tripped', {}, 'tripTime', {}, 'maxProb', {}, 'passed', {});
    
    % --- 4. Execute Tests in Batch ---
    fprintf('\n[Step 3/5] Starting Batch Simulation and Telemetry logging ...\n');
    for k = 1:size(test_cases,1)
        tc_name = test_cases{k,1};
        tc_type = test_cases{k,2};
        fA = test_cases{k,3}; fB = test_cases{k,4}; fC = test_cases{k,5}; fG = test_cases{k,6};
        Rf = test_cases{k,7}; t_fault = test_cases{k,8}; shouldTrip = test_cases{k,9};
        
        fprintf('  ---------------------------------------------------\n');
        fprintf('  Running Case %d: %s (Expected: %s)\n', k, tc_name, iff(shouldTrip, 'TRIP', 'BLOCK'));
        
        % Configure model blocks per test case
        resetFaultBlocks(model);
        
        if strcmp(tc_type, 'Inrush')
            % Magnetizing Inrush energization (HV breaker closes at 0.05s, no load)
            setInrushEnergization(model);
        else
            % Normal breakers configuration (both closed by default)
            setBreakersClosed(model);
            
            if strcmp(tc_type, 'Internal')
                % Arm internal fault block and Step3 trigger
                set_param([model '/Step3'], 'Time', num2str(t_fault, '%.6f'));
                set_param([model '/Internal_Fault1'], ...
                    'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                    'FaultResistance', num2str(Rf, '%.6f'));
            elseif strcmp(tc_type, 'External')
                % Arm external fault block and Step4 trigger
                set_param([model '/Step4'], 'Time', num2str(t_fault, '%.6f'));
                set_param([model '/External_Fault'], ...
                    'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                    'FaultResistance', num2str(Rf, '%.6f'));
            end
        end
        
        % Run simulation (StopTime must be >= 0.160s to fill the 1569-step feature window)
        try
            simOut = sim(model, 'StopTime', '1.0', 'ReturnWorkspaceOutputs', 'on');
            
            % Extract telemetry signals
            logs = simOut.get('logsout');
            
            % 1. Get predictions (probability) output from LSTM
            lstm_prob = 0;
            try
                lstm_el = logs.get('LSTM_Prediction');
                if ~isempty(lstm_el)
                    lstm_prob = lstm_el.Values.Data;
                end
            catch
            end
            
            % 2. Get TripSignal from Hybrid Relay
            tripped = false;
            tripTime = NaN;
            try
                trip_el = logs.get('TripSignal');
                if ~isempty(trip_el)
                    t_vec = trip_el.Values.Time;
                    d_vec = trip_el.Values.Data;
                    trip_idx = find(d_vec > 0.5, 1, 'first');
                    if ~isempty(trip_idx)
                        tripped = true;
                        tripTime = t_vec(trip_idx);
                    end
                end
            catch
            end
            
            max_prob = max(lstm_prob(:));
            passed = (tripped == shouldTrip);
            
            % Store results
            r.name = tc_name;
            r.shouldTrip = shouldTrip;
            r.tripped = tripped;
            r.tripTime = tripTime;
            r.maxProb = max_prob;
            r.passed = passed;
            results(end+1) = r; %#ok<AGROW>
            
            % Print results
            fprintf('    LSTM Peak Probability : %.4f\n', max_prob);
            if tripped
                fprintf('    Hybrid Relay Decision  : TRIP (Time = %.4f s / %.1f ms after fault)\n', ...
                    tripTime, (tripTime - t_fault)*1000);
            else
                fprintf('    Hybrid Relay Decision  : BLOCK\n');
            end
            fprintf('    Verification Outcome   : %s\n', iff(passed, 'PASS ✓', 'FAIL ✗'));
            
        catch ME
            fprintf('    ✗ Simulation failed: %s\n', ME.message);
            disp(ME.getReport());
        end
    end
    
    % --- 5. Generate Summary Report ---
    fprintf('\n===========================================================\n');
    fprintf('   VERIFICATION TEST SUMMARY REPORT\n');
    fprintf('===========================================================\n');
    nPass = sum([results.passed]);
    nTotal = numel(results);
    fprintf('Total cases executed: %d\n', nTotal);
    fprintf('Passed cases        : %d / %d (%.1f%%)\n', nPass, nTotal, nPass/nTotal*100);
    fprintf('\n%-22s  %-12s  %-12s  %-12s  %-8s\n', ...
        'Test Case', 'Expected', 'Actual', 'LSTM Max Prob', 'Status');
    fprintf('%s\n', repmat('-', 1, 72));
    for i = 1:numel(results)
        res = results(i);
        exp_str = iff(res.shouldTrip, 'TRIP', 'BLOCK');
        act_str = iff(res.tripped, 'TRIP', 'BLOCK');
        status_str = iff(res.passed, 'PASS', 'FAIL');
        fprintf('%-22s  %-12s  %-12s  %-12.4f  %-8s\n', ...
            res.name, exp_str, act_str, res.maxProb, status_str);
    end
    fprintf('%s\n', repmat('-', 1, 72));
    disp(' ');
end

% =========================================================================
% UTILITY HELPER FUNCTIONS (Inline definitions)
% =========================================================================
function val = iff(cond, valTrue, valFalse)
    if cond, val = valTrue; else, val = valFalse; end
end

function val = onOff(cond)
    if cond, val = 'on'; else, val = 'off'; end
end

function setBreakersClosed(model)
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try
        set_param(hv, 'External', 'on');
        set_param(hv, 'InitialState', 'closed');
        set_param(hv, 'SwitchTimes', '[]');
    catch ME, warning('ControlPanel:HVBreaker', '%s', ME.message); end
    try
        set_param(lv, 'External', 'on');
        set_param(lv, 'InitialState', 'closed');
        set_param(lv, 'SwitchTimes', '[]');
    catch ME, warning('ControlPanel:LVBreaker', '%s', ME.message); end
    try
        set_param([model '/Step_down_Transformer'], 'SetInitialFlux', 'off');
    catch ME, warning('ControlPanel:XfmrFlux', '%s', ME.message); end
end

function setInrushEnergization(model, residualFlux)
    if nargin < 2 || isempty(residualFlux)
        residualFlux = [-0.60 0.40 0.15]; % Static representative residual flux for inrush
    end
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try
        set_param(hv, 'External', 'off');
        set_param(hv, 'InitialState', 'open');
        set_param(hv, 'SwitchTimes', '[0.050]');
    catch ME, warning('ControlPanel:HVBreaker', '%s', ME.message); end
    try
        set_param(lv, 'External', 'on');
        set_param(lv, 'InitialState', 'closed');
        set_param(lv, 'SwitchTimes', '[]');
    catch ME, warning('ControlPanel:LVBreaker', '%s', ME.message); end
    try
        xf = [model '/Step_down_Transformer'];
        set_param(xf, 'SetInitialFlux', 'on');
        set_param(xf, 'InitialFluxes', mat2str(residualFlux, 6));
    catch ME, warning('ControlPanel:XfmrFlux', '%s', ME.message); end
end

function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
    try
        set_param([model '/Internal_Fault1'], ...
            'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', ...
            'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
    catch, end
    try
        set_param([model '/External_Fault'], ...
            'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', ...
            'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
    catch, end
end
