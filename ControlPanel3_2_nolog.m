function ControlPanel2
% =========================================================================
% TRANSFORMER PROTECTION CONTROL PANEL  v4.2 (No Logging)
% Hybrid UI  |  Real Model Response  |  Scenario-Aware
% =========================================================================

    % ---- AUTO-DETECT SIMULINK MODEL ----
    modelName = autoDetectSimulinkModel();
    if isempty(modelName), return; end

    % ---- AUTO-INSTRUMENT THE RELAY SUBSYSTEM ----
    instrumentationSuccess = autoInstrumentModel(modelName);

    % ---- THEME ----------------------------------------------------------
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

    if instrumentationSuccess
        instStr = 'Ground-Truth Signal Logging: AUTOMATICALLY WIRED';
        instCol = [0.25 0.85 0.45];
    else
        instStr = 'Warning: Could not auto-wire internal relay signals';
        instCol = [0.90 0.45 0.15];
    end

    uicontrol(f, 'Style','text', ...
        'Position',          [0, FIG_H-65, FIG_W, 22], ...
        'String',            sprintf('Target Plant: %s.slx   |   %s', modelName, instStr), ...
        'FontSize',          10, 'FontAngle','italic', ...
        'ForegroundColor',   instCol, 'BackgroundColor', BG, ...
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

    pBatch = uipanel(pLeft, ...
        'Title',           'Training Data Generator', ...
        'FontSize',        10, 'FontWeight','bold', ...
        'ForegroundColor', [0.75 0.55 0.95], ...
        'BackgroundColor', [0.12 0.16 0.20], ...
        'Units',           'pixels', ...
        'Position',        [8, 50, 222, 100]);

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

    hStatus = uicontrol(pRight, 'Style','text', ...
        'Position',          [20, 560, 820, 28], ...
        'String',            'System ready.  Select a scenario then press  START SIMULATION.', ...
        'FontSize',          11, 'FontWeight','bold', ...
        'ForegroundColor',   TXT, 'BackgroundColor', PANEL, ...
        'HorizontalAlignment','left');

    telY   = [520, 485, 450, 415, 380];
    labels = {'Conventional 87T Logic:', 'Signal Features (Real):', 'Model Trip Decision:', 'Peak  I_{diff}  (p.u.):', 'Relay Latency:'};
    tags   = {'Lbl87T','LblFeat','LblTrip','LblIdiff','LblLat'};
    colFG  = {MUTED, [0.82 0.72 0.30], TXT, ACCENT, [0.30 0.82 0.60]};

    for k = 1:5
        uicontrol(pRight, 'Style','text', ...
            'Position',          [20, telY(k), 210, 22], ...
            'String',            labels{k}, ...
            'FontSize',          10, 'FontWeight','bold', ...
            'ForegroundColor',   MUTED, 'BackgroundColor', PANEL, ...
            'HorizontalAlignment','left', 'Tag', ['Ttl' tags{k}]);

        valWidth = 550; if k > 3, valWidth = 375; end
        uicontrol(pRight, 'Style','text', ...
            'Position',          [238, telY(k), valWidth, 22], ...
            'String',            char(8212), ...
            'FontSize',          10.5, 'FontWeight','bold', ...
            'ForegroundColor',   colFG{k}, 'BackgroundColor', PANEL, ...
            'HorizontalAlignment','left', 'Tag', tags{k});
    end

    hAction = uicontrol(pRight, 'Style','text', ...
        'Position',          [630, 375, 185, 95], ...
        'String',            'STANDBY', ...
        'FontSize',          22, 'FontWeight','bold', ...
        'ForegroundColor',   TXT, 'BackgroundColor', [0.25 0.28 0.32], ...
        'HorizontalAlignment','center');

    uicontrol(pRight, 'Style','pushbutton', ...
        'Position',          [625, 475, 192, 52], ...
        'String',            char(9654) + "  START SIMULATION", ...
        'FontSize',          12, 'FontWeight','bold', ...
        'ForegroundColor',   [0.20 0.80 1.00], ...
        'BackgroundColor',   [0.08 0.25 0.40], ...
        'Callback', @(~,~) runSimWithTelemetry(f, modelName));

    ax = axes('Parent', pRight, 'Units', 'pixels', 'Position', [60, 40, 750, 310], ...
        'Color', [0.07 0.09 0.12], 'XColor', TXT, 'YColor', TXT, ...
        'GridColor', [0.35 0.38 0.42], 'GridAlpha', 0.4, 'FontSize', 9.5, 'Box','on', 'TickDir','out');
    grid(ax,'on');

    text(ax, 0.5, 0.5, 'No waveform data yet  —  select a scenario and press  START SIMULATION', ...
        'Units','normalized', 'HorizontalAlignment','center', 'Color', MUTED, 'FontSize', 11, 'FontAngle','italic', 'Tag','PlaceholderTxt');

    H = struct('status', hStatus, 'TtlIdiff', findobj(pRight,'Tag','TtlLblIdiff'), ...
        'r87T', findobj(pRight,'Tag','Lbl87T'), 'Feat', findobj(pRight,'Tag','LblFeat'), ...
        'Trip', findobj(pRight,'Tag','LblTrip'), 'Idiff', findobj(pRight,'Tag','LblIdiff'), ...
        'Lat', findobj(pRight,'Tag','LblLat'), 'Action', hAction, 'ax', ax);

    setappdata(f, 'handles', H);
    setappdata(f, 'currentScenario', 'Normal');
    setappdata(f, 'modelName', modelName);
end

% =========================================================================
% AUTO-INSTRUMENTATION  (resilient — name fallbacks + signal-line search)
% =========================================================================
function success = autoInstrumentModel(modelName)
    success = false;
    if ~bdIsLoaded(modelName), load_system(modelName); end
    relayPath = [modelName '/Hybrid 87T Relay'];

    targets = { ...
        'TripSignal', {'S-R Latch'}, {}; ...
        'I_diff',     {'I_diff','Idiff','I_Diff'},                 {'I_diff','Idiff'}; ...
        'I_rest',     {'I_rest','Irest','I_Rest'},                 {'I_rest','Irest'}  ...
    };

    okFlags = false(size(targets,1),1);
    for k = 1:size(targets,1)
        okFlags(k) = instrumentTarget(relayPath, targets{k,2}, targets{k,3}, targets{k,1});
    end

    try
        set_param(modelName, 'SignalLogging', 'on');
        set_param(modelName, 'SignalLoggingName', 'logsout');
    catch
    end

    success = okFlags(1) && okFlags(2);
    if success
        fprintf('Auto-Instrumentation OK: Trip=%d  Idiff=%d  Irest=%d\n', okFlags);
    else
        fprintf('Auto-Instrumentation partial: Trip=%d  Idiff=%d  Irest=%d\n', okFlags);
    end
end

function wired = instrumentTarget(parentPath, blockNameList, signalNameList, logName)
    wired = false;

    for nm = blockNameList
        try
            blks = find_system(parentPath, 'LookUnderMasks','all', ...
                               'FollowLinks','on', 'SearchDepth', 1, ...
                               'Name', nm{1});
            if ~isempty(blks)
                if wireBlockOutput(blks{1}, logName), wired = true; return; end
            end
        catch
        end
    end

    for sn = signalNameList
        try
            lines = find_system(parentPath, 'FindAll','on', ...
                                'LookUnderMasks','all', 'FollowLinks','on', ...
                                'Type','line', 'Name', sn{1});
            for li = 1:numel(lines)
                srcPort = get_param(lines(li), 'SrcPortHandle');
                if srcPort > 0
                    set_param(srcPort, 'DataLogging', 'on');
                    set_param(srcPort, 'DataLoggingNameMode', 'Custom');
                    set_param(srcPort, 'DataLoggingName', logName);
                    wired = true;
                    return;
                end
            end
        catch
        end
    end
end

function ok = wireBlockOutput(blk, logName)
    ok = false;
    try
        bType = get_param(blk, 'BlockType');
        if strcmp(bType, 'Outport') || strcmp(bType, 'Goto')
            lh = get_param(blk, 'LineHandles');
            if isfield(lh, 'Inport') && lh.Inport > 0
                srcPort = get_param(lh.Inport, 'SrcPortHandle');
                if srcPort > 0
                    set_param(srcPort, 'DataLogging', 'on');
                    set_param(srcPort, 'DataLoggingNameMode', 'Custom');
                    set_param(srcPort, 'DataLoggingName', logName);
                    ok = true;
                end
            end
        else
            ph = get_param(blk, 'PortHandles');
            if ~isempty(ph.Outport)
                set_param(ph.Outport(1), 'DataLogging', 'on');
                set_param(ph.Outport(1), 'DataLoggingNameMode', 'Custom');
                set_param(ph.Outport(1), 'DataLoggingName', logName);
                ok = true;
            end
        end
    catch
    end
end

% =========================================================================
% AUTO-DETECT SIMULINK MODEL
% =========================================================================
function modelName = autoDetectSimulinkModel()
    modelName = '';
    openModels = find_system('SearchDepth', 0, 'Type', 'block_diagram');
    openModels = setdiff(openModels, {'simulink'});
    if ~isempty(openModels), modelName = openModels{1}; return; end

    allFiles = [dir('*.slx'); dir('*.mdl')];
    if isempty(allFiles)
        errordlg('No Simulink model found. Navigate to your project folder.', 'Error');
        return;
    end
    [~, modelName] = fileparts(allFiles(1).name);
    load_system(modelName);
end

% =========================================================================
% SCENARIO SETTER
% =========================================================================
function setScenario(f, model, scenario)
    H = getappdata(f, 'handles');
    setappdata(f, 'currentScenario', scenario);
    faultTime = '0.05';

    try
        resetFaultBlocks(model);
        if ~strcmp(scenario, 'Inrush'), setBreakersClosed(model); end
        switch scenario
            case 'Normal'
            case 'Inrush'
                setInrushEnergization(model);
            case 'InternalAG',  set_param([model '/Step3'], 'Time', faultTime); set_param([model '/Internal_Fault'], 'FaultA','on','GroundFault','on');
            case 'InternalBG',  set_param([model '/Step3'], 'Time', faultTime); set_param([model '/Internal_Fault'], 'FaultB','on','GroundFault','on');
            case 'InternalAB',  set_param([model '/Step3'], 'Time', faultTime); set_param([model '/Internal_Fault'], 'FaultA','on','FaultB','on');
            case 'InternalABC', set_param([model '/Step3'], 'Time', faultTime); set_param([model '/Internal_Fault'], 'FaultA','on','FaultB','on','FaultC','on');
            case 'External',    set_param([model '/Step4'], 'Time', faultTime); set_param([model '/External_Fault'], 'FaultA','on','FaultB','on','FaultC','on');
            case 'ExternalAB',  set_param([model '/Step4'], 'Time', faultTime); set_param([model '/External_Fault'], 'FaultA','on','FaultB','on');
        end

        statusMsg = sprintf('Scenario armed:  %s  —  Press START SIMULATION to run.', scenarioTitle(scenario));
        set(H.status, 'String', statusMsg, 'ForegroundColor', [0.95 0.72 0.18]);
    catch ME
        warning('ControlPanel:ScenarioError', '[ControlPanel] %s', ME.message);
    end
end

% =========================================================================
% RUN SIMULATION
% =========================================================================
function runSimWithTelemetry(f, model)
    H        = getappdata(f, 'handles');
    scenario = getappdata(f, 'currentScenario');
    if isempty(scenario), scenario = 'Normal'; end

    ACCENT = [0.20 0.62 0.88];
    title  = scenarioTitle(scenario);

    % ---- RE-INSTRUMENT every run (defends against Simulink resets) ------
    autoInstrumentModel(model);

    % ---- UI: busy -------------------------------------------------------
    set(H.status, 'String', sprintf('Running simulation for  "%s" ...', title), ...
        'ForegroundColor', [0.95 0.72 0.18]);
    set(H.Action, 'String', 'RUNNING', 'BackgroundColor', [0.50 0.35 0.08]);
    set(H.r87T, 'String', 'Simulating…'); set(H.Feat, 'String', 'Extracting…');
    set(H.Trip, 'String', 'Awaiting…'); set(H.Idiff, 'String', char(8212));
    set(H.Lat,  'String', char(8212));
    drawnow;

    set_param(model, 'SignalLogging', 'on');
    set_param(model, 'SignalLoggingName', 'logsout');

    try
        stopT  = get_param(model, 'StopTime');
        simOut = sim(model, 'StopTime', stopT, 'ReturnWorkspaceOutputs', 'on');

        [time, idiff, nPhases, isUncomp] = extractRealDiffCurrent(simOut);
        [tripped, tripTime]              = extractTripDecision(simOut);

        peakIdiff = 0;
        if ~isempty(idiff) && ~isempty(time), peakIdiff = max(abs(idiff(:))); end

        faultInception = 0.05; latencyMs = NaN;
        if ~isempty(tripped) && tripped && ~isnan(tripTime) && tripTime > faultInception
            latencyMs = (tripTime - faultInception) * 1000;
        end

        [res87T, color87T] = interpret87TLogic(scenario, tripped, peakIdiff);
        featStr            = buildFeatureString(time, idiff, scenario);

        if isempty(tripped)
            actionStr = 'UNKNOWN'; actionColor = [0.45 0.45 0.45];
            tripDispStr = 'UNKNOWN (Signal missing)';
        elseif tripped
            actionStr = 'TRIP';    actionColor = [0.75 0.14 0.12];
            tripDispStr = 'TRIP (from true relay output)';
        else
            actionStr = 'BLOCK';   actionColor = [0.10 0.52 0.28];
            tripDispStr = 'BLOCK (from true relay output)';
        end

        if isUncomp
            set(H.TtlIdiff, 'String', 'Idiff (UNCOMPENSATED):');
            idiffStr = sprintf('%.4f A  (WARNING: External raw calc)', peakIdiff);
            idiffCol = [0.90 0.45 0.15];
        else
            set(H.TtlIdiff, 'String', 'Peak I_{diff} (p.u.):');
            if peakIdiff > 0
                idiffStr = sprintf('%.4f  (Relay internal signal)', peakIdiff);
            else
                idiffStr = 'No I_diff signal logged';
            end
            idiffCol = ACCENT;
        end

        updateWaveformPlot(H.ax, time, idiff, nPhases, scenario, isUncomp);

        set(H.status, 'String', sprintf('Analysis complete  |  Scenario: %s  |  Result: %s', ...
            title, actionStr), 'ForegroundColor', [0.25 0.85 0.45]);
        set(H.r87T,  'String', res87T,    'ForegroundColor', color87T);
        set(H.Feat,  'String', featStr);
        set(H.Trip,  'String', tripDispStr);
        set(H.Idiff, 'String', idiffStr,  'ForegroundColor', idiffCol);

        if ~isnan(latencyMs)
            set(H.Lat, 'String', sprintf('%.1f ms', latencyMs));
        elseif ~isempty(tripped) && tripped
            set(H.Lat, 'String', 'TRIP — inception indeterminate');
        elseif isempty(tripped)
            set(H.Lat, 'String', 'UNKNOWN');
        else
            set(H.Lat, 'String', 'N/A');
        end
        set(H.Action, 'String', actionStr, 'BackgroundColor', actionColor);

        fprintf('>>> %s | %s | Peak Idiff=%.4f\n', upper(scenario), actionStr, peakIdiff);

    catch ME
        set(H.status, 'String', sprintf('Error: %s', ME.message), 'ForegroundColor', [0.90 0.22 0.18]);
        set(H.Action, 'String', 'SYS FAULT', 'BackgroundColor', [0.45 0.10 0.08]);
        disp(['ERROR: ' ME.message]);
    end
end

% =========================================================================
% DATA EXTRACTION
% =========================================================================
function [time, idiff, nPhases, isUncomp] = extractRealDiffCurrent(simOut)
    time = []; idiff = []; nPhases = 3; isUncomp = false;

    try
        logs = simOut.get('logsout');
        el = logs.get('I_diff');
        if ~isempty(el)
            [time, idiff] = unwrapTimeSeries(el.Values);
            if ~isempty(idiff)
                nPhases = size(idiff,2);
                return;
            end
        end
    catch
    end

    try
        rawP = simOut.get('I_primary_abc'); rawS = simOut.get('I_secondary_abc');
        [tP, dP] = unwrapTimeSeries(rawP); [tS, dS] = unwrapTimeSeries(rawS);
        if ~isempty(dP) && ~isempty(dS)
            if ~isequal(tP, tS), dS = interp1(tS, dS, tP, 'linear', 'extrap'); end
            time = tP; idiff = dP - dS; nPhases = min(3, size(idiff, 2)); isUncomp = true;
            return;
        end
    catch
    end
end

function [tripped, tripTime] = extractTripDecision(simOut)
    tripped = []; tripTime = NaN;
    candidates = {'TripSignal','Trip_Signal','relay_trip_signal_out', ...
                  'relay_trip_latch','top_relay_trip_to_breakers'};
    try
        logs = simOut.get('logsout');
        for cn = candidates
            try
                el = logs.get(cn{1});
                if isempty(el), continue; end
                [t, v] = unwrapTimeSeries(el.Values);
                if isempty(v), continue; end
                idx = find(v(:,1) > 0.5, 1, 'first');
                if ~isempty(idx)
                    tripped = true; tripTime = t(min(idx, numel(t)));
                else
                    tripped = false;
                end
                return;
            catch
            end
        end
    catch
    end

    for cn = candidates
        try
            raw = simOut.get(cn{1});
            [t, v] = unwrapTimeSeries(raw);
            if isempty(v), continue; end
            idx = find(v(:,1) > 0.5, 1, 'first');
            if ~isempty(idx)
                tripped = true; tripTime = t(min(idx, numel(t)));
            else
                tripped = false;
            end
            return;
        catch
        end
    end
end

% =========================================================================
% UTILS
% =========================================================================
function [t, d] = unwrapTimeSeries(raw)
    t = []; d = []; if isempty(raw), return; end
    if isa(raw, 'timeseries'), t = raw.Time; d = raw.Data;
    elseif isa(raw, 'Simulink.SimulationData.Signal'), t = raw.Values.Time; d = raw.Values.Data;
    elseif isstruct(raw) && isfield(raw, 'time'), t = raw.time; d = raw.signals.values;
    elseif isnumeric(raw), d = raw; t = (0:size(raw,1)-1)' * 6.25e-4;
    else
        try t = raw.Time; d = raw.Data; catch, end
    end
    if ndims(d) == 3, d = squeeze(d); end
    if ~isempty(t) && ~isempty(d)
        if size(d, 1) ~= length(t) && size(d, 2) == length(t)
            d = d';
        end
    end
end

function [res87T, color] = interpret87TLogic(scenario, tripped, peakIdiff)
    if isempty(tripped), res87T = 'UNKNOWN'; color = [0.6 0.65 0.7]; return; end
    isInternal = startsWith(scenario, 'Internal');
    if tripped && isInternal, res87T = sprintf('TRIP (Peak=%.3f)', peakIdiff); color = [0.9 0.4 0.2];
    elseif ~tripped && ~isInternal, res87T = sprintf('BLOCK (Peak=%.4f)', peakIdiff); color = [0.6 0.65 0.7];
    elseif tripped, res87T = sprintf('TRIP (MALOPERATION) (Peak=%.3f)', peakIdiff); color = [0.9 0.22 0.18];
    else, res87T = sprintf('BLOCK (MISSED TRIP) (Peak=%.3f)', peakIdiff); color = [0.9 0.22 0.18];
    end
end

function s = buildFeatureString(time, idiff, scenario)
    if isempty(idiff) || isempty(time), s = 'No data'; return; end
    flat = idiff(:);
    peakVal = max(abs(flat));
    rmsVal  = sqrt(mean(flat.^2));
    dur_ms  = (time(end)-time(1))*1e3;

    harmRatio = computeSecondHarmonicRatio(time, idiff(:,1));

    if ~isnan(harmRatio)
        s = sprintf('Peak: %.3f | RMS: %.3f | 2nd Harm: %.1f%% | Dur: %.1f ms', peakVal, rmsVal, harmRatio*100, dur_ms);
    else
        s = sprintf('Peak: %.3f | RMS: %.3f | Dur: %.1f ms', peakVal, rmsVal, dur_ms);
    end
end

function ratio = computeSecondHarmonicRatio(time, sig)
    ratio = NaN;
    try
        if numel(time) < 64, return; end
        fs = 1 / mean(diff(time)); N = numel(sig); Y = fft(sig); freqs = (0:N-1) * (fs/N);
        [~, i1] = min(abs(freqs - 50)); [~, i2] = min(abs(freqs - 100));
        mag1 = abs(Y(i1)); mag2 = abs(Y(i2));
        if mag1 > 0, ratio = mag2 / mag1; end
    catch
    end
end

function t = scenarioTitle(scenario)
    map = containers.Map( ...
        {'Normal', 'Inrush', 'InternalAG', 'InternalBG', 'InternalAB', 'InternalABC', 'External', 'ExternalAB'}, ...
        {'Normal Load Condition', 'Magnetizing Inrush', 'Internal Fault — Phase A-G', ...
         'Internal Fault — Phase B-G', 'Internal Fault — Phase A-B', 'Internal Fault — 3-Phase', ...
         'External Through-Fault — 3-Phase', 'External Through-Fault — Phase A-B'});
    if isKey(map, scenario)
        t = map(scenario);
    else
        t = scenario;
    end
end

function updateWaveformPlot(ax, time, idiff, nPhases, scenario, isUncomp)
    cla(ax); hold(ax, 'on');
    if isempty(time) || isempty(idiff), hold(ax, 'off'); return; end
    phColors = [0.18 0.82 0.84; 0.98 0.72 0.18; 0.90 0.32 0.72];
    for k = 1:min(nPhases, size(idiff, 2)), plot(ax, time*1e3, idiff(:,k), 'Color', phColors(k,:), 'LineWidth', 1.5); end

    if ~ismember(scenario, {'Normal', 'Inrush'})
        xline(ax, 50, '--', 'Color', [1 0.38 0.28], 'LineWidth', 1.2, 'Label', 'Fault Inception (50 ms)', ...
              'LabelVerticalAlignment', 'bottom', 'FontSize', 9, 'FontAngle', 'italic', 'HandleVisibility', 'off');
    end
    hold(ax, 'off');

    titleStr = scenarioTitle(scenario);
    if isUncomp
        titleStr = [titleStr '  —  [UNCOMPENSATED EXTERNAL I_{diff}]'];
        tColor = [0.90 0.45 0.15];
    else
        titleStr = [titleStr '  —  [Internal Relay I_{diff}]'];
        tColor = [0.95 0.95 0.95];
    end

    title(ax, titleStr, 'Color', tColor, 'FontSize', 10.5, 'FontWeight', 'normal');
    xlabel(ax, 'Time  (ms)', 'Color', [0.75 0.78 0.82], 'FontSize', 10);
    ylabel(ax, 'I_{diff}', 'Color', [0.75 0.78 0.82], 'FontSize', 10);

    grid(ax,'on');
    ax.GridColor = [0.35 0.38 0.42]; ax.GridAlpha = 0.40;
    ax.XLim = [0, max(time)*1e3];
    ax.TickDir = 'out'; ax.XMinorTick = 'on'; ax.YMinorTick = 'on';
    ax.FontSize = 9.5; ax.XColor = [0.75 0.78 0.82]; ax.YColor = [0.75 0.78 0.82];
end

function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10'); set_param([model '/Step4'], 'Time', '10');
    set_param([model '/Internal_Fault'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
    set_param([model '/External_Fault'], 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
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
        residualFlux = (rand(1,3)*2 - 1) * 0.80;
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

% =========================================================================
% BATCH DATASET GENERATOR
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

    dataset.zone             = cell(nSamples, 1);
    dataset.faultType        = cell(nSamples, 1);
    dataset.faultResistance  = zeros(nSamples, 1);
    dataset.inceptionAngle   = zeros(nSamples, 1);
    dataset.inceptionTime    = zeros(nSamples, 1);
    dataset.shouldTrip       = false(nSamples, 1);
    dataset.primaryCurrent   = cell(nSamples, 1);
    dataset.secondaryCurrent = cell(nSamples, 1);
    dataset.diffCurrent      = cell(nSamples, 1);
    dataset.tripSignal       = cell(nSamples, 1);
    dataset.simulationStatus = cell(nSamples, 1);
    dataset.noiseLevel       = zeros(nSamples, 1);
    dataset.ctMismatch       = cell(nSamples, 1);

    hWait = waitbar(0, 'Initialising…', 'Name', 'Batch Generation Progress');

    try
        for i = 1:nSamples
            if mod(i, 10) == 0
                waitbar(i/nSamples, hWait, sprintf('Generating sample %d/%d…', i, nSamples));
            end

            scenarioRand = rand();
            if scenarioRand < 0.15
                dataset.zone{i} = 'Normal'; dataset.faultType{i} = 'None';
                dataset.faultResistance(i) = 0; dataset.inceptionAngle(i) = 0;
                dataset.inceptionTime(i) = 0; dataset.shouldTrip(i) = false;
                configureNormalScenario(model);
            elseif scenarioRand < 0.30
                dataset.zone{i} = 'Inrush'; dataset.faultType{i} = 'Inrush';
                dataset.faultResistance(i) = 0; dataset.inceptionAngle(i) = randi([0, 360]);
                dataset.inceptionTime(i) = 0.05; dataset.shouldTrip(i) = false;
                configureInrushScenario(model);
            elseif scenarioRand < 0.75
                dataset.zone{i} = 'Internal'; [fType, Rf] = generateRandomFault();
                dataset.faultType{i} = fType; dataset.faultResistance(i) = Rf;
                angle = randi([0, 360]); dataset.inceptionAngle(i) = angle;
                faultTime = angleToTime(angle); dataset.inceptionTime(i) = faultTime;
                dataset.shouldTrip(i) = true;
                configureInternalFault(model, fType, Rf, faultTime);
            else
                dataset.zone{i} = 'External'; [fType, Rf] = generateRandomFault();
                dataset.faultType{i} = fType; dataset.faultResistance(i) = Rf;
                angle = randi([0, 360]); dataset.inceptionAngle(i) = angle;
                faultTime = angleToTime(angle); dataset.inceptionTime(i) = faultTime;
                dataset.shouldTrip(i) = false;
                configureExternalFault(model, fType, Rf, faultTime);
            end

            global_noise_level = 0.01 + (0.06 * rand());
            ct_mismatches      = 0.98 + (0.04 * rand(6, 1));
            dataset.noiseLevel(i) = global_noise_level;
            dataset.ctMismatch{i} = ct_mismatches;

            try
                for ch = 1:6
                    set_param(sprintf('%s/Noise Merging Unit/CT_Gain_Mismatch_%d', model, ch), 'Gain', num2str(ct_mismatches(ch)));
                    set_param(sprintf('%s/Noise Merging Unit/Noise_Gain_%d', model, ch), 'Gain', num2str(global_noise_level));
                end
            catch
                if i == 1, disp('  Warning: Noise Merging Unit not found — continuing without noise injection'); end
            end

            try
                simOut = sim(model, 'StopTime', '1.0');

                try dataset.primaryCurrent{i}   = simOut.get('I_primary_abc');  catch, try dataset.primaryCurrent{i}   = simOut.I_primary_abc;  catch, dataset.primaryCurrent{i}   = []; end; end
                try dataset.secondaryCurrent{i} = simOut.get('I_secondary_abc'); catch, try dataset.secondaryCurrent{i} = simOut.I_secondary_abc; catch, dataset.secondaryCurrent{i} = []; end; end
                try dataset.diffCurrent{i}      = simOut.get('I_diff');          catch, try dataset.diffCurrent{i}      = simOut.I_diff;          catch, dataset.diffCurrent{i}      = []; end; end
                try dataset.tripSignal{i}       = simOut.get('TripSignal');      catch, try dataset.tripSignal{i}       = simOut.TripSignal;      catch, dataset.tripSignal{i}       = []; end; end

                dataset.simulationStatus{i} = 'Success';
            catch ME
                fprintf('  Sample %d failed: %s\n', i, ME.message);
                dataset.simulationStatus{i}  = sprintf('Failed: %s', ME.message);
                dataset.primaryCurrent{i} = []; dataset.secondaryCurrent{i} = [];
                dataset.diffCurrent{i} = []; dataset.tripSignal{i} = [];
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
        fprintf('Generated: %d samples  (%d successful, %.1f%%)\n', nSamples, successCount, successRate);
        fprintf('Saved to : %s\n', filename);

        msgbox(sprintf('Generated %d samples (%.1f%% success).\n\nSaved to: %s', nSamples, successRate, filename), 'Batch Complete', 'help');
    catch ME
        if isvalid(hWait), close(hWait); end
        errordlg(['Batch generation error: ' ME.message], 'Error');
        rethrow(ME);
    end
end

function [faultType, Rf] = generateRandomFault()
    faultTypes = {'AG','BG','CG','AB','BC','CA','ABC','ABG','BCG','CAG'};
    faultType  = faultTypes{randi(length(faultTypes))};
    Rf = 10^(rand() * (log10(20) - log10(0.01)) + log10(0.01));
end

function configureNormalScenario(model)
    resetFaultBlocks(model);
    setBreakersClosed(model);
end

function configureInrushScenario(model)
    resetFaultBlocks(model);
    setInrushEnergization(model);
end

function configureInternalFault(model, faultType, Rf, faultTime)
    resetFaultBlocks(model);
    setBreakersClosed(model);
    set_param([model '/Step3'], 'Time', num2str(faultTime));
    [fA, fB, fC, fG] = decodeFaultType(faultType);
    set_param([model '/Internal_Fault'], 'FaultA', fA, 'FaultB', fB, 'FaultC', fC, 'GroundFault', fG);
    try set_param([model '/Internal_Fault'], 'FaultResistance', num2str(Rf)); catch; end
end

function configureExternalFault(model, faultType, Rf, faultTime)
    resetFaultBlocks(model);
    setBreakersClosed(model);
    set_param([model '/Step4'], 'Time', num2str(faultTime));
    [fA, fB, fC, fG] = decodeFaultType(faultType);
    try
        set_param([model '/External_Fault'], 'FaultA', fA, 'FaultB', fB, 'FaultC', fC, 'GroundFault', fG);
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
    faultTime = 0.5 + (angle / 360) * (1/50);
end
