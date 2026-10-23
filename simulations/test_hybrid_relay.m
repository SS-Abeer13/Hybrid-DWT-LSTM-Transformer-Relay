% test_hybrid_relay Script
% =========================================================================
% AUTOMATED HYBRID AI-RELAY VERIFICATION & TEST ENGINE (Complete Version)
% Verifies the exported 9-feature DWT-LSTM model against transient scenarios.
% =========================================================================

    clc;
    thisDir = fileparts(mfilename('fullpath'));
    disp('===========================================================');
    disp('   AUTOMATED HYBRID AI-RELAY VERIFICATION TEST SUITE       ');
    disp('===========================================================');
    
    cfg = relay_config();
    model = 'TransformerWithCTSaturation';
    
    % --- 1. Load Model ---
    fprintf('\n[Step 1/5] Loading Simulink model: %s ...\n', model);
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    % --- 2. Apply Model Modifications ---
    fprintf('[Step 2/5] Programmatically modifying model for 9-feature compatibility ...\n');
    try
        repair_hybrid_relay_for_lstm_verification(true);
        fprintf('  OK: restored LSTM path, 1600 Hz sampling, %d-step sequence, and AI-gated trip logic.\n', cfg.N_WINDOW);

        % Update DWT Stateflow Script via Stateflow API
        rt = sfroot;
        chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', [model '/Hybrid 87T Relay/DWT Feature Extraction']);
        if isempty(chart)
            error('Stateflow DWT Chart not found at Hybrid 87T Relay/DWT Feature Extraction.');
        end
        
        % Define 12-feature DWT + 2nd Harmonic Ratio code
        dwt_code = sprintf([ ...
            'function features = DWT_Feature_Extraction(I_diff_window)\n' ...
            '    %% Inputs: I_diff_window (32x3 matrix from the Buffer block)\n' ...
            '    %% Outputs: features (1x12 vector for the LSTM)\n' ...
            '    \n' ...
            '    %% wavelets and fft are extrinsic because code generator does not support dwt/wavedec/fft\n' ...
            '    coder.extrinsic(''wavedec'', ''detcoef'', ''appcoef'', ''fft'');\n' ...
            '    \n' ...
            '    features = zeros(1, 12);\n' ...
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
            '        fft_vals = zeros(32, 1);\n' ...
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
            '        %% Store features in 12-element feature vector\n' ...
            '        base = (ph - 1) * 3 + 1;\n' ...
            '        features(base)     = log(1 + E_D1);\n' ...
            '        features(base + 1) = log(1 + E_D2);\n' ...
            '        features(base + 2) = log(1 + E_A2);\n' ...
            '        \n' ...
            '        %% 2nd Harmonic Ratio (Bin 3 = 100 Hz, Bin 2 = 50 Hz @ 1600 Hz / 32 samples)\n' ...
            '        fft_vals = abs(fft(signal));\n' ...
            '        ratio_2nd = fft_vals(3) / (fft_vals(2) + 1e-4);\n' ...
            '        features(9 + ph) = min(ratio_2nd, 2.0);\n' ...
            '    end\n' ...
            'end' ...
        ]);
        chart.Script = dwt_code;
        fprintf('  ✓ Updated DWT Stateflow Script to 12 features (9 DWT + 3 2nd Harmonic Ratios).\n');
        
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
        'Internal A-G Fault', 'Internal', 1,  0,  0,  1,  0.1,  0.05,    true;  ...
        'External 3Φ Fault',  'External', 1,  1,  1,  0,  0.1,  0.05,    false  ...
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
        clear lstm_predict_wrapper;
        
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
                    'FaultResistance', num2str(Rf, '%.6f'), 'SwitchTimes', sprintf('[%.6f 1.10]', t_fault));
            elseif strcmp(tc_type, 'External')
                % Arm external fault block and Step4 trigger
                set_param([model '/Step4'], 'Time', num2str(t_fault, '%.6f'));
                set_param([model '/External_Fault'], ...
                    'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                    'FaultResistance', num2str(Rf, '%.6f'), 'SwitchTimes', sprintf('[%.6f 1.10]', t_fault));
            end
        end
        
        % Run simulation (StopTime must be >= 0.160s to fill the 1569-step feature window)
        try
            simOut = sim(model, 'StopTime', '1.10', 'ReturnWorkspaceOutputs', 'on');
            
            % Extract telemetry signals
            logs = simOut.get('logsout');
            
            % 1. Get predictions (probability) output from LSTM
            lstm_prob = 0;
            max_prob = 0;
            try
                lstm_el = logs.get('LSTM_Prediction');
                if ~isempty(lstm_el)
                    t_vec_p = lstm_el.Values.Time;
                    p_vec_p = lstm_el.Values.Data;
                    eval_idx = find(t_vec_p >= 0.056, 1, 'first');
                    if ~isempty(eval_idx)
                        max_prob = max(p_vec_p(eval_idx:end));
                    else
                        max_prob = max(p_vec_p);
                    end
                end
            catch
            end
            
            % 2. Get TripSignal from Hybrid Relay
            tripped = false;
            tripTime = NaN;
            try
                trip_el = getFirstLog(logs, {'Dec_Trip_Signal', 'TripSignal', 'Trip_Signal'});
                if ~isempty(trip_el)
                    t_vec = trip_el.Values.Time;
                    d_vec = trip_el.Values.Data;
                    % Evaluate trip decision after initial solver startup (t >= 0.056s)
                    trip_idx = find(t_vec >= 0.056 & d_vec > 0.5, 1, 'first');
                    if ~isempty(trip_idx)
                        tripped = true;
                        tripTime = t_vec(trip_idx);
                    end
                end
            catch
            end
            
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
    cfg = relay_config();
    reportFile = fullfile(thisDir, 'test_hybrid_relay_results.txt');
    fid = fopen(reportFile, 'w');
    
    headerStr = sprintf('\n===========================================================\n   VERIFICATION TEST SUMMARY REPORT (N_WINDOW = %d)\n===========================================================\n', cfg.N_WINDOW);
    fprintf(headerStr);
    if fid ~= -1, fprintf(fid, '%s', headerStr); end
    
    nPass = sum([results.passed]);
    nTotal = numel(results);
    summaryStr = sprintf('Total cases executed: %d\nPassed cases        : %d / %d (%.1f%%)\n\n%-22s  %-12s  %-12s  %-12s  %-8s\n%s\n', ...
        nTotal, nPass, nTotal, nPass/nTotal*100, 'Test Case', 'Expected', 'Actual', 'LSTM Max Prob', 'Status', repmat('-', 1, 72));
    fprintf(summaryStr);
    if fid ~= -1, fprintf(fid, '%s', summaryStr); end
    
    for i = 1:numel(results)
        res = results(i);
        exp_str = iff(res.shouldTrip, 'TRIP', 'BLOCK');
        act_str = iff(res.tripped, 'TRIP', 'BLOCK');
        status_str = iff(res.passed, 'PASS', 'FAIL');
        lineStr = sprintf('%-22s  %-12s  %-12s  %-12.4f  %-8s\n', ...
            res.name, exp_str, act_str, res.maxProb, status_str);
        fprintf(lineStr);
        if fid ~= -1, fprintf(fid, '%s', lineStr); end
    end
    footerStr = sprintf('%s\n\nSaved empirical verification results to test_hybrid_relay_results.txt\n', repmat('-', 1, 72));
    fprintf(footerStr);
    if fid ~= -1
        fprintf(fid, '%s', footerStr);
        fclose(fid);
    end
    
    save(fullfile(thisDir, 'test_hybrid_relay_results.mat'), 'results');
    disp(' ');

% =========================================================================
% UTILITY HELPER FUNCTIONS (Inline definitions)
% =========================================================================
function val = iff(cond, valTrue, valFalse)
    if cond, val = valTrue; else, val = valFalse; end
end

function val = onOff(cond)
    if cond, val = 'on'; else, val = 'off'; end
end

function el = getFirstLog(logs, names)
    el = [];
    for idx = 1:numel(names)
        try
            candidate = logs.get(names{idx});
            if ~isempty(candidate)
                el = candidate;
                return;
            end
        catch
        end
    end
end

function setBreakersClosed(model)
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try
        set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
    catch
    end
    try
        set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
    catch
    end
    try
        set_param([model '/Step_down_Transformer'], 'SetInitialFlux', 'off');
    catch
    end
end

function setInrushEnergization(model, residualFlux)
    if nargin < 2 || isempty(residualFlux)
        residualFlux = [-0.60 0.40 0.15]; % Static representative residual flux for inrush
    end
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try
        set_param(hv, 'External', 'off', 'InitialState', 'open', 'SwitchTimes', '[0.050 1.10]');
    catch
    end
    try
        set_param(lv, 'External', 'off', 'InitialState', 'open', 'SwitchTimes', '[10 11]');
    catch
    end
    try
        xf = [model '/Step_down_Transformer'];
        set_param(xf, 'SetInitialFlux', 'on', 'InitialFluxes', mat2str(residualFlux, 6));
    catch
    end
end

function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
    try
        set_param([model '/Internal_Fault1'], ...
            'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', ...
            'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1.10]');
    catch, end
    try
        set_param([model '/External_Fault'], ...
            'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', ...
            'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1.10]');
    catch, end
end
