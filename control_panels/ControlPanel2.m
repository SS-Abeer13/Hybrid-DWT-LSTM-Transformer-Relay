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
% =========================================================================

function setNormal(model)
    resetFaultBlocks(model);
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: NORMAL LOAD CONDITION (Healthy Operation)');
    disp('═══════════════════════════════════════════════════');
    % Step 1 and 2 removed (Breakers controlled by Relay)
    set_param([model '/Step3'], 'Time', '10'); % Keep internal fault off
    set_param([model '/Step4'], 'Time', '10'); % Keep external fault off
    disp('✓ Configuration complete. Ready to simulate.');
end



function setInrush(model)
    % Inrush via breaker switching is not available when Constant=1 is
    % hardwired to the breaker External port.  Configuration falls back to
    % Normal so the model is left in a safe, runnable state.
    resetFaultBlocks(model);
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: MAGNETIZING INRUSH');
    disp('═══════════════════════════════════════════════════');
    disp('  NOTE: Breakers are hardwired (Constant=1) — true inrush');
    disp('        requires open→close energization which is not possible');
    disp('        here.  Model configured as Normal instead.');
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
    disp('✓ Configuration complete (Normal fallback). Ready to simulate.');
end

function setInternalAG(model)
    resetFaultBlocks(model);
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: INTERNAL FAULT (Phase A-Ground)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '0.5'); % Fault strikes at 0.5s
    set_param([model '/Internal_Fault'], 'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on');
    set_param([model '/Step4'], 'Time', '10');
    disp('✓ Configuration complete. Ready to simulate.');
end

function setInternalAB(model)
    resetFaultBlocks(model);
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: INTERNAL FAULT (Phase A-B)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '0.5');
    set_param([model '/Internal_Fault'], 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'off', 'GroundFault', 'off');
    set_param([model '/Step4'], 'Time', '10');
    disp('✓ Configuration complete. Ready to simulate.');
end

function setInternalABC(model)
    resetFaultBlocks(model);
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: INTERNAL FAULT (3-Phase)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '0.5');
    set_param([model '/Internal_Fault'], 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off');
    set_param([model '/Step4'], 'Time', '10');
    disp('✓ Configuration complete. Ready to simulate.');
end

function setExternalFault(model)
    resetFaultBlocks(model);
    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: EXTERNAL FAULT (Through Fault)');
    disp('═══════════════════════════════════════════════════');
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '0.5'); % External fault strikes at 0.5s
    % Enable all three phases on External_Fault (3-phase through-fault).
    % resetFaultBlocks clears these to 'off', so they must be re-enabled here.
    set_param([model '/External_Fault'], 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off');
    disp('✓ Configuration complete. Ready to simulate.');
end
function runSim(model)
    disp(' ');
    disp('>>> STARTING INDIVIDUAL SIMULATION WITH NORMAL-DEBUG LOG...');
    disp('===================================================');

    status = get_param(model, 'SimulationStatus');
    if strcmp(status, 'running')
        disp('Simulation already running. Please wait.');
        return;
    end

    logDir = fullfile(pwd, 'IndividualRunLogs');
    if ~exist(logDir, 'dir')
        mkdir(logDir);
    end

    timestamp = datestr(now, 'yyyymmdd_HHMMSS');
    logFile = fullfile(logDir, sprintf('%s_%s_normal_debug.log', model, timestamp));
    matFile = fullfile(logDir, sprintf('%s_%s_normal_debug.mat', model, timestamp));

    fid = fopen(logFile, 'w');
    if fid < 0
        errordlg('Could not create debug log file.', 'Logging Error');
        return;
    end

    cleanupFile = onCleanup(@() fclose(fid));

    oldSignalLogging = get_param(model, 'SignalLogging');
    oldSignalLoggingName = get_param(model, 'SignalLoggingName');

    restoreLines = struct('Line', {}, 'DataLogging', {}, ...
                          'DataLoggingNameMode', {}, 'DataLoggingName', {});

    debugData = struct();
    debugData.timestamp = timestamp;
    debugData.model = model;
    debugData.logFile = logFile;

    try
        fprintf(fid, '============================================================\n');
        fprintf(fid, 'NORMAL SCENARIO FALSE-TRIP DEBUG LOG\n');
        fprintf(fid, '============================================================\n');
        fprintf(fid, 'Timestamp: %s\n', datestr(now));
        fprintf(fid, 'Model: %s\n', model);
        fprintf(fid, 'MATLAB version: %s\n', version);
        fprintf(fid, 'Working folder: %s\n\n', pwd);

        set_param(model, 'SignalLogging', 'on');
        set_param(model, 'SignalLoggingName', 'logsout');

        debugLogNormalScenarioState(fid, model);
        debugLogRelayConfiguration(fid, model);

        fprintf(fid, '\n============================================================\n');
        fprintf(fid, 'TEMPORARY SIGNAL LOGGING SETUP\n');
        fprintf(fid, '============================================================\n');

        restoreLines = debugEnableNormalRunSignalLogging(fid, model);

        fprintf(fid, '\n============================================================\n');
        fprintf(fid, 'MODEL UPDATE / COMPILE CHECK\n');
        fprintf(fid, '============================================================\n');

        try
            set_param(model, 'SimulationCommand', 'update');
            fprintf(fid, 'Model update: SUCCESS\n');
        catch MEupdate
            fprintf(fid, 'Model update: FAILED\n');
            fprintf(fid, '%s\n', getReport(MEupdate, 'extended', 'hyperlinks', 'off'));
            debugData.updateError = MEupdate;
            save(matFile, 'debugData');
            rethrow(MEupdate);
        end

        debugLogCompiledPortInfo(fid, model);

        fprintf(fid, '\n============================================================\n');
        fprintf(fid, 'SIMULATION RUN\n');
        fprintf(fid, '============================================================\n');

        stopTime = get_param(model, 'StopTime');
        fprintf(fid, 'StopTime: %s\n', stopTime);

        simOut = sim(model, ...
            'StopTime', stopTime, ...
            'ReturnWorkspaceOutputs', 'on');

        fprintf(fid, '\nSimulation: SUCCESS\n');

        debugData.simOut = simOut;
        debugLogSimulationOutputsForNormalTrip(fid, simOut);

        save(matFile, 'debugData', '-v7.3');

        fprintf(fid, '\n============================================================\n');
        fprintf(fid, 'DEBUG LOG COMPLETE\n');
        fprintf(fid, 'MAT file: %s\n', matFile);
        fprintf(fid, '============================================================\n');

        disp('Simulation completed successfully.');
        fprintf('Debug log saved to:\n%s\n', logFile);

        msgbox(sprintf('Simulation completed.\n\nDebug log:\n%s', logFile), ...
               'Simulation Complete', 'help');

    catch ME
        fprintf(fid, '\n============================================================\n');
        fprintf(fid, 'SIMULATION FAILED\n');
        fprintf(fid, '============================================================\n');
        fprintf(fid, '%s\n', getReport(ME, 'extended', 'hyperlinks', 'off'));

        debugData.error = ME;

        try
            [lastMsg, lastId] = lastwarn;
            fprintf(fid, '\nLast warning ID: %s\n', lastId);
            fprintf(fid, 'Last warning message: %s\n', lastMsg);
            debugData.lastWarning.message = lastMsg;
            debugData.lastWarning.id = lastId;
        catch
        end

        save(matFile, 'debugData', '-v7.3');

        disp(['ERROR: ' ME.message]);
        fprintf('Debug log saved to:\n%s\n', logFile);
        fprintf('Debug MAT saved to:\n%s\n', matFile);

        errordlg(sprintf('%s\n\nDebug log saved to:\n%s', ME.message, logFile), ...
                 'Simulation Error');

    end

    debugRestoreSignalLogging(restoreLines);
    set_param(model, 'SignalLogging', oldSignalLogging);
    set_param(model, 'SignalLoggingName', oldSignalLoggingName);
end

function debugLogNormalScenarioState(fid, model)
    fprintf(fid, 'NORMAL SCENARIO STATE CHECK\n');
    fprintf(fid, '---------------------------\n');

    stopTime = str2double(get_param(model, 'StopTime'));
    if isnan(stopTime)
        stopTime = inf;
    end

    step3Time = str2double(get_param([model '/Step3'], 'Time'));
    step4Time = str2double(get_param([model '/Step4'], 'Time'));

    fprintf(fid, 'StopTime: %.6g\n', stopTime);
    fprintf(fid, 'Step3 Internal Fault Time: %.6g\n', step3Time);
    fprintf(fid, 'Step4 External Fault Time: %.6g\n', step4Time);

    debugLogFaultBlock(fid, model, 'Internal_Fault');
    debugLogFaultBlock(fid, model, 'External_Fault');

    internalArmed = debugFaultBlockArmed(model, 'Internal_Fault');
    externalArmed = debugFaultBlockArmed(model, 'External_Fault');

    fprintf(fid, '\nNormal-run interpretation:\n');
    if step3Time > stopTime && step4Time > stopTime
        fprintf(fid, '  Step times indicate intended NORMAL/NO-FAULT run.\n');
    else
        fprintf(fid, '  WARNING: One or more fault steps occur within StopTime.\n');
    end

    if internalArmed || externalArmed
        fprintf(fid, '  WARNING: One or more fault blocks still have phase/ground flags ON.\n');
        fprintf(fid, '  This can contaminate a normal run if the fault control path enables them.\n');
    else
        fprintf(fid, '  Fault block phase/ground flags are all OFF.\n');
    end
end


function debugLogFaultBlock(fid, model, blockName)
    blk = [model '/' blockName];

    fprintf(fid, '\nBlock: %s\n', blk);

    params = {'InitialStates', 'FaultA', 'FaultB', 'FaultC', 'GroundFault', ...
              'SwitchTimes', 'External', 'SwitchStatus', 'FaultResistance', ...
              'GroundResistance', 'SnubberResistance', 'SnubberCapacitance'};

    for i = 1:numel(params)
        try
            fprintf(fid, '  %s: %s\n', params{i}, get_param(blk, params{i}));
        catch
            fprintf(fid, '  %s: <not available>\n', params{i});
        end
    end
end


function armed = debugFaultBlockArmed(model, blockName)
    blk = [model '/' blockName];
    armed = false;

    params = {'FaultA', 'FaultB', 'FaultC', 'GroundFault'};
    for i = 1:numel(params)
        try
            armed = armed || strcmpi(get_param(blk, params{i}), 'on');
        catch
        end
    end
end


function debugLogRelayConfiguration(fid, model)
    fprintf(fid, '\nRELAY / AI CONFIGURATION\n');
    fprintf(fid, '------------------------\n');

    relay = [model '/Hybrid 87T Relay'];

    blocks = {
        [relay '/I_diff']
        [relay '/I_rest']
        [relay '/I_diff_window']
        [relay '/MATLAB Function1']
        [relay '/Feature Window']
        debugFindRelayBlock(relay, '^Reshape\s*$')
        [relay '/LSTM Predict']
        [relay '/Manual Switch']
        [relay '/OFF']
        [relay '/RESET']
        [relay '/Supervisory Override with Hardware Fallback']
        debugFindRelayBlock(relay, '^S-R\s*Latch$')
        [relay '/Trip_Signal']
    };

    for i = 1:numel(blocks)
        blk = blocks{i};
        if isempty(blk)
            continue;
        end

        fprintf(fid, '\nBlock: %s\n', blk);

        try
            dlg = get_param(blk, 'DialogParameters');
            names = fieldnames(dlg);

            for j = 1:numel(names)
                name = names{j};
                try
                    val = get_param(blk, name);
                    if ischar(val) || isstring(val) || isnumeric(val) || islogical(val)
                        fprintf(fid, '  %s: %s\n', name, debugValueToText(val));
                    end
                catch
                end
            end
        catch ME
            fprintf(fid, '  Could not read parameters: %s\n', ME.message);
        end
    end
end


function restoreLines = debugEnableNormalRunSignalLogging(fid, model)
    relay = [model '/Hybrid 87T Relay'];
    restoreLines = struct('Line', {}, 'DataLogging', {}, ...
                          'DataLoggingNameMode', {}, 'DataLoggingName', {});

    points = {
        [relay '/MATLAB Function'], 1, 'relay_hv_comp'
        [relay '/MATLAB Function'], 2, 'relay_lv_comp'
        [relay '/I_diff'], 1, 'relay_I_diff'
        [relay '/I_rest'], 1, 'relay_I_rest'
        [relay '/Gain'], 1, 'relay_I_rest_half'
        [relay '/I_diff_window'], 1, 'relay_I_diff_window'
        [relay '/MATLAB Function1'], 1, 'relay_dwt_features_6'
        [relay '/Feature Window'], 1, 'relay_feature_window_32'
        debugFindRelayBlock(relay, '^Reshape\s*$'), 1, 'relay_lstm_input'
        [relay '/LSTM Predict'], 1, 'relay_lstm_confidence'
        [relay '/Manual Switch'], 1, 'relay_lstm_manual_switch_out'
        [relay '/Supervisory Override with Hardware Fallback'], 1, 'relay_raw_trip_decision'
        [relay '/Data Type Conversion'], 1, 'relay_trip_bool'
        debugFindRelayBlock(relay, '^S-R\s*Latch$'), 1, 'relay_trip_latch'
        [relay '/Trip_Signal'], 1, 'relay_trip_signal_out'
        [model '/Hybrid 87T Relay'], 1, 'top_relay_trip_to_breakers'
    };

    for i = 1:size(points, 1)
        blk = points{i, 1};
        portIdx = points{i, 2};
        logName = points{i, 3};

        if isempty(blk)
            fprintf(fid, 'SKIP: %s block not found.\n', logName);
            continue;
        end

        [restoreLines, ok, msg] = debugMarkOutportForLogging(restoreLines, blk, portIdx, logName);

        if ok
            fprintf(fid, 'Logging ON: %s -> %s\n', blk, logName);
        else
            fprintf(fid, 'Could not log %s: %s\n', logName, msg);
        end
    end

    breakerBlocks = {
        [model '/Three-Phase Breaker'], 'breaker_primary_trip_input'
        [model '/Three-Phase Breaker1'], 'breaker_secondary_trip_input'
    };

    for i = 1:size(breakerBlocks, 1)
        blk = breakerBlocks{i, 1};
        logName = breakerBlocks{i, 2};

        [restoreLines, ok, msg] = debugMarkLastInportForLogging(restoreLines, blk, logName);

        if ok
            fprintf(fid, 'Logging ON: %s control input -> %s\n', blk, logName);
        else
            fprintf(fid, 'Could not log %s: %s\n', logName, msg);
        end
    end
end


function [restoreLines, ok, msg] = debugMarkOutportForLogging(restoreLines, blk, portIdx, logName)
    ok = false;
    msg = '';

    try
        ph = get_param(blk, 'PortHandles');

        if numel(ph.Outport) < portIdx
            msg = 'requested outport does not exist';
            return;
        end

        line = get_param(ph.Outport(portIdx), 'Line');

        if line == -1
            msg = 'outport has no connected signal line';
            return;
        end

        restoreLines(end+1) = debugCaptureLineLoggingState(line);

        set_param(line, 'DataLogging', 'on');
        set_param(line, 'DataLoggingNameMode', 'Custom');
        set_param(line, 'DataLoggingName', logName);

        ok = true;

    catch ME
        msg = ME.message;
    end
end


function [restoreLines, ok, msg] = debugMarkLastInportForLogging(restoreLines, blk, logName)
    ok = false;
    msg = '';

    try
        ph = get_param(blk, 'PortHandles');

        if isempty(ph.Inport)
            msg = 'block has no Simulink input ports';
            return;
        end

        line = get_param(ph.Inport(end), 'Line');

        if line == -1
            msg = 'last input port has no connected signal line';
            return;
        end

        restoreLines(end+1) = debugCaptureLineLoggingState(line);

        set_param(line, 'DataLogging', 'on');
        set_param(line, 'DataLoggingNameMode', 'Custom');
        set_param(line, 'DataLoggingName', logName);

        ok = true;

    catch ME
        msg = ME.message;
    end
end


function state = debugCaptureLineLoggingState(line)
    state = struct();
    state.Line = line;

    try
        state.DataLogging = get_param(line, 'DataLogging');
    catch
        state.DataLogging = 'off';
    end

    try
        state.DataLoggingNameMode = get_param(line, 'DataLoggingNameMode');
    catch
        state.DataLoggingNameMode = 'SignalName';
    end

    try
        state.DataLoggingName = get_param(line, 'DataLoggingName');
    catch
        state.DataLoggingName = '';
    end
end


function debugRestoreSignalLogging(restoreLines)
    for i = 1:numel(restoreLines)
        try
            set_param(restoreLines(i).Line, 'DataLogging', restoreLines(i).DataLogging);
            set_param(restoreLines(i).Line, 'DataLoggingNameMode', restoreLines(i).DataLoggingNameMode);
            set_param(restoreLines(i).Line, 'DataLoggingName', restoreLines(i).DataLoggingName);
        catch
        end
    end
end


function debugLogCompiledPortInfo(fid, model)
    fprintf(fid, '\nCOMPILED PORT DIMENSIONS / TYPES\n');
    fprintf(fid, '--------------------------------\n');

    relay = [model '/Hybrid 87T Relay'];

    blocks = {
        [relay '/MATLAB Function']
        [relay '/I_diff']
        [relay '/I_rest']
        [relay '/I_diff_window']
        [relay '/MATLAB Function1']
        [relay '/Feature Window']
        debugFindRelayBlock(relay, '^Reshape\s*$')
        [relay '/LSTM Predict']
        [relay '/Manual Switch']
        [relay '/Supervisory Override with Hardware Fallback']
        [relay '/Data Type Conversion']
        debugFindRelayBlock(relay, '^S-R\s*Latch$')
        [model '/Hybrid 87T Relay']
        [model '/Three-Phase Breaker']
        [model '/Three-Phase Breaker1']
    };

    for i = 1:numel(blocks)
        blk = blocks{i};
        if isempty(blk)
            continue;
        end

        fprintf(fid, '\nBlock: %s\n', blk);

        try
            dims = get_param(blk, 'CompiledPortDimensions');
            fprintf(fid, '  Dimensions:\n%s\n', evalc('disp(dims)'));
        catch ME
            fprintf(fid, '  Could not read dimensions: %s\n', ME.message);
        end

        try
            types = get_param(blk, 'CompiledPortDataTypes');
            fprintf(fid, '  Data types:\n%s\n', evalc('disp(types)'));
        catch ME
            fprintf(fid, '  Could not read data types: %s\n', ME.message);
        end
    end
end


function debugLogSimulationOutputsForNormalTrip(fid, simOut)
    fprintf(fid, '\nSIMULATION OUTPUTS / LOGGED SIGNALS\n');
    fprintf(fid, '-----------------------------------\n');

    try
        names = simOut.who;
        fprintf(fid, 'Variables returned by simOut:\n');
        for i = 1:numel(names)
            fprintf(fid, '  %s\n', names{i});
        end
    catch ME
        fprintf(fid, 'Could not list simOut variables: %s\n', ME.message);
    end

    fprintf(fid, '\nTo Workspace variables:\n');
    debugLogSimOutVariable(fid, simOut, 'I_primary_abc');
    debugLogSimOutVariable(fid, simOut, 'I_secondary_abc');
    debugLogSimOutVariable(fid, simOut, 'I_diff');
    debugLogSimOutVariable(fid, simOut, 'I_rest');
    debugLogSimOutVariable(fid, simOut, 'TripSignal');
    debugLogSimOutVariable(fid, simOut, 'Trip_Signal');

    fprintf(fid, '\nlogsout details:\n');

    try
        logsout = simOut.get('logsout');
        fprintf(fid, 'logsout elements: %d\n', logsout.numElements);

        for i = 1:logsout.numElements
            element = logsout.get(i);
            fprintf(fid, '\n[%02d] %s\n', i, element.Name);
            debugLogLoggedElement(fid, element);
        end
    catch ME
        fprintf(fid, 'Could not read logsout: %s\n', ME.message);
    end

    fprintf(fid, '\nTrip diagnosis summary:\n');
    debugTrySignalTripSummary(fid, simOut, 'relay_I_diff');
    debugTrySignalTripSummary(fid, simOut, 'relay_I_rest');
    debugTrySignalTripSummary(fid, simOut, 'relay_lstm_confidence');
    debugTrySignalTripSummary(fid, simOut, 'relay_raw_trip_decision');
    debugTrySignalTripSummary(fid, simOut, 'relay_trip_latch');
    debugTrySignalTripSummary(fid, simOut, 'top_relay_trip_to_breakers');
    debugTrySignalTripSummary(fid, simOut, 'breaker_primary_trip_input');
    debugTrySignalTripSummary(fid, simOut, 'breaker_secondary_trip_input');
end


function debugLogSimOutVariable(fid, simOut, name)
    try
        val = simOut.get(name);
        fprintf(fid, '  %s: %s\n', name, debugDescribeValue(val));
    catch
        fprintf(fid, '  %s: <not found>\n', name);
    end
end


function debugLogLoggedElement(fid, element)
    try
        values = element.Values;
        fprintf(fid, '  Values class: %s\n', class(values));

        if isa(values, 'timeseries')
            fprintf(fid, '  Time size: %s\n', mat2str(size(values.Time)));
            fprintf(fid, '  Data size: %s\n', mat2str(size(values.Data)));
            debugLogNumericStats(fid, values.Data, values.Time);
        else
            fprintf(fid, '  Description: %s\n', debugDescribeValue(values));
        end
    catch ME
        fprintf(fid, '  Could not inspect element: %s\n', ME.message);
    end
end


function debugTrySignalTripSummary(fid, simOut, signalName)
    try
        logsout = simOut.get('logsout');
        element = logsout.get(signalName);
        values = element.Values;

        if isa(values, 'timeseries')
            data = values.Data;
            time = values.Time;

            if isempty(data)
                fprintf(fid, '  %s: empty\n', signalName);
                return;
            end

            dataFlat = data(:);
            maxVal = max(dataFlat);
            minVal = min(dataFlat);
            lastVal = dataFlat(end);

            firstHighIdx = find(abs(dataFlat) > 0.5, 1, 'first');

            fprintf(fid, '  %s: min=%.6g max=%.6g last=%.6g size=%s', ...
                    signalName, minVal, maxVal, lastVal, mat2str(size(data)));

            if ~isempty(firstHighIdx)
                tIdx = min(firstHighIdx, numel(time));
                fprintf(fid, ' first>|0.5| at t=%.6g', time(tIdx));
            end

            fprintf(fid, '\n');
        end
    catch
        fprintf(fid, '  %s: <not logged>\n', signalName);
    end
end


function debugLogNumericStats(fid, data, time)
    try
        if isempty(data)
            fprintf(fid, '  Data is empty.\n');
            return;
        end

        dataFlat = data(:);

        fprintf(fid, '  Min: %.6g\n', min(dataFlat));
        fprintf(fid, '  Max: %.6g\n', max(dataFlat));
        fprintf(fid, '  Mean: %.6g\n', mean(dataFlat));
        fprintf(fid, '  Last: %.6g\n', dataFlat(end));

        idx = find(abs(dataFlat) > 0.5, 1, 'first');
        if ~isempty(idx) && ~isempty(time)
            tIdx = min(idx, numel(time));
            fprintf(fid, '  First abs(value)>0.5 around t=%.6g\n', time(tIdx));
        end

        nShow = min(5, numel(dataFlat));
        fprintf(fid, '  First %d values: %s\n', nShow, mat2str(dataFlat(1:nShow).', 6));
        fprintf(fid, '  Last %d values: %s\n', nShow, mat2str(dataFlat(end-nShow+1:end).', 6));
    catch ME
        fprintf(fid, '  Could not compute numeric stats: %s\n', ME.message);
    end
end


function blk = debugFindRelayBlock(parent, regexpName)
    blk = '';

    try
        matches = find_system(parent, ...
            'SearchDepth', 1, ...
            'Regexp', 'on', ...
            'Name', regexpName);

        if ~isempty(matches)
            blk = matches{1};
        end
    catch
        blk = '';
    end
end


function out = debugValueToText(val)
    if isnumeric(val) || islogical(val)
        out = mat2str(val);
    elseif isstring(val)
        out = char(val);
    elseif ischar(val)
        out = val;
    else
        out = sprintf('<%s>', class(val));
    end
end


function out = debugDescribeValue(val)
    try
        if isnumeric(val) || islogical(val)
            out = sprintf('%s, size %s, min %.6g, max %.6g', ...
                class(val), mat2str(size(val)), min(val(:)), max(val(:)));
        elseif isa(val, 'timeseries')
            out = sprintf('timeseries, Data size %s, Time size %s', ...
                mat2str(size(val.Data)), mat2str(size(val.Time)));
        elseif isa(val, 'Simulink.SimulationData.Dataset')
            out = sprintf('Dataset with %d elements', val.numElements);
        elseif isstruct(val)
            out = sprintf('struct, size %s, fields: %s', ...
                mat2str(size(val)), strjoin(fieldnames(val), ', '));
        else
            out = sprintf('%s, size %s', class(val), mat2str(size(val)));
        end
    catch ME
        out = sprintf('Could not describe value: %s', ME.message);
    end
end

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
    dataset.metadata.nSamples      = nSamples;
    dataset.metadata.generatedDate = datetime('now');
    dataset.metadata.modelName     = model;
    % ── Variability configuration (logged for reproducibility) ──────────────
    dataset.metadata.variabilityConfig = struct( ...
        'classDistribution',  '20% Normal | 52% Internal | 28% External', ...
        'faultTimeRange_s',   '[0.10, 0.80]  uniform random', ...
        'faultResistance_Ohm','[0.001, 100]  log-uniform', ...
        'noiseLevelRange',    '[0.005, 0.12] uniform random', ...
        'ctMismatchRange',    '[0.95, 1.05]  per-channel uniform random', ...
        'inrushNote',         'Inrush omitted — Constant=1 on breakers prevents energisation switching');

    % Preallocate arrays for labels
    dataset.zone            = cell(nSamples, 1);  % 'Internal','External','Normal'
    dataset.faultType       = cell(nSamples, 1);  % 'AG','BG','AB','ABC', etc.
    dataset.faultResistance = zeros(nSamples, 1); % Ohms
    dataset.inceptionAngle  = zeros(nSamples, 1); % Degrees within cycle (0-360)
    dataset.inceptionTime   = zeros(nSamples, 1); % Absolute seconds
    dataset.shouldTrip      = false(nSamples, 1); % Ground-truth label

    % Preallocate arrays for waveform data
    dataset.primaryCurrent   = cell(nSamples, 1); % Primary side 3-phase currents
    dataset.secondaryCurrent = cell(nSamples, 1); % Secondary side 3-phase currents
    dataset.diffCurrent      = cell(nSamples, 1); % Differential current I_diff
    dataset.restCurrent      = cell(nSamples, 1); % Restraint current I_rest
    dataset.tripSignal       = cell(nSamples, 1); % Relay trip signal
    dataset.simulationStatus = cell(nSamples, 1); % 'Success' / 'Failed: ...'

    % Preallocate arrays for noise and mismatch metadata
    dataset.noiseLevel = zeros(nSamples, 1);      % Global noise level per sample
    dataset.ctMismatch = cell(nSamples, 1);       % CT ratio mismatches (6 channels)
    
    % Progress figure
    hWait = waitbar(0, 'Initializing...', 'Name', 'Batch Generation Progress');
    
    try
        for i = 1:nSamples
            % Update progress
            if mod(i, 10) == 0
                waitbar(i/nSamples, hWait, sprintf('Generating sample %d/%d...', i, nSamples));
            end
            
            % ── Scenario selection  (20 % Normal | 52 % Internal | 28 % External) ──
            % Inrush is excluded: Constant=1 on breakers prevents open→close
            % energisation; including it would produce corrupt Normal-like data
            % labelled as Inrush.  Train a separate inrush discriminator using
            % data captured with proper breaker switching.
            scenarioRand = rand();
            if scenarioRand < 0.20
                % ── 20 % Normal operation ────────────────────────────────────
                dataset.zone{i}           = 'Normal';
                dataset.faultType{i}      = 'None';
                dataset.faultResistance(i)= 0;
                dataset.inceptionAngle(i) = 0;
                dataset.inceptionTime(i)  = 0;
                dataset.shouldTrip(i)     = false;
                configureNormalScenario(model);

            elseif scenarioRand < 0.72
                % ── 52 % Internal faults ─────────────────────────────────────
                % Fault inception time: uniform [0.10, 0.80] s
                % This wide spread prevents the LSTM from learning time-position
                % instead of the actual signal morphology.
                dataset.zone{i}  = 'Internal';
                [fType, Rf]      = generateRandomFault();
                dataset.faultType{i}       = fType;
                dataset.faultResistance(i) = Rf;
                faultTime = 0.10 + 0.70 * rand();          % uniform [0.10, 0.80] s
                dataset.inceptionTime(i)   = faultTime;
                % Record angle within cycle for analysis
                dataset.inceptionAngle(i)  = mod(faultTime, 1/50) / (1/50) * 360;
                dataset.shouldTrip(i)      = true;
                configureInternalFault(model, fType, Rf, faultTime);

            else
                % ── 28 % External faults ─────────────────────────────────────
                dataset.zone{i}  = 'External';
                [fType, Rf]      = generateRandomFault();
                dataset.faultType{i}       = fType;
                dataset.faultResistance(i) = Rf;
                faultTime = 0.10 + 0.70 * rand();          % uniform [0.10, 0.80] s
                dataset.inceptionTime(i)   = faultTime;
                dataset.inceptionAngle(i)  = mod(faultTime, 1/50) / (1/50) * 360;
                dataset.shouldTrip(i)      = false;
                configureExternalFault(model, fType, Rf, faultTime);
            end

            % ── Measurement noise & CT mismatch ──────────────────────────────
            % Wide ranges to cover quiet rural substations through to noisy
            % industrial busbars, and IEC 61869-2 Class 0.5 through to Class 1.

            % 1. Noise level: uniform [0.005, 0.12]  (0.5 % → 12 % of rated)
            global_noise_level = 0.005 + 0.115 * rand();
            dataset.noiseLevel(i) = global_noise_level;

            % 2. CT ratio mismatch: uniform [0.95, 1.05] per channel (±5 %)
            ct_mismatches = 0.95 + 0.10 * rand(6, 1);
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
                    % Restraint current I_rest (key feature for operating char.)
                    dataset.restCurrent{i} = simOut.get('I_rest');
                catch
                    try
                        dataset.restCurrent{i} = simOut.I_rest;
                    catch
                        dataset.restCurrent{i} = [];
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
% HELPER FUNCTIONS FOR BATCH GENERATION
% =========================================================================

function [faultType, Rf] = generateRandomFault()
    % Generate random fault type and resistance.
    % All 10 symmetrical-component fault types are included so the network
    % sees balanced, unbalanced, and ground-involving events equally.
    faultTypes = {'AG', 'BG', 'CG', 'AB', 'BC', 'CA', 'ABC', 'ABG', 'BCG', 'CAG'};
    faultType = faultTypes{randi(length(faultTypes))};

    % Fault resistance: log-uniform [0.001, 100] Ω
    %   0.001 Ω  — bolted / metallic fault (maximum fault current)
    %   ~1–10 Ω  — typical arcing fault
    %   ~20–100 Ω — high-impedance fault (challenging detection edge case)
    % Log-uniform ensures the network sees all regimes in proportion.
    Rf = 10^(rand() * (log10(100) - log10(0.001)) + log10(0.001));
end

function configureNormalScenario(model)
    resetFaultBlocks(model);
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
end

function configureInrushScenario(model)
    % NOTE: Authentic inrush requires the HV breaker to open then re-close
    % onto a residual-flux core.  With Constant=1 hardwired to the breaker
    % External port, that switching is not possible via Step blocks alone.
    % This function intentionally falls back to Normal-equivalent configuration.
    % The batch generator already redirects inrush slots to Normal labels.
    resetFaultBlocks(model);
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
end

function configureInternalFault(model, faultType, Rf, faultTime)
    resetFaultBlocks(model);
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
    resetFaultBlocks(model);
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

function [fA, fB, fC, fG] = decodeFaultType(faultType)
    
    % Decode fault type string to phase involvement
    fA = 'off'; fB = 'off'; fC = 'off'; fG = 'off';
    
    if contains(faultType, 'A'), fA = 'on'; end
    if contains(faultType, 'B'), fB = 'on'; end
    if contains(faultType, 'C'), fC = 'on'; end
    if contains(faultType, 'G'), fG = 'on'; end
end

function faultTime = angleToTime(angle)
    % Convert inception angle (0-360 degrees) to time offset
    % Assumes 50Hz system (change to 60 if needed)
    frequency = 50; % Hz - ADJUST THIS FOR YOUR SYSTEM
    
    % Base fault start time (when system is stable)
    baseTime = 0.5; % seconds
    
    % Calculate time offset for the given angle
    % One cycle = 1/frequency seconds = 360 degrees
    cyclePeriod = 1 / frequency;
    timeOffset = (angle / 360) * cyclePeriod;
    
    % Final fault inception time
    faultTime = baseTime + timeOffset;
end
function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');

    set_param([model '/Internal_Fault'], ...
        'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    try
        set_param([model '/Internal_Fault'], 'FaultResistance', '0.01');
    catch, end

    set_param([model '/External_Fault'], ...
        'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    try
        set_param([model '/External_Fault'], 'FaultResistance', '0.01');
    catch, end
end
