function ControlPanel
    % =========================================================================
    % TRANSFORMER PROTECTION CONTROL PANEL WITH BATCH GENERATOR
    % =========================================================================

    % --- CONFIGURATION ---
    modelName = gcs; 
    if isempty(modelName)
        errordlg('Please open your Simulink model first!'); return;
    end
    
    % Get the root model name (in case gcs returns a subsystem path)
    modelName = bdroot(modelName);

    bgColor = [0.95 0.95 0.97];      
    panelColor = [1.0 1.0 1.0];      
    
    cNormal = [0.7 0.95 0.7];        
    cInrush = [1.0 0.87 0.6];        
    cFault  = [1.0 0.75 0.75];       
    cExternal = [0.75 0.87 1.0];     
    cRun = [0.85 0.92 1.0];
    cBatch = [0.95 0.85 1.0];        % Batch generator color
    
    cTextDark = [0.2 0.2 0.2];       
    cTextNormal = [0.15 0.5 0.15];   
    cTextInrush = [0.6 0.4 0.0];     
    cTextFault = [0.6 0.1 0.1];      
    cTextExternal = [0.1 0.3 0.6];   
    cTextBatch = [0.4 0.1 0.5];      % Batch text color
    
    % --- CREATE FIGURE (TALLER TO FIT BATCH SECTION) ---
    f = figure('Name', 'Protection Test Console', 'NumberTitle', 'off', ...
               'Position', [300, 100, 400, 680], 'MenuBar', 'none', ...
               'Resize', 'off', 'Color', bgColor);

    % --- HEADER LABEL ---
    uicontrol('Parent', f, 'Style', 'text', ...
              'Position', [20, 635, 360, 30], ...
              'String', 'TRANSFORMER PROTECTION TEST', ...
              'FontSize', 13, 'FontWeight', 'bold', ...
              'ForegroundColor', [0.2 0.3 0.5], ...
              'BackgroundColor', bgColor, ...
              'HorizontalAlignment', 'center');

    % --- MAIN PANEL FRAME ---
    p = uipanel('Parent', f, 'Title', 'Test Scenarios', ...
                'FontSize', 11, 'FontWeight', 'bold', ...
                'ForegroundColor', [0.3 0.3 0.3], ...
                'BackgroundColor', panelColor, ...
                'BorderType', 'line', 'HighlightColor', [0.7 0.7 0.7], ...
                'Position', [0.05 0.35 0.9 0.58]);

    % --- MODEL LABEL ---
    uicontrol('Parent', p, 'Style', 'text', ...
              'Position', [15, 350, 340, 22], ...
              'FontSize', 9, 'FontAngle', 'italic', ...
              'String', ['Connected Model: ' modelName], ...
              'HorizontalAlignment', 'left', ...
              'ForegroundColor', [0.4 0.4 0.4], ...
              'BackgroundColor', panelColor);

    % ================= SCENARIO BUTTONS =================
    btnX = 40; 
    startY = 290; 
    height = 42; 
    gap = 52; 
    width = 290;
    fontSize = 10;
    
    % --- BUTTON 0: NORMAL CONDITION ---
    uicontrol('Parent', p, 'Style', 'pushbutton', ...
              'Position', [btnX, startY, width, height], ...
              'String', 'NORMAL OPERATION', ...
              'BackgroundColor', cNormal, ...
              'ForegroundColor', cTextNormal, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Healthy transformer with load connected', ...
              'Callback', @(src,event) setNormal(modelName));

    % --- BUTTON 1: INRUSH ---
    uicontrol('Parent', p, 'Style', 'pushbutton', ...
              'Position', [btnX, startY - gap, width, height], ...
              'String', 'MAGNETIZING INRUSH', ...
              'BackgroundColor', cInrush, ...
              'ForegroundColor', cTextInrush, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Energization without load (inrush current test)', ...
              'Callback', @(src,event) setInrush(modelName));

    % --- BUTTON 2: INTERNAL FAULT A-G ---
    uicontrol('Parent', p, 'Style', 'pushbutton', ...
              'Position', [btnX, startY - 2*gap, width, height], ...
              'String', 'INTERNAL FAULT (A-G)', ...
              'BackgroundColor', cFault, ...
              'ForegroundColor', cTextFault, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Phase A to ground fault inside protection zone', ...
              'Callback', @(src,event) setInternalAG(modelName));

    % --- BUTTON 3: INTERNAL FAULT A-B ---
    uicontrol('Parent', p, 'Style', 'pushbutton', ...
              'Position', [btnX, startY - 3*gap, width, height], ...
              'String', 'INTERNAL FAULT (A-B)', ...
              'BackgroundColor', cFault, ...
              'ForegroundColor', cTextFault, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Phase A-B fault inside protection zone', ...
              'Callback', @(src,event) setInternalAB(modelName));

    % --- BUTTON 4: INTERNAL FAULT A-B-C ---
    uicontrol('Parent', p, 'Style', 'pushbutton', ...
              'Position', [btnX, startY - 4*gap, width, height], ...
              'String', 'INTERNAL FAULT (3-Phase)', ...
              'BackgroundColor', cFault, ...
              'ForegroundColor', cTextFault, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Three-phase fault inside protection zone', ...
              'Callback', @(src,event) setInternalABC(modelName));

    % --- BUTTON 5: EXTERNAL FAULT ---
    uicontrol('Parent', p, 'Style', 'pushbutton', ...
              'Position', [btnX, startY - 5*gap, width, height], ...
              'String', 'EXTERNAL FAULT (Through)', ...
              'BackgroundColor', cExternal, ...
              'ForegroundColor', cTextExternal, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Fault outside protection zone (should not trip)', ...
              'Callback', @(src,event) setExternalFault(modelName));

    % ================= BATCH GENERATOR PANEL =================
    pBatch = uipanel('Parent', f, 'Title', 'Training Data Generator', ...
                     'FontSize', 11, 'FontWeight', 'bold', ...
                     'ForegroundColor', [0.4 0.1 0.5], ...
                     'BackgroundColor', panelColor, ...
                     'BorderType', 'line', 'HighlightColor', [0.8 0.7 0.9], ...
                     'Position', [0.05 0.12 0.9 0.21]);

  

    % Sample count input
    uicontrol('Parent', pBatch, 'Style', 'text', ...
              'Position', [30, 70, 120, 20], ...
              'String', 'Number of Samples:', ...
              'FontSize', 9, ...
              'HorizontalAlignment', 'left', ...
              'BackgroundColor', panelColor);
    
    hSampleCount = uicontrol('Parent', pBatch, 'Style', 'edit', ...
                             'Position', [155, 70, 70, 25], ...
                             'String', '500', ...
                             'FontSize', 10, ...
                             'BackgroundColor', [1 1 1]);

    % Generate button
    uicontrol('Parent', pBatch, 'Style', 'pushbutton', ...
              'Position', [58, 15, 240, 35], ...
              'String', '⚡ GENERATE BATCH DATASET', ...
              'FontSize', 10, 'FontWeight', 'bold', ...
              'BackgroundColor', cBatch, ...
              'ForegroundColor', cTextBatch, ...
              'TooltipString', 'Generate random scenarios and save to .mat file', ...
              'Callback', @(src,event) generateBatch(modelName, hSampleCount));
    
    % ================= START SIMULATION BUTTON =================
    uicontrol('Parent', f, 'Style', 'pushbutton', ...
              'Position', [80, 15, 240, 45], ...
              'String', '▶ START SIMULATION', ...
              'FontSize', 12, 'FontWeight', 'bold', ...
              'BackgroundColor', cRun, ...
              'ForegroundColor', [0.1 0.3 0.6], ...
              'Callback', @(src,event) runSim(modelName));
end

% =========================================================================
% CALLBACK FUNCTIONS
% ========================================================================

function setNormal(model)
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: NORMAL LOAD CONDITION (Healthy Operation)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '10'); 
    set_param([model '/Step4'], 'Time', '10'); 
    % Connect the load
    set_param([model '/Load_Logic/Load_Switch'], 'Value', '1'); 
    disp('✓ Configuration complete. Ready to simulate.');
end

function setInrush(model)
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: MAGNETIZING INRUSH (No-Load Energization)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '10'); 
    set_param([model '/Step4'], 'Time', '10'); 
    % Disconnect the load to force pure magnetizing inrush
    set_param([model '/Load_Logic/Load_Switch'], 'Value', '0');     
    disp('✓ Configuration complete. Ready to simulate.');
end

function setInternalAG(model)
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: INTERNAL FAULT (Phase A-Ground)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '0.5'); % Fault strikes at 0.5s
    set_param([model '/Internal_Fault'], 'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on');
    set_param([model '/Step4'], 'Time', '10');
    set_param([model '/Load_Logic/Load_Switch'], 'Value', '1'); 
    disp('✓ Configuration complete. Ready to simulate.');
end

function setInternalAB(model)
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: INTERNAL FAULT (Phase A-B)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '0.5');
    set_param([model '/Internal_Fault'], 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'off', 'GroundFault', 'off');
    set_param([model '/Step4'], 'Time', '10');
    set_param([model '/Load_Logic/Load_Switch'], 'Value', '1'); 
    disp('✓ Configuration complete. Ready to simulate.');
end

function setInternalABC(model)
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: INTERNAL FAULT (3-Phase)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '0.5');
    set_param([model '/Internal_Fault'], 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off');
    set_param([model '/Step4'], 'Time', '10');
    set_param([model '/Load_Logic/Load_Switch'], 'Value', '1'); 
    disp('✓ Configuration complete. Ready to simulate.');
end

function setExternalFault(model)
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: EXTERNAL FAULT (Through Fault)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '0.5'); % External fault strikes at 0.5s
    set_param([model '/Load_Logic/Load_Switch'], 'Value', '1'); 
    disp('✓ Configuration complete. Ready to simulate.');
end

% Delete the setupFaultConditions(model) function entirely, it is no longer needed!

% =========================================================================
% BATCH GENERATOR FUNCTION
% =========================================================================

function generateBatch(model, hSampleCount)
    % Get number of samples
    nSamples = str2double(get(hSampleCount, 'String'));
    if isnan(nSamples) || nSamples < 1
        errordlg('Please enter a valid number of samples (e.g., 500)');
        return;
    end
    
    nSamples = round(nSamples);
    
    % Confirmation dialog
    answer = questdlg(sprintf('Generate %d random scenarios?\n\nEstimated time: ~%d seconds\n(Fast Restart disabled for Simscape compatibility)', ...
                      nSamples, round(nSamples * 1.5)), ...
                      'Confirm Batch Generation', 'Generate', 'Cancel', 'Generate');
    if ~strcmp(answer, 'Generate')
        return;
    end
    
    disp(' ');
    disp('╔═══════════════════════════════════════════════════════════╗');
    disp('║          BATCH DATASET GENERATION STARTED                 ║');
    disp('╚═══════════════════════════════════════════════════════════╝');
    fprintf('Generating %d samples...\n', nSamples);
    disp(' ');
    
    % ═══ IMPORTANT: FAST RESTART DISABLED ═══
    % Fast Restart is NOT compatible with changing Simscape electrical parameters
    % (like Fault Resistance). Each sample requires a full model recompile to
    % update the system matrix. This is slower (~1-2s per sample) but ensures
    % your dataset has TRUE diversity in fault magnitudes.
    fprintf('⚙️  Fast Restart: DISABLED (required for Simscape parameter changes)');
    fprintf('    Estimated time: ~%d seconds for %d samples', round(nSamples * 3.5), nSamples);
    disp(' ');
    
    % Initialize storage
    dataset = struct();
    dataset.metadata = struct();
    dataset.metadata.nSamples = nSamples;
    dataset.metadata.generatedDate = datetime('now');
    dataset.metadata.modelName = model;
    
    % Preallocate arrays for labels
    dataset.zone = cell(nSamples, 1);           % 'Internal', 'External', 'Inrush', 'Normal'
    dataset.faultType = cell(nSamples, 1);      % 'AG', 'BG', 'CG', 'AB', 'BC', 'CA', 'ABC', 'ABG', etc.
    dataset.faultResistance = zeros(nSamples, 1); % Ohms
    dataset.inceptionAngle = zeros(nSamples, 1);  % Degrees (0-360)
    dataset.inceptionTime = zeros(nSamples, 1);   % Seconds
    dataset.shouldTrip = false(nSamples, 1);      % Boolean: should protection operate?
    
    % Preallocate arrays for waveform data
    dataset.primaryCurrent = cell(nSamples, 1);   % Primary side currents
    dataset.secondaryCurrent = cell(nSamples, 1); % Secondary side currents
    dataset.diffCurrent = cell(nSamples, 1);      % Differential current (if available)
    dataset.tripSignal = cell(nSamples, 1);       % Protection trip signal
    dataset.simulationStatus = cell(nSamples, 1); % Success/failure tracking
    
    % Preallocate arrays for noise and mismatch data
    dataset.noiseLevel = zeros(nSamples, 1);      % Global noise level for each sample
    dataset.ctMismatch = cell(nSamples, 1);       % CT ratio mismatches (6 channels)
    
    % Progress figure
    hWait = waitbar(0, 'Initializing...', 'Name', 'Batch Generation Progress');
    
    try
        for i = 1:nSamples
            % Update progress
            if mod(i, 10) == 0
                waitbar(i/nSamples, hWait, sprintf('Generating sample %d/%d...', i, nSamples));
            end
            
            % Randomly select scenario type
            scenarioRand = rand();
            if scenarioRand < 0.15
                % 15% Normal operation
                dataset.zone{i} = 'Normal';
                dataset.faultType{i} = 'None';
                dataset.faultResistance(i) = 0;
                dataset.inceptionAngle(i) = 0;
                dataset.inceptionTime(i) = 0;
                dataset.shouldTrip(i) = false;
                configureNormalScenario(model);
                
            elseif scenarioRand < 0.30
                % 15% Inrush current
                dataset.zone{i} = 'Inrush';
                dataset.faultType{i} = 'Inrush';
                dataset.faultResistance(i) = 0;
                dataset.inceptionAngle(i) = randi([0, 360]);
                dataset.inceptionTime(i) = 0.05;
                dataset.shouldTrip(i) = false;
                configureInrushScenario(model);
                
            elseif scenarioRand < 0.75
                % 45% Internal faults
                dataset.zone{i} = 'Internal';
                [fType, Rf] = generateRandomFault();
                dataset.faultType{i} = fType;
                dataset.faultResistance(i) = Rf;
                angle = randi([0, 360]);
                dataset.inceptionAngle(i) = angle;
                % Calculate actual inception time based on angle
                faultTime = angleToTime(angle);
                dataset.inceptionTime(i) = faultTime;
                dataset.shouldTrip(i) = true;
                configureInternalFault(model, fType, Rf, faultTime);
                
            else
                % 25% External faults
                dataset.zone{i} = 'External';
                [fType, Rf] = generateRandomFault();
                dataset.faultType{i} = fType;
                dataset.faultResistance(i) = Rf;
                angle = randi([0, 360]);
                dataset.inceptionAngle(i) = angle;
                % Calculate actual inception time based on angle
                faultTime = angleToTime(angle);
                dataset.inceptionTime(i) = faultTime;
                dataset.shouldTrip(i) = false;
                configureExternalFault(model, fType, Rf, faultTime);
            end
            
            % ═══ APPLY REALISTIC MEASUREMENT NOISE & CT MISMATCHES ═══
            % This simulates real-world conditions: imperfect CTs and noisy signals
            
            % 1. GENERATE GLOBAL NOISE LEVEL (same for all phases in this event)
            % Simulates "Quiet Day" (0.01) vs "Stormy Day" (0.11)
            global_noise_level = 0.01 + (0.06 * rand()); 
            dataset.noiseLevel(i) = global_noise_level;
            
            % 2. GENERATE CT RATIO MISMATCHES (unique per channel)
            % Real CTs have ±2% tolerance, each channel different
            ct_mismatches = 0.98 + (0.04 * rand(6, 1)); % 6 channels, range [0.98, 1.02]
            dataset.ctMismatch{i} = ct_mismatches;
            
            % 3. APPLY TO SIMULINK MODEL
            try
                % Loop through 6 channels (Primary ABC + Secondary ABC)
                for ch = 1:6
                    % A. SET CT MISMATCH (Unique per phase)
                    blockPath_CT = sprintf('%s/Noise Merging Unit/CT_Gain_Mismatch_%d', model, ch);
                    set_param(blockPath_CT, 'Gain', num2str(ct_mismatches(ch)));
                    
                    % B. SET NOISE GAIN (Same level for all phases)
                    blockPath_Noise = sprintf('%s/Noise Merging Unit/Noise_Gain_%d', model, ch);
                    set_param(blockPath_Noise, 'Gain', num2str(global_noise_level));
                end
            catch ME
                % If Noise Merging Unit doesn't exist, just log warning and continue
                if i == 1  % Only warn once
                    disp('  ⚠ Warning: Noise Merging Unit not found in model - continuing without noise injection');
                end
            end
            
            % Run simulation
            try
                % ═══ STANDARD SIM COMMAND (No Fast Restart) ═══
                % Model recompiles each time to apply new fault resistance
                % This ensures TRUE parameter diversity in your dataset
                simOut = sim(model, 'StopTime', '1.0');
                
                % ═══ CRITICAL: EXTRACT WAVEFORM DATA ═══
                % These variable names must match your "To Workspace" blocks in Simulink
                % Adjust based on your actual model configuration
                
                try
                    % Primary side currents (3-phase)
                    dataset.primaryCurrent{i} = simOut.get('I_primary_abc');
                catch
                    % Fallback if variable name is different
                    try
                        dataset.primaryCurrent{i} = simOut.I_primary_abc;
                    catch
                        dataset.primaryCurrent{i} = [];
                        fprintf('  Warning: Could not extract I_primary_abc for sample %d\n', i);
                    end
                end
                
                try
                    % Secondary side currents (3-phase)
                    dataset.secondaryCurrent{i} = simOut.get('I_secondary_abc');
                catch
                    try
                        dataset.secondaryCurrent{i} = simOut.I_secondary_abc;
                    catch
                        dataset.secondaryCurrent{i} = [];
                        fprintf('  Warning: Could not extract I_secondary_abc for sample %d\n', i);
                    end
                end
                
                try
                    % Differential current (if available)
                    dataset.diffCurrent{i} = simOut.get('I_diff');
                catch
                    try
                        dataset.diffCurrent{i} = simOut.I_diff;
                    catch
                        dataset.diffCurrent{i} = [];
                    end
                end
                
                try
                    % Trip signal (if available)
                    dataset.tripSignal{i} = simOut.get('TripSignal');
                catch
                    try
                        dataset.tripSignal{i} = simOut.TripSignal;
                    catch
                        dataset.tripSignal{i} = [];
                    end
                end
                
                dataset.simulationStatus{i} = 'Success';
                
            catch ME
                disp(sprintf('  ✗ Warning: Simulation %d failed: %s', i, ME.message));
                dataset.simulationStatus{i} = sprintf('Failed: %s', ME.message);
                dataset.primaryCurrent{i} = [];
                dataset.secondaryCurrent{i} = [];
                dataset.diffCurrent{i} = [];
                dataset.tripSignal{i} = [];
            end
            
            % Brief pause to allow model to reset
            pause(0.01);
        end
        
        % Save dataset
        timestamp = datestr(now, 'yyyymmdd_HHMMSS');
        filename = sprintf('TransformerProtection_Dataset_%s.mat', timestamp);
        save(filename, 'dataset');
        
        close(hWait);
        
        % Calculate success rate
        successCount = sum(strcmp(dataset.simulationStatus, 'Success'));
        successRate = (successCount / nSamples) * 100;
        
        disp(' ');
        disp('╔═══════════════════════════════════════════════════════════╗');
        disp('║          BATCH GENERATION COMPLETED!                      ║');
        disp('╚═══════════════════════════════════════════════════════════╝');
        fprintf('✓ Generated %d samples (%d successful, %.1f%%)\n', ...
                     nSamples, successCount, successRate);
        fprintf('✓ Saved to: %s\n', filename);
        disp(' ');
        disp('Dataset summary:');
        fprintf('  Normal:   %d samples\n', sum(strcmp(dataset.zone, 'Normal')));
        fprintf('  Inrush:   %d samples\n', sum(strcmp(dataset.zone, 'Inrush')));
        fprintf('  Internal: %d samples (should trip)\n', sum(strcmp(dataset.zone, 'Internal')));
        fprintf('  External: %d samples (should NOT trip)\n', sum(strcmp(dataset.zone, 'External')));
        disp(' ');
        disp('Noise characteristics:');
        fprintf('  Noise level range: %.3f to %.3f\n', min(dataset.noiseLevel), max(dataset.noiseLevel));
        fprintf('  Mean noise level: %.3f\n', mean(dataset.noiseLevel));
        fprintf('  CT mismatch range: %.3f to %.3f\n', ...
                     min(cellfun(@min, dataset.ctMismatch)), ...
                     max(cellfun(@max, dataset.ctMismatch)));
        disp(' ');
        
        msgbox(sprintf('Successfully generated %d samples (%.1f%% success)!\n\nSaved to: %s', ...
                      nSamples, successRate, filename), ...
               'Batch Generation Complete', 'help');
        
    catch ME
        if isvalid(hWait)
            close(hWait);
        end
        errordlg(['Batch generation error: ' ME.message], 'Error');
        rethrow(ME);
    end
end



% =========================================================================
% HELPER FUNCTIONS FOR BATCH GENERATION & SIMULATION
% =========================================================================

function runSim(model)
    disp('▶ Starting simulation in Simulink...');
    try
        % Execute the simulation
        sim(model);
        disp('✓ Simulation completed successfully. Check your scopes!');
    catch ME
        % If it fails, pop up an error box so you know why
        errordlg(['Simulation failed: ' ME.message], 'Simulation Error');
        disp(['✗ Simulation failed: ' ME.message]);
    end
end

function configureNormalScenario(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
end

function configureInrushScenario(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
end

function configureInternalFault(model, faultType, Rf, faultTime)
    set_param([model '/Step3'], 'Time', num2str(faultTime)); 
    set_param([model '/Step4'], 'Time', '10');
    
    [fA, fB, fC, fG] = decodeFaultType(faultType);
    set_param([model '/Internal_Fault'], 'FaultA', fA, 'FaultB', fB, ...
              'FaultC', fC, 'GroundFault', fG);
    
    try
        set_param([model '/Internal_Fault'], 'FaultResistance', num2str(Rf));
    catch
    end
end

function configureExternalFault(model, faultType, Rf, faultTime)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', num2str(faultTime)); 
    
    [fA, fB, fC, fG] = decodeFaultType(faultType);
    try
        set_param([model '/External_Fault'], 'FaultA', fA, 'FaultB', fB, ...
                  'FaultC', fC, 'GroundFault', fG);
        set_param([model '/External_Fault'], 'FaultResistance', num2str(Rf));
    catch
    end
end

function [fType, Rf] = generateRandomFault()
    % Define possible fault types
    types = {'AG', 'BG', 'CG', 'AB', 'BC', 'CA', 'ABG', 'BCG', 'CAG', 'ABC'};
    % Pick a random index
    idx = randi(length(types));
    fType = types{idx};
    
    % Generate a realistic fault resistance
    % 80% chance of a solid/low-impedance fault, 20% chance of high impedance
    if rand() > 0.8
        Rf = 10 + 40 * rand(); % High impedance: 10 to 50 ohms
    else
        Rf = 0.001 + 5 * rand(); % Solid fault: near 0 to 5 ohms
    end
end

function faultTime = angleToTime(angle)
    % Converts an inception angle (0-360 degrees) to a time delay
    freq = 60; % Change to 50 if your system is 50Hz
    period = 1/freq;
    timeDelay = (angle / 360) * period;
    
    % Assuming your steady-state is reached by 0.5s, we trigger the fault then
    faultTime = 0.5 + timeDelay; 
end

function [fA, fB, fC, fG] = decodeFaultType(fType)
    % Translates a string like 'ABG' into Simulink block parameters
    fA = 'off'; fB = 'off'; fC = 'off'; fG = 'off';
    
    if contains(fType, 'A'), fA = 'on'; end
    if contains(fType, 'B'), fB = 'on'; end
    if contains(fType, 'C'), fC = 'on'; end
    if contains(fType, 'G') || strcmp(fType, 'AG') || strcmp(fType, 'BG') || strcmp(fType, 'CG')
        fG = 'on'; 
    end
end