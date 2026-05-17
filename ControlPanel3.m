function ControlPanel2
% =========================================================================
% TRANSFORMER PROTECTION CONTROL PANEL  v3.0
% Hybrid UI  |  Real Model Response  |  Scenario-Aware Logging
% =========================================================================
%
%  UI layout matches HybridRelayInferencePanel (dark theme, wide canvas).
%  Telemetry rows are populated from REAL simulation outputs — no hardcoded
%  classification logic.  Log files and headers always reflect the active
%  scenario (no more hard-wired "NORMAL" labels on fault runs).
%
%  Left panel  : Event Injection + Training-Data Generator
%  Right panel : Waveform axes  + Relay telemetry  + Action badge
% =========================================================================

    % ---- AUTO-DETECT SIMULINK MODEL ----
    modelName = autoDetectSimulinkModel();
    if isempty(modelName), return; end

    % ---- THEME (dark, matches HybridRelayInferencePanel) ----------------
    BG     = [0.10 0.13 0.16];
    PANEL  = [0.15 0.19 0.24];
    TXT    = [0.95 0.95 0.95];
    ACCENT = [0.20 0.62 0.88];
    MUTED  = [0.60 0.65 0.70];
    BTN_FG = [0.88 0.92 0.96];

    FIG_W = 1150;  FIG_H = 720;

    f = figure( ...
        'Name',        ['Protection Test Console  —  ' modelName], ...
        'NumberTitle', 'off', ...
        'Position',    [100, 50, FIG_W, FIG_H], ...
        'MenuBar',     'none', ...
        'Resize',      'off', ...
        'Color',       BG);

    % ---- HEADER ---------------------------------------------------------
    uicontrol(f, 'Style','text', ...
        'Position',          [0, FIG_H-45, FIG_W, 36], ...
        'String',            'TRANSFORMER PROTECTION TEST CONSOLE', ...
        'FontSize',          14, 'FontWeight','bold', ...
        'ForegroundColor',   TXT, 'BackgroundColor', BG, ...
        'HorizontalAlignment','center');

    uicontrol(f, 'Style','text', ...
        'Position',          [0, FIG_H-65, FIG_W, 22], ...
        'String',            ['Target Plant:  ' modelName '.slx'], ...
        'FontSize',          10, 'FontAngle','italic', ...
        'ForegroundColor',   MUTED, 'BackgroundColor', BG, ...
        'HorizontalAlignment','center');

    % =========================================================================
    % LEFT PANEL — EVENT INJECTION NETWORK
    % =========================================================================
    pLeft = uipanel(f, ...
        'Title',           'Event Injection Network', ...
        'FontSize',        11, 'FontWeight','bold', ...
        'ForegroundColor', ACCENT, ...
        'BackgroundColor', PANEL, ...
        'Position',        [0.015, 0.03, 0.22, 0.87]);

    % --- Scenario definitions [Label, key, RGB color] --------------------
    scenarios = { ...
        'Normal Operation',       'Normal',      [0.14 0.50 0.28]; ...
        'Magnetizing Inrush',     'Inrush',      [0.18 0.40 0.65]; ...
        'Internal Fault (A-G)',   'InternalAG',  [0.65 0.22 0.18]; ...
        'Internal Fault (B-G)',   'InternalBG',  [0.70 0.25 0.20]; ...
        'Internal Fault (A-B)',   'InternalAB',  [0.75 0.18 0.14]; ...
        'Internal Fault (3\Phi)', 'InternalABC', [0.80 0.15 0.10]; ...
        'External Fault (3\Phi)', 'External',    [0.42 0.38 0.12]; ...
        'External Fault (A-B)',   'ExternalAB',  [0.45 0.40 0.15]  ...
    };

    BH = 38;  GAP = 9;  TOP = 515;
    for k = 1:size(scenarios,1)
        yPos = TOP - (k-1)*(BH+GAP);
        uicontrol(pLeft, 'Style','pushbutton', ...
            'Position',        [15, yPos, 200, BH], ...
            'String',          scenarios{k,1}, ...
            'FontSize',        10, 'FontWeight','bold', ...
            'ForegroundColor', BTN_FG, ...
            'BackgroundColor', scenarios{k,3}, ...
            'Callback', @(~,~) setScenario(f, modelName, scenarios{k,2}));
    end

    uicontrol(pLeft, 'Style','text', ...
        'Position',          [15, 25, 200, 22], ...
        'String',            'Armed & Awaiting Trigger', ...
        'FontSize',          9, 'FontAngle','italic', ...
        'ForegroundColor',   MUTED, 'BackgroundColor', PANEL, ...
        'HorizontalAlignment','center');

    % ---- BATCH GENERATOR sub-panel --------------------------------------
    pBatch = uipanel(pLeft, ...
        'Title',           'Training Data Generator', ...
        'FontSize',        10, 'FontWeight','bold', ...
        'ForegroundColor', [0.75 0.55 0.95], ...
        'BackgroundColor', [0.12 0.16 0.20], ...
        'Units',           'pixels', ...
        'Position',        [8, 50, 222, 100]);   % anchored above status text

    uicontrol(pBatch, 'Style','text', ...
        'Position',          [8, 58, 105, 20], ...
        'String',            'Number of Samples:', ...
        'FontSize',          9, ...
        'ForegroundColor',   MUTED, 'BackgroundColor', [0.12 0.16 0.20], ...
        'HorizontalAlignment','left');

    hSampleCount = uicontrol(pBatch, 'Style','edit', ...
        'Position',          [118, 56, 70, 24], ...
        'String',            '500', ...
        'FontSize',          10, ...
        'BackgroundColor',   [0.22 0.28 0.35], ...
        'ForegroundColor',   TXT);

    uicontrol(pBatch, 'Style','pushbutton', ...
        'Position',          [10, 12, 200, 34], ...
        'String',            char(9889) + " GENERATE BATCH DATASET", ...
        'FontSize',          9, 'FontWeight','bold', ...
        'ForegroundColor',   [0.75 0.55 0.95], ...
        'BackgroundColor',   [0.20 0.15 0.28], ...
        'TooltipString',     'Generate random scenarios and save to .mat file', ...
        'Callback', @(~,~) generateBatch(modelName, hSampleCount));

    % =========================================================================
    % RIGHT PANEL — TELEMETRY & ANALYTICS
    % =========================================================================
    pRight = uipanel(f, ...
        'Title',           'Real-Time Relay Telemetry  &  Signal Analytics', ...
        'FontSize',        11, 'FontWeight','bold', ...
        'ForegroundColor', ACCENT, ...
        'BackgroundColor', PANEL, ...
        'Position',        [0.245, 0.03, 0.742, 0.87]);

    % -- Status line --
    hStatus = uicontrol(pRight, 'Style','text', ...
        'Position',          [20, 560, 820, 28], ...
        'String',            'System ready.  Select a scenario then press  START SIMULATION.', ...
        'FontSize',          11, 'FontWeight','bold', ...
        'ForegroundColor',   TXT, 'BackgroundColor', PANEL, ...
        'HorizontalAlignment','left');

    % -- Telemetry rows ---------------------------------------------------
    telY   = [520, 485, 450, 415, 380];
    labels = {'Conventional 87T Logic:',  ...
              'Signal Features (Real):',  ...
              'Model Trip Decision:',     ...
              'Peak  I_{diff}  (amps):', ...
              'Relay Latency:'};
    tags   = {'Lbl87T','LblFeat','LblTrip','LblIdiff','LblLat'};
    colFG  = {MUTED, [0.82 0.72 0.30], TXT, ACCENT, [0.30 0.82 0.60]};

    for k = 1:5
        uicontrol(pRight, 'Style','text', ...
            'Position',          [20, telY(k), 210, 22], ...
            'String',            labels{k}, ...
            'FontSize',          10, 'FontWeight','bold', ...
            'ForegroundColor',   MUTED, 'BackgroundColor', PANEL, ...
            'HorizontalAlignment','left');

        valWidth = 550;
        if k > 3, valWidth = 375; end

        uicontrol(pRight, 'Style','text', ...
            'Position',          [238, telY(k), valWidth, 22], ...
            'String',            char(8212), ...   % —
            'FontSize',          10.5, 'FontWeight','bold', ...
            'ForegroundColor',   colFG{k}, 'BackgroundColor', PANEL, ...
            'HorizontalAlignment','left', 'Tag', tags{k});
    end

    % -- Action badge  (TRIP / BLOCK / STANDBY) ---------------------------
    hAction = uicontrol(pRight, 'Style','text', ...
        'Position',          [630, 375, 185, 95], ...
        'String',            'STANDBY', ...
        'FontSize',          22, 'FontWeight','bold', ...
        'ForegroundColor',   TXT, 'BackgroundColor', [0.25 0.28 0.32], ...
        'HorizontalAlignment','center');

    % -- START SIMULATION button ------------------------------------------
    uicontrol(pRight, 'Style','pushbutton', ...
        'Position',          [625, 475, 192, 52], ...
        'String',            char(9654) + "  START SIMULATION", ...
        'FontSize',          12, 'FontWeight','bold', ...
        'ForegroundColor',   [0.20 0.80 1.00], ...
        'BackgroundColor',   [0.08 0.25 0.40], ...
        'TooltipString',     'Run the active scenario and display real relay output', ...
        'Callback', @(~,~) runSimWithTelemetry(f, modelName));

    % -- Waveform axes ----------------------------------------------------
    ax = axes('Parent', pRight, ...
        'Units',      'pixels', ...
        'Position',   [60, 40, 750, 310], ...
        'Color',      [0.07 0.09 0.12], ...
        'XColor',     TXT, 'YColor', TXT, ...
        'GridColor',  [0.35 0.38 0.42], 'GridAlpha', 0.4, ...
        'FontSize',   9.5, 'Box','on', 'TickDir','out', ...
        'XMinorTick', 'on', 'YMinorTick','on');
    grid(ax,'on');

    text(ax, 0.5, 0.5, ...
        'No waveform data yet  —  select a scenario and press  START SIMULATION', ...
        'Units','normalized', 'HorizontalAlignment','center', ...
        'Color', MUTED, 'FontSize', 11, 'FontAngle','italic', 'Tag','PlaceholderTxt');

    % ---- Collect handles ------------------------------------------------
    H = struct( ...
        'status', hStatus, ...
        'r87T',   findobj(pRight,'Tag','Lbl87T'), ...
        'Feat',   findobj(pRight,'Tag','LblFeat'), ...
        'Trip',   findobj(pRight,'Tag','LblTrip'), ...
        'Idiff',  findobj(pRight,'Tag','LblIdiff'), ...
        'Lat',    findobj(pRight,'Tag','LblLat'), ...
        'Action', hAction, ...
        'ax',     ax);

    setappdata(f, 'handles',         H);
    setappdata(f, 'currentScenario', 'Normal');
    setappdata(f, 'modelName',       modelName);
end


% =========================================================================
% AUTO-DETECT SIMULINK MODEL
% =========================================================================
function modelName = autoDetectSimulinkModel()
    modelName = '';
    openModels = find_system('SearchDepth', 0, 'Type', 'block_diagram');
    openModels = setdiff(openModels, {'simulink'});
    if ~isempty(openModels)
        modelName = openModels{1};
        return;
    end
    allFiles = [dir('*.slx'); dir('*.mdl')];
    if isempty(allFiles)
        errordlg('No Simulink model found. Navigate to your project folder first.', 'Model Not Found');
        return;
    end
    names = cell(numel(allFiles), 1);
    for i = 1:numel(allFiles)
        [~, names{i}] = fileparts(allFiles(i).name);
    end
    if numel(names) == 1
        modelName = names{1};
        load_system(modelName);
    else
        [idx, ok] = listdlg( ...
            'PromptString',  'Select the target Simulink plant:', ...
            'SelectionMode', 'single', ...
            'ListString',    names, ...
            'Name',          'Plant Selection', 'ListSize', [260, 160]);
        if ok
            modelName = names{idx};
            load_system(modelName);
        end
    end
end


% =========================================================================
% SCENARIO SETTER  — arms Simulink blocks and stores active scenario key
% =========================================================================
function setScenario(f, model, scenario)
    H = getappdata(f, 'handles');

    % Update stored scenario
    setappdata(f, 'currentScenario', scenario);

    faultTime = '0.05';   % seconds — fault inception for all fault scenarios

    try
        % Reset all fault blocks first
        set_param([model '/Internal_Fault'], ...
            'FaultA','off','FaultB','off','FaultC','off','GroundFault','off');
        set_param([model '/External_Fault'], ...
            'FaultA','off','FaultB','off','FaultC','off','GroundFault','off');
        set_param([model '/Step3'], 'Time', '10');
        set_param([model '/Step4'], 'Time', '10');

        switch scenario
            case 'Normal'
                % All steps deferred — normal load, no fault
            case 'Inrush'
                % Steps deferred — transformer energised without load
            case 'InternalAG'
                set_param([model '/Step3'], 'Time', faultTime);
                set_param([model '/Internal_Fault'], 'FaultA','on','GroundFault','on');
            case 'InternalBG'
                set_param([model '/Step3'], 'Time', faultTime);
                set_param([model '/Internal_Fault'], 'FaultB','on','GroundFault','on');
            case 'InternalAB'
                set_param([model '/Step3'], 'Time', faultTime);
                set_param([model '/Internal_Fault'], 'FaultA','on','FaultB','on');
            case 'InternalABC'
                set_param([model '/Step3'], 'Time', faultTime);
                set_param([model '/Internal_Fault'], ...
                    'FaultA','on','FaultB','on','FaultC','on');
            case 'External'
                set_param([model '/Step4'], 'Time', faultTime);
                set_param([model '/External_Fault'], ...
                    'FaultA','on','FaultB','on','FaultC','on');
            case 'ExternalAB'
                set_param([model '/Step4'], 'Time', faultTime);
                set_param([model '/External_Fault'], 'FaultA','on','FaultB','on');
        end

        statusMsg = sprintf('Scenario armed:  %s  —  Press START SIMULATION to run.', ...
                            scenarioTitle(scenario));
        set(H.status, 'String', statusMsg, 'ForegroundColor', [0.95 0.72 0.18]);

    catch ME
        set(H.status, ...
            'String', ['Block config warning: ' ME.message], ...
            'ForegroundColor', [0.90 0.65 0.20]);
        warning('[ControlPanel2] setScenario: %s', ME.message);
    end
end


% =========================================================================
% RUN SIMULATION  —  extract real relay outputs, update telemetry
% =========================================================================
function runSimWithTelemetry(f, model)
    H        = getappdata(f, 'handles');
    scenario = getappdata(f, 'currentScenario');
    if isempty(scenario), scenario = 'Normal'; end

    title = scenarioTitle(scenario);

    % -- UI: busy state ---------------------------------------------------
    set(H.status, ...
        'String', sprintf('Running simulation for  "%s" ...', title), ...
        'ForegroundColor', [0.95 0.72 0.18]);
    set(H.Action, 'String', 'RUNNING', 'BackgroundColor', [0.50 0.35 0.08]);
    set(H.r87T,  'String', 'Simulating…');
    set(H.Feat,  'String', 'Extracting signals…');
    set(H.Trip,  'String', 'Awaiting model output…');
    set(H.Idiff, 'String', char(8212));
    set(H.Lat,   'String', char(8212));
    drawnow;

    % -- Prepare log ------------------------------------------------------
    logDir = fullfile(pwd, 'IndividualRunLogs');
    if ~exist(logDir, 'dir'), mkdir(logDir); end

    timestamp = datestr(now, 'yyyymmdd_HHMMSS');
    % Log file name reflects actual scenario — no more hardcoded "normal_debug"
    logFile = fullfile(logDir, sprintf('%s_%s_%s.log', model, scenario, timestamp));
    matFile = fullfile(logDir, sprintf('%s_%s_%s.mat', model, scenario, timestamp));

    fid = fopen(logFile, 'w');
    if fid < 0
        errordlg('Could not create log file.', 'Logging Error');
        return;
    end
    cleanupFID = onCleanup(@() fclose(fid));

    % -- Log header (scenario-aware, never hardcodes NORMAL) ---------------
    fprintf(fid, '============================================================\n');
    fprintf(fid, 'SCENARIO DEBUG LOG:  %s\n', upper(title));
    fprintf(fid, '============================================================\n');
    fprintf(fid, 'Timestamp   : %s\n', datestr(now));
    fprintf(fid, 'Model       : %s\n', model);
    fprintf(fid, 'Scenario    : %s\n', scenario);
    fprintf(fid, 'Description : %s\n', title);
    fprintf(fid, 'MATLAB ver  : %s\n', version);
    fprintf(fid, 'Working dir : %s\n\n', pwd);

    % Log current block state (always scenario-specific)
    logBlockState(fid, model, scenario);

    % -- Enable signal logging for key relay signals -----------------------
    oldSigLog     = get_param(model, 'SignalLogging');
    oldSigLogName = get_param(model, 'SignalLoggingName');
    set_param(model, 'SignalLogging',     'on');
    set_param(model, 'SignalLoggingName', 'logsout');

    simOut    = [];
    debugData = struct('scenario', scenario, 'model', model, 'timestamp', timestamp);

    try
        stopT = get_param(model, 'StopTime');
        fprintf(fid, '--- SIMULATION RUN ---\nStopTime: %s\n', stopT);

        simOut = sim(model, ...
            'StopTime',                stopT, ...
            'ReturnWorkspaceOutputs',  'on');

        fprintf(fid, 'Simulation: SUCCESS\n');

        % ---- Extract REAL data from simulation output -------------------
        [time, idiff, nPhases] = extractRealDiffCurrent(simOut, fid);
        [tripped, tripTime]    = extractTripDecision(simOut, fid);

        % ---- Derived metrics --------------------------------------------
        peakIdiff = 0;
        if ~isempty(idiff) && ~isempty(time)
            peakIdiff = max(abs(idiff(:)));
        end

        faultInception = 0.05;  % seconds
        latencyMs      = NaN;
        if tripped && ~isnan(tripTime) && tripTime > faultInception
            latencyMs = (tripTime - faultInception) * 1000;
        end

        % ---- Interpret 87T result from actual trip signal ---------------
        [res87T, color87T] = interpret87TLogic(scenario, tripped, peakIdiff);

        % ---- Feature summary from real waveform -------------------------
        featStr = buildFeatureString(time, idiff, scenario);

        % ---- Action badge -----------------------------------------------
        if tripped
            actionStr   = 'TRIP';
            actionColor = [0.75 0.14 0.12];
        else
            actionStr   = 'BLOCK';
            actionColor = [0.10 0.52 0.28];
        end

        % ---- Update plot with real differential current -----------------
        updateWaveformPlot(H.ax, time, idiff, nPhases, scenario);

        % ---- Update telemetry rows --------------------------------------
        set(H.status, ...
            'String', sprintf('Analysis complete  |  Scenario: %s  |  Result: %s', title, actionStr), ...
            'ForegroundColor', [0.25 0.85 0.45]);
        set(H.r87T,  'String', res87T, 'ForegroundColor', color87T);
        set(H.Feat,  'String', featStr);
        set(H.Trip,  'String', sprintf('%s  (from relay TripSignal output)', actionStr));

        if peakIdiff > 0
            set(H.Idiff, 'String', sprintf('%.4f A  (peak differential  |  %.3f p.u.)', ...
                peakIdiff, peakIdiff / max(peakIdiff, 1)));
        else
            set(H.Idiff, 'String', 'No I_diff signal logged — see log file for details');
        end

        if ~isnan(latencyMs)
            set(H.Lat, 'String', sprintf('%.1f ms  (fault inception %.0f ms  →  trip at %.0f ms)', ...
                latencyMs, faultInception*1000, tripTime*1000));
        elseif tripped
            set(H.Lat, 'String', 'TRIP detected — inception time indeterminate');
        else
            set(H.Lat, 'String', 'N/A  (no trip event in this simulation)');
        end

        set(H.Action, 'String', actionStr, 'BackgroundColor', actionColor);

        % ---- Write results to log ---------------------------------------
        fprintf(fid, '\n--- RELAY OUTPUT (REAL MODEL RESPONSE) ---\n');
        fprintf(fid, '87T interpretation : %s\n', res87T);
        fprintf(fid, 'Trip decision       : %d  (%s)\n', tripped, actionStr);
        fprintf(fid, 'Peak Idiff          : %.4f A\n', peakIdiff);
        if ~isnan(latencyMs)
            fprintf(fid, 'Relay latency       : %.2f ms\n', latencyMs);
        else
            fprintf(fid, 'Relay latency       : N/A\n');
        end
        fprintf(fid, 'Signal features     : %s\n', featStr);
        fprintf(fid, '\n=== LOG COMPLETE ===\n');

        % ---- Save MAT ---------------------------------------------------
        debugData.simOut     = simOut;
        debugData.tripped    = tripped;
        debugData.peakIdiff  = peakIdiff;
        debugData.latencyMs  = latencyMs;
        save(matFile, 'debugData', '-v7.3');

        disp(' ');
        disp(['>>> ' upper(scenario) ' simulation complete.']);
        fprintf('    Trip: %s  |  Peak Idiff: %.4f A\n', actionStr, peakIdiff);
        if ~isnan(latencyMs)
            fprintf('    Latency: %.1f ms\n', latencyMs);
        end
        fprintf('    Log: %s\n', logFile);
        disp(' ');

        msgbox(sprintf('Simulation complete.\n\nScenario : %s\nResult   : %s\nPeak Idiff : %.4f A\n\nLog saved to:\n%s', ...
               title, actionStr, peakIdiff, logFile), ...
               'Simulation Complete', 'help');

    catch ME
        fprintf(fid, '\nSIMULATION FAILED\n%s\n', ...
            getReport(ME, 'extended', 'hyperlinks', 'off'));

        set(H.status, ...
            'String', sprintf('Simulation error: %s', ME.message), ...
            'ForegroundColor', [0.90 0.22 0.18]);
        set(H.Action, 'String', 'SYS FAULT', 'BackgroundColor', [0.45 0.10 0.08]);

        debugData.error = ME;
        save(matFile, 'debugData', '-v7.3');

        disp(['ERROR: ' ME.message]);
        fprintf('Debug log: %s\n', logFile);
        errordlg(sprintf('%s\n\nLog saved to:\n%s', ME.message, logFile), ...
                 'Simulation Error');
    end

    % Restore signal-logging settings
    set_param(model, 'SignalLogging',     oldSigLog);
    set_param(model, 'SignalLoggingName', oldSigLogName);
end


% =========================================================================
% SCENARIO TITLE LOOKUP  —  human-readable description for any scenario key
% =========================================================================
function t = scenarioTitle(scenario)
    map = containers.Map( ...
        {'Normal',   'Inrush',  'InternalAG',                'InternalBG', ...
         'InternalAB',                        'InternalABC', ...
         'External',                          'ExternalAB'}, ...
        {'Normal Load Condition (Healthy Operation)', ...
         'Magnetizing Inrush (Energisation — No Load)', ...
         'Internal Fault — Phase A to Ground', ...
         'Internal Fault — Phase B to Ground', ...
         'Internal Fault — Phase A-B (Phase-to-Phase)', ...
         'Internal Fault — 3-Phase Symmetric', ...
         'External Through-Fault — 3-Phase', ...
         'External Through-Fault — Phase A-B'});

    if isKey(map, scenario)
        t = map(scenario);
    else
        t = scenario;
    end
end


% =========================================================================
% LOG HELPER — block state written with actual scenario context
% =========================================================================
function logBlockState(fid, model, scenario)
    fprintf(fid, '--- BLOCK CONFIGURATION  (%s) ---\n', scenario);
    paramNames = {'Step3.Time', 'Step4.Time', ...
                  'Internal_Fault.FaultA', 'Internal_Fault.FaultB', ...
                  'Internal_Fault.FaultC', 'Internal_Fault.GroundFault', ...
                  'External_Fault.FaultA', 'External_Fault.FaultB', ...
                  'External_Fault.FaultC', 'External_Fault.GroundFault'};
    blocks  = {'Step3',         'Step4', ...
               'Internal_Fault','Internal_Fault','Internal_Fault','Internal_Fault', ...
               'External_Fault','External_Fault','External_Fault','External_Fault'};
    params  = {'Time',     'Time', ...
               'FaultA','FaultB','FaultC','GroundFault', ...
               'FaultA','FaultB','FaultC','GroundFault'};
    for k = 1:numel(paramNames)
        try
            val = get_param([model '/' blocks{k}], params{k});
            fprintf(fid, '  %-40s : %s\n', paramNames{k}, val);
        catch
            fprintf(fid, '  %-40s : <not accessible>\n', paramNames{k});
        end
    end
    fprintf(fid, '\n');
end


% =========================================================================
% EXTRACT REAL DIFFERENTIAL CURRENT FROM SIM OUTPUT
%   Tries multiple access paths before giving up.
%   Returns empty arrays (never synthetic data) if unavailable.
% =========================================================================
function [time, idiff, nPhases] = extractRealDiffCurrent(simOut, fid)
    time    = [];
    idiff   = [];
    nPhases = 3;

    % --- Attempt 1: direct To-Workspace variable 'I_diff' ----------------
    try
        raw = simOut.get('I_diff');
        [time, idiff] = unwrapTimeSeries(raw);
        if ~isempty(idiff)
            nPhases = min(3, size(idiff, 2));
            fprintf(fid, 'I_diff: extracted via simOut.get(''I_diff'')  [%d x %d]\n', ...
                    size(idiff,1), size(idiff,2));
            return;
        end
    catch
    end

    % --- Attempt 2: logsout element 'I_diff' or 'relay_I_diff' ----------
    for sigName = {'I_diff', 'relay_I_diff', 'relay_I_diff_window'}
        try
            logs = simOut.get('logsout');
            el   = logs.get(sigName{1});
            [time, idiff] = unwrapTimeSeries(el.Values);
            if ~isempty(idiff)
                nPhases = min(3, size(idiff, 2));
                fprintf(fid, 'I_diff: extracted from logsout.get(''%s'')\n', sigName{1});
                return;
            end
        catch
        end
    end

    % --- Attempt 3: compute from I_primary_abc − I_secondary_abc ---------
    try
        rawP = simOut.get('I_primary_abc');
        rawS = simOut.get('I_secondary_abc');
        [tP, dP] = unwrapTimeSeries(rawP);
        [tS, dS] = unwrapTimeSeries(rawS);
        if ~isempty(dP) && ~isempty(dS)
            % Interpolate to common time base (primary)
            if ~isequal(tP, tS)
                dS = interp1(tS, dS, tP, 'linear', 'extrap');
            end
            time   = tP;
            idiff  = dP - dS;
            nPhases = min(3, size(idiff, 2));
            fprintf(fid, 'I_diff: computed as I_primary_abc - I_secondary_abc  [%d x %d]\n', ...
                    size(idiff,1), size(idiff,2));
            return;
        end
    catch
    end

    % --- Nothing found ---------------------------------------------------
    fprintf(fid, 'WARNING: Could not extract I_diff by any method. ');
    fprintf(fid, 'Enable "Log data to workspace" on the I_diff signal line, ');
    fprintf(fid, 'or ensure To Workspace blocks for I_primary_abc / I_secondary_abc are active.\n');
end


% =========================================================================
% EXTRACT TRIP DECISION FROM SIM OUTPUT
%   Returns tripped (bool) and the time at which trip went high.
% =========================================================================
function [tripped, tripTime] = extractTripDecision(simOut, fid)
    tripped  = false;
    tripTime = NaN;

    candidateNames = {'TripSignal',  'Trip_Signal', ...
                      'relay_trip_signal_out', 'relay_trip_latch', ...
                      'top_relay_trip_to_breakers'};

    % Try direct workspace variables
    for cn = candidateNames
        try
            raw = simOut.get(cn{1});
            [t, v] = unwrapTimeSeries(raw);
            if ~isempty(v)
                idx = find(v(:,1) > 0.5, 1, 'first');
                if ~isempty(idx)
                    tripped  = true;
                    tripTime = t(min(idx, numel(t)));
                end
                fprintf(fid, 'TripSignal: from simOut.get(''%s'')  tripped=%d\n', cn{1}, tripped);
                return;
            end
        catch
        end
    end

    % Try logsout
    try
        logs = simOut.get('logsout');
        for cn = candidateNames
            try
                el = logs.get(cn{1});
                [t, v] = unwrapTimeSeries(el.Values);
                if ~isempty(v)
                    idx = find(v(:,1) > 0.5, 1, 'first');
                    if ~isempty(idx)
                        tripped  = true;
                        tripTime = t(min(idx, numel(t)));
                    end
                    fprintf(fid, 'TripSignal: from logsout.get(''%s'')  tripped=%d\n', cn{1}, tripped);
                    return;
                end
            catch
            end
        end
    catch
    end

    fprintf(fid, 'WARNING: TripSignal not found in any output. ');
    fprintf(fid, 'Enable logging on Trip_Signal line in the Hybrid 87T Relay subsystem.\n');
end


% =========================================================================
% UNWRAP TIMESERIES OR STRUCT — returns [time, data] as plain matrices
% =========================================================================
function [t, d] = unwrapTimeSeries(raw)
    t = []; d = [];
    if isempty(raw), return; end
    if isa(raw, 'timeseries')
        t = raw.Time;
        d = raw.Data;
    elseif isa(raw, 'Simulink.SimulationData.Signal')
        t = raw.Values.Time;
        d = raw.Values.Data;
    elseif isstruct(raw) && isfield(raw, 'time')
        t = raw.time;
        d = raw.signals.values;
    elseif isnumeric(raw)
        % Plain array (e.g., n-by-3) — generate a dummy time axis
        d = raw;
        t = (0:size(raw,1)-1)' * 6.25e-4;  % matches SampleTime in paramlist
    else
        try
            t = raw.Time;
            d = raw.Data;
        catch
        end
    end
    % Flatten 3-D arrays (e.g., n-by-1-by-3 from some Dataset formats)
    if ndims(d) == 3
        d = squeeze(d);
    end
end


% =========================================================================
% INTERPRET CONVENTIONAL 87T LOGIC FROM ACTUAL TRIP OUTPUT
% =========================================================================
function [res87T, color] = interpret87TLogic(scenario, tripped, peakIdiff)
    isInternal = startsWith(scenario, 'Internal');
    isNormal   = strcmp(scenario, 'Normal');
    isInrush   = strcmp(scenario, 'Inrush');
    isExternal = startsWith(scenario, 'External');

    if tripped && isInternal
        res87T = sprintf('TRIP   —  Idiff >> pickup slope  (peak = %.3f A)', peakIdiff);
        color  = [0.90 0.40 0.20];

    elseif ~tripped && (isNormal || isInrush || isExternal)
        res87T = sprintf('BLOCK  —  Idiff below restraint threshold  (peak = %.4f A)', peakIdiff);
        color  = [0.60 0.65 0.70];

    elseif tripped && ~isInternal
        res87T = sprintf('TRIP   ***  MALOPERATION DETECTED  ***  peak = %.3f A', peakIdiff);
        color  = [0.90 0.22 0.18];

    elseif ~tripped && isInternal
        res87T = sprintf('BLOCK  ***  MISSED TRIP DETECTED  ***  peak = %.3f A', peakIdiff);
        color  = [0.90 0.22 0.18];

    else
        res87T = sprintf('Undetermined  (peak Idiff = %.3f A)', peakIdiff);
        color  = [0.60 0.65 0.70];
    end
end


% =========================================================================
% BUILD FEATURE SUMMARY STRING FROM REAL WAVEFORM
% =========================================================================
function s = buildFeatureString(time, idiff, scenario)
    if isempty(idiff) || isempty(time)
        s = 'No waveform data extracted — check I_diff logging configuration.';
        return;
    end

    flat     = idiff(:);
    peakVal  = max(abs(flat));
    rmsVal   = sqrt(mean(flat.^2));
    nSamples = numel(time);
    dur_ms   = (time(end) - time(1)) * 1e3;

    % Simple harmonic ratio (2nd / fundamental) from phase-A if available
    harmRatio = computeSecondHarmonicRatio(time, idiff(:,1));

    if ~isnan(harmRatio)
        s = sprintf('Peak: %.3f A | RMS: %.3f A | 2nd Harmonic: %.1f%% | Samples: %d | Duration: %.1f ms', ...
            peakVal, rmsVal, harmRatio*100, nSamples, dur_ms);
    else
        s = sprintf('Peak: %.3f A | RMS: %.3f A | Samples: %d | Duration: %.1f ms', ...
            peakVal, rmsVal, nSamples, dur_ms);
    end
end


% =========================================================================
% COMPUTE 2ND HARMONIC RATIO  (used to distinguish inrush from fault)
% =========================================================================
function ratio = computeSecondHarmonicRatio(time, sig)
    ratio = NaN;
    try
        if numel(time) < 64, return; end
        fs      = 1 / mean(diff(time));
        N       = numel(sig);
        Y       = fft(sig);
        freqs   = (0:N-1) * (fs/N);
        f0      = 50;          % fundamental (Hz) — 50 Hz system per paramlist
        [~, i1] = min(abs(freqs - f0));
        [~, i2] = min(abs(freqs - 2*f0));
        mag1    = abs(Y(i1));
        mag2    = abs(Y(i2));
        if mag1 > 0
            ratio = mag2 / mag1;
        end
    catch
    end
end


% =========================================================================
% UPDATE WAVEFORM AXES WITH REAL DATA
% =========================================================================
function updateWaveformPlot(ax, time, idiff, nPhases, scenario)
    phColors = [0.18 0.82 0.84; 0.98 0.72 0.18; 0.90 0.32 0.72];
    phNames  = {'Phase A', 'Phase B', 'Phase C'};
    TXT      = [0.95 0.95 0.95];
    MUTED    = [0.60 0.65 0.70];
    GRID_C   = [0.35 0.38 0.42];
    AX_C     = [0.75 0.78 0.82];

    cla(ax); hold(ax, 'on');

    if isempty(time) || isempty(idiff)
        text(ax, 0.5, 0.5, ...
            {'I_{diff} signal not found in simulation output.', ...
             'Enable data logging on the I_diff signal line in the', ...
             'Hybrid 87T Relay subsystem and re-run.'}, ...
            'Units','normalized', 'HorizontalAlignment','center', ...
            'Color', MUTED, 'FontSize', 10.5, 'FontAngle','italic');
        hold(ax, 'off');
        return;
    end

    nPlot = min(nPhases, size(idiff, 2));
    for k = 1:nPlot
        plot(ax, time*1e3, idiff(:,k), ...
            'Color', phColors(k,:), 'LineWidth', 1.5, ...
            'DisplayName', phNames{k});
    end

    % Mark fault inception
    if ~ismember(scenario, {'Normal', 'Inrush'})
        xline(ax, 50, '--', ...
            'Color', [1 0.38 0.28], 'LineWidth', 1.2, ...
            'Label', 'Fault Inception (50 ms)', ...
            'LabelVerticalAlignment', 'bottom', ...
            'FontSize', 9, 'FontAngle', 'italic', ...
            'HandleVisibility', 'off');
    end

    hold(ax, 'off');

    % Dynamic title
    titleMap = containers.Map( ...
        {'Normal','Inrush','InternalAG','InternalBG','InternalAB','InternalABC','External','ExternalAB'}, ...
        {'Normal Operation  —  Differential Current Baseline', ...
         'Magnetizing Inrush  —  Decaying DC Offset Signature', ...
         'Internal Fault (A-G)  —  Phase A Flux Saturation Rise', ...
         'Internal Fault (B-G)  —  Phase B Flux Saturation Rise', ...
         'Internal Fault (A-B)  —  Phase-to-Phase Current Escalation', ...
         'Internal Fault (3\Phi)  —  Symmetric Catastrophic Rise', ...
         'External Through-Fault (3\Phi)  —  Restraint Dominant', ...
         'External Through-Fault (A-B)  —  Restraint Dominant'});

    if isKey(titleMap, scenario)
        titleStr = titleMap(scenario);
    else
        titleStr = scenario;
    end

    title(ax, titleStr,    'Color', TXT,   'FontSize', 10.5, 'FontWeight', 'normal');
    xlabel(ax, 'Time  (ms)', 'Color', AX_C, 'FontSize', 10);
    ylabel(ax, 'I_{diff}  (A)', 'Color', AX_C, 'FontSize', 10);

    grid(ax,'on');
    ax.GridColor    = GRID_C;
    ax.GridAlpha    = 0.40;
    ax.XLim         = [0, max(time)*1e3];
    ax.TickDir      = 'out';
    ax.XMinorTick   = 'on';
    ax.YMinorTick   = 'on';
    ax.FontSize      = 9.5;
    ax.XColor        = AX_C;
    ax.YColor        = AX_C;

    yMax = max(abs(idiff(:)));
    if yMax < 0.01, yMax = 0.5; end
    ax.YLim = [-yMax*1.25, yMax*1.25];

    if nPlot > 1
        leg = legend(ax, 'Location','northeast', 'FontSize', 9, 'TextColor', TXT);
        leg.Color     = [0.10 0.13 0.16];
        leg.EdgeColor = GRID_C;
    end

    delete(findobj(ax, 'Tag', 'PlaceholderTxt'));
end


% =========================================================================
% BATCH DATASET GENERATOR  (unchanged from ControlPanel2 v2.0)
% =========================================================================
function generateBatch(model, hSampleCount)
    nSamples = str2double(get(hSampleCount, 'String'));
    if isnan(nSamples) || nSamples < 1
        errordlg('Please enter a valid number of samples (e.g., 500)');
        return;
    end
    nSamples = round(nSamples);

    answer = questdlg( ...
        sprintf('Generate %d random scenarios?\n\nEstimated time: ~%d seconds', ...
                nSamples, round(nSamples * 1.5)), ...
        'Confirm Batch Generation', 'Generate', 'Cancel', 'Generate');
    if ~strcmp(answer, 'Generate'), return; end

    disp(' ');
    disp('╔═══════════════════════════════════════════════════════════╗');
    disp('║          BATCH DATASET GENERATION STARTED                 ║');
    disp('╚═══════════════════════════════════════════════════════════╝');
    fprintf('Generating %d samples...\n', nSamples);

    dataset = struct();
    dataset.metadata.nSamples      = nSamples;
    dataset.metadata.generatedDate = datetime('now');
    dataset.metadata.modelName     = model;

    dataset.zone            = cell(nSamples, 1);
    dataset.faultType       = cell(nSamples, 1);
    dataset.faultResistance = zeros(nSamples, 1);
    dataset.inceptionAngle  = zeros(nSamples, 1);
    dataset.inceptionTime   = zeros(nSamples, 1);
    dataset.shouldTrip      = false(nSamples, 1);
    dataset.primaryCurrent  = cell(nSamples, 1);
    dataset.secondaryCurrent = cell(nSamples, 1);
    dataset.diffCurrent     = cell(nSamples, 1);
    dataset.tripSignal      = cell(nSamples, 1);
    dataset.simulationStatus = cell(nSamples, 1);
    dataset.noiseLevel      = zeros(nSamples, 1);
    dataset.ctMismatch      = cell(nSamples, 1);

    hWait = waitbar(0, 'Initialising…', 'Name', 'Batch Generation Progress');

    try
        for i = 1:nSamples
            if mod(i, 10) == 0
                waitbar(i/nSamples, hWait, ...
                    sprintf('Generating sample %d/%d…', i, nSamples));
            end

            scenarioRand = rand();
            if scenarioRand < 0.15
                dataset.zone{i}            = 'Normal';
                dataset.faultType{i}       = 'None';
                dataset.faultResistance(i) = 0;
                dataset.inceptionAngle(i)  = 0;
                dataset.inceptionTime(i)   = 0;
                dataset.shouldTrip(i)      = false;
                configureNormalScenario(model);

            elseif scenarioRand < 0.30
                dataset.zone{i}            = 'Inrush';
                dataset.faultType{i}       = 'Inrush';
                dataset.faultResistance(i) = 0;
                dataset.inceptionAngle(i)  = randi([0, 360]);
                dataset.inceptionTime(i)   = 0.05;
                dataset.shouldTrip(i)      = false;
                configureInrushScenario(model);

            elseif scenarioRand < 0.75
                dataset.zone{i}    = 'Internal';
                [fType, Rf]        = generateRandomFault();
                dataset.faultType{i}       = fType;
                dataset.faultResistance(i) = Rf;
                angle                      = randi([0, 360]);
                dataset.inceptionAngle(i)  = angle;
                faultTime                  = angleToTime(angle);
                dataset.inceptionTime(i)   = faultTime;
                dataset.shouldTrip(i)      = true;
                configureInternalFault(model, fType, Rf, faultTime);

            else
                dataset.zone{i}    = 'External';
                [fType, Rf]        = generateRandomFault();
                dataset.faultType{i}       = fType;
                dataset.faultResistance(i) = Rf;
                angle                      = randi([0, 360]);
                dataset.inceptionAngle(i)  = angle;
                faultTime                  = angleToTime(angle);
                dataset.inceptionTime(i)   = faultTime;
                dataset.shouldTrip(i)      = false;
                configureExternalFault(model, fType, Rf, faultTime);
            end

            % Noise and CT mismatch injection
            global_noise_level = 0.01 + (0.06 * rand());
            ct_mismatches      = 0.98 + (0.04 * rand(6, 1));
            dataset.noiseLevel(i) = global_noise_level;
            dataset.ctMismatch{i} = ct_mismatches;

            try
                for ch = 1:6
                    set_param(sprintf('%s/Noise Merging Unit/CT_Gain_Mismatch_%d', model, ch), ...
                              'Gain', num2str(ct_mismatches(ch)));
                    set_param(sprintf('%s/Noise Merging Unit/Noise_Gain_%d', model, ch), ...
                              'Gain', num2str(global_noise_level));
                end
            catch
                if i == 1
                    disp('  Warning: Noise Merging Unit not found — continuing without noise injection');
                end
            end

            try
                simOut = sim(model, 'StopTime', '1.0');

                try
                    dataset.primaryCurrent{i} = simOut.get('I_primary_abc');
                catch
                    try,  dataset.primaryCurrent{i}  = simOut.I_primary_abc;  catch,  dataset.primaryCurrent{i}  = []; end
                end
                try
                    dataset.secondaryCurrent{i} = simOut.get('I_secondary_abc');
                catch
                    try,  dataset.secondaryCurrent{i} = simOut.I_secondary_abc; catch, dataset.secondaryCurrent{i} = []; end
                end
                try
                    dataset.diffCurrent{i} = simOut.get('I_diff');
                catch
                    try,  dataset.diffCurrent{i} = simOut.I_diff; catch, dataset.diffCurrent{i} = []; end
                end
                try
                    dataset.tripSignal{i} = simOut.get('TripSignal');
                catch
                    try,  dataset.tripSignal{i} = simOut.TripSignal; catch, dataset.tripSignal{i} = []; end
                end

                dataset.simulationStatus{i} = 'Success';

            catch ME
                fprintf('  Sample %d failed: %s\n', i, ME.message);
                dataset.simulationStatus{i}  = sprintf('Failed: %s', ME.message);
                dataset.primaryCurrent{i}    = [];
                dataset.secondaryCurrent{i}  = [];
                dataset.diffCurrent{i}       = [];
                dataset.tripSignal{i}        = [];
            end

            pause(0.01);
        end

        timestamp = datestr(now, 'yyyymmdd_HHMMSS');
        filename  = sprintf('TransformerProtection_Dataset_%s.mat', timestamp);
        save(filename, 'dataset');
        close(hWait);

        successCount = sum(strcmp(dataset.simulationStatus, 'Success'));
        successRate  = (successCount / nSamples) * 100;

        disp(' ');
        disp('╔═══════════════════════════════════════════════════════════╗');
        disp('║          BATCH GENERATION COMPLETED                       ║');
        disp('╚═══════════════════════════════════════════════════════════╝');
        fprintf('Generated: %d samples  (%d successful, %.1f%%)\n', ...
                nSamples, successCount, successRate);
        fprintf('Saved to : %s\n', filename);
        fprintf('Normal   : %d\n', sum(strcmp(dataset.zone, 'Normal')));
        fprintf('Inrush   : %d\n', sum(strcmp(dataset.zone, 'Inrush')));
        fprintf('Internal : %d\n', sum(strcmp(dataset.zone, 'Internal')));
        fprintf('External : %d\n', sum(strcmp(dataset.zone, 'External')));

        msgbox(sprintf('Generated %d samples (%.1f%% success).\n\nSaved to: %s', ...
               nSamples, successRate, filename), ...
               'Batch Complete', 'help');

    catch ME
        if isvalid(hWait), close(hWait); end
        errordlg(['Batch generation error: ' ME.message], 'Error');
        rethrow(ME);
    end
end


% =========================================================================
% BATCH HELPER — FAULT / SCENARIO CONFIGURATION
% =========================================================================
function [faultType, Rf] = generateRandomFault()
    faultTypes = {'AG','BG','CG','AB','BC','CA','ABC','ABG','BCG','CAG'};
    faultType  = faultTypes{randi(length(faultTypes))};
    Rf = 10^(rand() * (log10(20) - log10(0.01)) + log10(0.01));
end

function configureNormalScenario(model)
    resetFaultBlocks(model);
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
end

function configureInrushScenario(model)
    resetFaultBlocks(model);
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
end

function configureInternalFault(model, faultType, Rf, faultTime)
    resetFaultBlocks(model);
    set_param([model '/Step3'], 'Time', num2str(faultTime));
    set_param([model '/Step4'], 'Time', '10');
    [fA, fB, fC, fG] = decodeFaultType(faultType);
    set_param([model '/Internal_Fault'], ...
        'FaultA', fA, 'FaultB', fB, 'FaultC', fC, 'GroundFault', fG);
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
        set_param([model '/External_Fault'], ...
            'FaultA', fA, 'FaultB', fB, 'FaultC', fC, 'GroundFault', fG);
        set_param([model '/External_Fault'], 'FaultResistance', num2str(Rf));
    catch
    end
end

function [fA, fB, fC, fG] = decodeFaultType(faultType)
    fA = 'off'; fB = 'off'; fC = 'off'; fG = 'off';
    if contains(faultType, 'A'), fA = 'on'; end
    if contains(faultType, 'B'), fB = 'on'; end
    if contains(faultType, 'C'), fC = 'on'; end
    if contains(faultType, 'G'), fG = 'on'; end
end

function faultTime = angleToTime(angle)
    frequency  = 50;    % Hz — 50 Hz system (paramlist confirms 50 Hz)
    baseTime   = 0.5;   % seconds
    cyclePeriod = 1 / frequency;
    faultTime  = baseTime + (angle / 360) * cyclePeriod;
end

function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
    set_param([model '/Internal_Fault'], ...
        'FaultA','off','FaultB','off','FaultC','off','GroundFault','off');
    set_param([model '/External_Fault'], ...
        'FaultA','off','FaultB','off','FaultC','off','GroundFault','off');
end