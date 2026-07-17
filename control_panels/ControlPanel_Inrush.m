function ControlPanel_Inrush
% =========================================================================
% TRANSFORMER PROTECTION — INRUSH DATASET GENERATOR
% =========================================================================
%
% PURPOSE
%   Dedicated control panel for generating TRUE magnetizing inrush current
%   data.  Uses Step1 / Step2 blocks connected to the circuit-breaker
%   command (com) ports to simulate open → close energisation.
%
% HARDWARE ASSUMPTION (CRITICAL)
%   Step1 → Primary-side breaker com port
%   Step2 → Secondary-side breaker com port
%   Both steps: Initial value = 0 (breaker open at t = 0)
%               Final value   = 1 (close command)
%               Step time     = t_energise  (varies per sample)
%
%   The transformer starts de-energised.  When Step1 fires, the primary
%   winding is connected to the network → flux builds from residual →
%   magnetising inrush current appears on the primary side.
%
% INRUSH PHYSICS
%   Severity depends on the voltage angle at the instant of closure:
%     θ = 0° / 180°  (zero crossing)  →  maximum DC offset, worst inrush
%     θ = 90° / 270° (voltage peak)   →  minimum inrush, near steady-state
%   The batch generator sweeps t_energise across 0–20 ms (one full cycle)
%   to produce all severity levels.
%
% OUTPUT FORMAT
%   Compatible with FeatureExtractor.m v2.
%   Filename: InrushDataset_YYYYMMDD_HHMMSS.mat
%   Label:    zone = 'Inrush',  shouldTrip = false
%             (inrush must NOT trip the 87T relay — this is the classical
%              security problem the 2nd-harmonic restraint solves)
%
% USAGE
%   1. Open your Simulink model.
%   2. Run: ControlPanel_Inrush
%   3. Click scenario buttons to test individual cases.
%   4. Use the Batch Generator panel to produce the full dataset.
%
% =========================================================================

    modelName = gcs;
    if isempty(modelName)
        errordlg('Please open your Simulink model first!'); return;
    end
    modelName = bdroot(modelName);

    % ── Colours ──────────────────────────────────────────────────────────
    bgColor     = [0.94 0.96 0.99];
    panelColor  = [1.00 1.00 1.00];
    cInrush     = [1.00 0.87 0.60];
    cInrushDark = [0.98 0.80 0.40];
    cRun        = [0.85 0.92 1.00];
    cBatch      = [0.95 0.85 1.00];
    cTextInrush = [0.55 0.35 0.00];
    cTextBatch  = [0.40 0.10 0.50];

    % ── Figure ───────────────────────────────────────────────────────────
    f = figure('Name', 'Inrush Dataset Generator', 'NumberTitle', 'off', ...
               'Position', [300, 80, 420, 720], 'MenuBar', 'none', ...
               'Resize', 'off', 'Color', bgColor);

    % ── Title ────────────────────────────────────────────────────────────
    uicontrol('Parent', f, 'Style', 'text', ...
              'Position', [20, 675, 380, 35], ...
              'String', 'MAGNETIZING INRUSH GENERATOR', ...
              'FontSize', 13, 'FontWeight', 'bold', ...
              'ForegroundColor', [0.50 0.30 0.00], ...
              'BackgroundColor', bgColor, ...
              'HorizontalAlignment', 'center');

    uicontrol('Parent', f, 'Style', 'text', ...
              'Position', [20, 655, 380, 20], ...
              'String', ['Model: ' modelName], ...
              'FontSize', 8, 'FontAngle', 'italic', ...
              'ForegroundColor', [0.45 0.45 0.45], ...
              'BackgroundColor', bgColor, ...
              'HorizontalAlignment', 'center');

    % ── Physics note ─────────────────────────────────────────────────────
    uicontrol('Parent', f, 'Style', 'text', ...
              'Position', [20, 615, 380, 38], ...
              'String', ['Step1 → Primary breaker  |  Step2 → Secondary breaker' newline ...
                         'Breakers start OPEN (Step=0).  Closure at t_energise triggers inrush.'], ...
              'FontSize', 8, 'FontAngle', 'italic', ...
              'ForegroundColor', [0.30 0.30 0.30], ...
              'BackgroundColor', [0.98 0.96 0.90], ...
              'HorizontalAlignment', 'center');

    % =========================================================
    % MANUAL SCENARIO PANEL
    % =========================================================
    pManual = uipanel('Parent', f, 'Title', 'Manual Test Scenarios', ...
                      'FontSize', 11, 'FontWeight', 'bold', ...
                      'ForegroundColor', cTextInrush, ...
                      'BackgroundColor', panelColor, ...
                      'Position', [0.05 0.46 0.90 0.56]);

    btnX = 35; width = 320; height = 40; gap = 50; fontSize = 10;

    % ── Energisation time input ───────────────────────────────────────────
    uicontrol('Parent', pManual, 'Style', 'text', ...
              'Position', [35, 310, 180, 20], ...
              'String', 'Custom t_energise (s):', ...
              'FontSize', 9, 'HorizontalAlignment', 'left', ...
              'BackgroundColor', panelColor);

    hEnergiseTime = uicontrol('Parent', pManual, 'Style', 'edit', ...
                              'Position', [220, 310, 80, 24], ...
                              'String', '0.50', ...
                              'FontSize', 10, 'BackgroundColor', [1 1 1]);

    uicontrol('Parent', pManual, 'Style', 'text', ...
              'Position', [35, 287, 320, 16], ...
              'String', '(Step1 & Step2 will close at this time)', ...
              'FontSize', 8, 'FontAngle', 'italic', ...
              'ForegroundColor', [0.4 0.4 0.4], ...
              'BackgroundColor', panelColor);

    % ── Button: Severe Inrush (0° — zero crossing, worst case) ───────────
    uicontrol('Parent', pManual, 'Style', 'pushbutton', ...
              'Position', [btnX, 240, width, height], ...
              'String', 'SEVERE INRUSH  (0° — voltage zero crossing)', ...
              'BackgroundColor', cInrushDark, 'ForegroundColor', cTextInrush, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Close at voltage zero crossing → maximum DC offset, worst inrush', ...
              'Callback', @(s,e) setInrushManual(modelName, 0.500, 'noload'));
              % 0.500 s → 50Hz cycle = 20ms → angle = mod(0.500, 0.020)/0.020*360 = 0°

    % ── Button: Moderate Inrush (45°) ────────────────────────────────────
    uicontrol('Parent', pManual, 'Style', 'pushbutton', ...
              'Position', [btnX, 240 - gap, width, height], ...
              'String', 'MODERATE INRUSH  (45° — leading quarter)', ...
              'BackgroundColor', cInrush, 'ForegroundColor', cTextInrush, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Close at 45° into cycle → moderate inrush', ...
              'Callback', @(s,e) setInrushManual(modelName, 0.5025, 'noload'));
              % 0.5025 s → angle = 0.0025/0.020*360 = 45°

    % ── Button: Mild Inrush (90° — voltage peak, best case) ───────────────
    uicontrol('Parent', pManual, 'Style', 'pushbutton', ...
              'Position', [btnX, 240 - 2*gap, width, height], ...
              'String', 'MILD INRUSH  (90° — voltage peak)', ...
              'BackgroundColor', [1.00 0.96 0.80], 'ForegroundColor', cTextInrush, ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Close at voltage peak → minimum inrush (near normal energisation)', ...
              'Callback', @(s,e) setInrushManual(modelName, 0.505, 'noload'));
              % 0.505 s → angle = 0.005/0.020*360 = 90°

    % ── Button: Loaded Energisation (primary + secondary close together) ──
    uicontrol('Parent', pManual, 'Style', 'pushbutton', ...
              'Position', [btnX, 240 - 3*gap, width, height], ...
              'String', 'LOADED ENERGISATION  (both breakers close)', ...
              'BackgroundColor', [0.88 0.95 1.00], 'ForegroundColor', [0.10 0.30 0.60], ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Primary + secondary close simultaneously — transformer energised with load', ...
              'Callback', @(s,e) setInrushManual(modelName, 0.500, 'loaded'));

    % ── Button: Custom (from edit field) ─────────────────────────────────
    uicontrol('Parent', pManual, 'Style', 'pushbutton', ...
              'Position', [btnX, 240 - 4*gap, width, height], ...
              'String', 'CUSTOM ENERGISATION  (use field above)', ...
              'BackgroundColor', [0.90 0.90 0.90], 'ForegroundColor', [0.20 0.20 0.20], ...
              'FontSize', fontSize, 'FontWeight', 'bold', ...
              'TooltipString', 'Set custom energisation time from the edit field above', ...
              'Callback', @(s,e) setInrushCustom(modelName, hEnergiseTime));

    % ── Run simulation button ──────────────────────────────────────────────
    uicontrol('Parent', pManual, 'Style', 'pushbutton', ...
              'Position', [90, 10, 210, 38], ...
              'String', '▶ RUN SIMULATION', ...
              'FontSize', 11, 'FontWeight', 'bold', ...
              'BackgroundColor', cRun, 'ForegroundColor', [0.10 0.30 0.60], ...
              'Callback', @(s,e) runSingleSim(modelName));

    % =========================================================
    % BATCH GENERATOR PANEL
    % =========================================================
    pBatch = uipanel('Parent', f, 'Title', 'Inrush Batch Generator', ...
                     'FontSize', 11, 'FontWeight', 'bold', ...
                     'ForegroundColor', cTextBatch, ...
                     'BackgroundColor', panelColor, ...
                     'Position', [0.05 0.18 0.90 0.26]);

    uicontrol('Parent', pBatch, 'Style', 'text', ...
              'Position', [20, 100, 200, 20], ...
              'String', 'Number of samples:', ...
              'FontSize', 9, 'HorizontalAlignment', 'left', ...
              'BackgroundColor', panelColor);

    hSampleCount = uicontrol('Parent', pBatch, 'Style', 'edit', ...
                             'Position', [220, 100, 80, 24], ...
                             'String', '500', 'FontSize', 10, ...
                             'BackgroundColor', [1 1 1]);

    % Secondary breaker mode selector
    uicontrol('Parent', pBatch, 'Style', 'text', ...
              'Position', [20, 70, 200, 20], ...
              'String', 'Secondary breaker mode:', ...
              'FontSize', 9, 'HorizontalAlignment', 'left', ...
              'BackgroundColor', panelColor);

    hSecMode = uicontrol('Parent', pBatch, 'Style', 'popupmenu', ...
                         'Position', [220, 70, 150, 24], ...
                         'String', {'No-load (open)','Loaded (closed)','Random mix'}, ...
                         'Value', 3, 'FontSize', 9, ...
                         'BackgroundColor', [1 1 1]);

    uicontrol('Parent', pBatch, 'Style', 'text', ...
              'Position', [20, 40, 360, 20], ...
              'String', 'Angles swept: full 0–360° (uniform t_energise over 35+ cycles)', ...
              'FontSize', 8, 'FontAngle', 'italic', ...
              'ForegroundColor', [0.4 0.4 0.4], ...
              'BackgroundColor', panelColor);

    uicontrol('Parent', pBatch, 'Style', 'pushbutton', ...
              'Position', [60, 8, 280, 30], ...
              'String', '⚡ GENERATE INRUSH BATCH DATASET', ...
              'FontSize', 10, 'FontWeight', 'bold', ...
              'BackgroundColor', cBatch, 'ForegroundColor', cTextBatch, ...
              'TooltipString', 'Generate inrush scenarios across all energisation angles', ...
              'Callback', @(s,e) generateInrushBatch(modelName, hSampleCount, hSecMode));

    % ── Status bar ────────────────────────────────────────────────────────
    uicontrol('Parent', f, 'Style', 'text', ...
              'Position', [20, 20, 380, 60], ...
              'String', ['IMPORTANT: Ensure Step1.Before = 0  and  Step1.After = 1' newline ...
                         '           (breaker open at t=0, closes when step fires).' newline ...
                         '           Step3/Step4 fault blocks will be held at t=10 (inactive).'], ...
              'FontSize', 8, 'ForegroundColor', [0.50 0.10 0.10], ...
              'BackgroundColor', [1.00 0.96 0.96], ...
              'HorizontalAlignment', 'left');
end

% =========================================================================
% MANUAL SCENARIO CONFIGURATION FUNCTIONS
% =========================================================================

function setInrushManual(model, t_energise, secondaryMode)
    %% Configure model for a specific inrush scenario.
    %  t_energise    : time at which Step1 (and optionally Step2) fires (s)
    %  secondaryMode : 'noload'  — secondary breaker stays open
    %                  'loaded'  — secondary breaker closes simultaneously

    resetForInrush(model);

    angle_deg = mod(t_energise, 1/50) / (1/50) * 360;

    disp('═══════════════════════════════════════════════════');
    disp('>>> SCENARIO: MAGNETIZING INRUSH');
    fprintf('    t_energise = %.6f s  (%.1f° into 50 Hz cycle)\n', t_energise, angle_deg);
    fprintf('    Secondary  : %s\n', secondaryMode);
    disp('═══════════════════════════════════════════════════');

    % ── PRIMARY BREAKER: open at t=0, close at t_energise ────────────────
    set_param([model '/Step1'], 'Before', '0', 'After', '1', ...
              'Time', num2str(t_energise, '%.6f'));

    % ── SECONDARY BREAKER: depends on mode ───────────────────────────────
    switch secondaryMode
        case 'noload'
            % Keep secondary open — pure no-load magnetising inrush
            set_param([model '/Step2'], 'Before', '0', 'After', '0', 'Time', '10');
            disp('    Secondary breaker: OPEN (no-load energisation)');

        case 'loaded'
            % Secondary closes at same time → transformer energised with load
            set_param([model '/Step2'], 'Before', '0', 'After', '1', ...
                      'Time', num2str(t_energise, '%.6f'));
            disp('    Secondary breaker: CLOSES WITH PRIMARY (loaded energisation)');

        otherwise
            set_param([model '/Step2'], 'Before', '0', 'After', '0', 'Time', '10');
    end

    if angle_deg < 30 || angle_deg > 330 || (angle_deg > 150 && angle_deg < 210)
        disp('    Severity: HIGH (near zero crossing — maximum DC offset expected)');
    elseif (angle_deg >= 60 && angle_deg <= 120) || (angle_deg >= 240 && angle_deg <= 300)
        disp('    Severity: LOW (near voltage peak — minimal inrush expected)');
    else
        disp('    Severity: MODERATE');
    end

    disp('✓ Configuration complete. Click ▶ RUN SIMULATION.');
end


function setInrushCustom(model, hEnergiseTime)
    t_str = strtrim(get(hEnergiseTime, 'String'));
    t_val = str2double(t_str);
    if isnan(t_val) || t_val <= 0
        errordlg('Please enter a valid positive time in seconds (e.g. 0.50)', ...
                 'Invalid Input');
        return;
    end
    setInrushManual(model, t_val, 'noload');
end


function runSingleSim(model)
    status = get_param(model, 'SimulationStatus');
    if strcmp(status, 'running')
        disp('Simulation already running. Please wait.');
        return;
    end
    disp(' ');
    disp('>>> RUNNING INRUSH SIMULATION...');
    try
        simOut = sim(model, 'StopTime', '1.0');
        disp('✓ Simulation complete.');
    catch ME
        errordlg(['Simulation error: ' ME.message], 'Simulation Error');
        disp(['✗ Error: ' ME.message]);
    end
end

% =========================================================================
% BATCH GENERATION FUNCTION
% =========================================================================

function generateInrushBatch(model, hSampleCount, hSecMode)

    nSamples = round(str2double(get(hSampleCount, 'String')));
    if isnan(nSamples) || nSamples < 1
        errordlg('Enter a valid sample count (e.g. 500).'); return;
    end

    secModeIdx = get(hSecMode, 'Value');
    secModeStr = get(hSecMode, 'String');
    secModeSelected = secModeStr{secModeIdx};

    answer = questdlg( ...
        sprintf(['Generate %d inrush samples?\n\n' ...
                 'Secondary mode: %s\n' ...
                 'Angle sweep: 0–360° (uniform)\n\n' ...
                 'Estimated time: ~%d seconds'], ...
                nSamples, secModeSelected, round(nSamples * 2)), ...
        'Confirm Inrush Batch', 'Generate', 'Cancel', 'Generate');
    if ~strcmp(answer, 'Generate'), return; end

    disp(' ');
    disp('╔═══════════════════════════════════════════════════════════╗');
    disp('║        INRUSH BATCH GENERATION STARTED                    ║');
    disp('╚═══════════════════════════════════════════════════════════╝');
    fprintf('Samples      : %d\n', nSamples);
    fprintf('Secondary    : %s\n', secModeSelected);
    disp(' ');

    % ── Preallocate dataset struct (compatible with FeatureExtractor.m) ──
    dataset                   = struct();
    dataset.metadata          = struct();
    dataset.metadata.nSamples      = nSamples;
    dataset.metadata.generatedDate = datetime('now');
    dataset.metadata.modelName     = model;
    dataset.metadata.generatorType = 'ControlPanel_Inrush';
    dataset.metadata.variabilityConfig = struct( ...
        'scenarioType',      'Inrush ONLY — 100% magnetizing inrush', ...
        'energisationAngle', '0–360° uniform (t_energise uniform over multi-cycle range)', ...
        'secondaryMode',     secModeSelected, ...
        'noiseLevelRange',   '[0.005, 0.12]  uniform random', ...
        'ctMismatchRange',   '[0.95, 1.05]   per-channel uniform random', ...
        'shouldTrip',        'Always FALSE — inrush must NOT trip 87T relay', ...
        'physicsNote',       'Step1(Before=0,After=1) triggers primary breaker closure. Inrush severity determined by voltage angle at t_energise.');

    % Label arrays
    dataset.zone              = cell(nSamples, 1);
    dataset.faultType         = cell(nSamples, 1);
    dataset.faultResistance   = zeros(nSamples, 1);
    dataset.inceptionAngle    = zeros(nSamples, 1);  % voltage angle at closure (°)
    dataset.inceptionTime     = zeros(nSamples, 1);  % t_energise (s)
    dataset.shouldTrip        = false(nSamples, 1);  % ALWAYS false for inrush
    dataset.secondaryMode     = cell(nSamples, 1);   % 'noload' or 'loaded'

    % Waveform arrays (same names as ControlPanel2 for FeatureExtractor compat)
    dataset.primaryCurrent    = cell(nSamples, 1);
    dataset.secondaryCurrent  = cell(nSamples, 1);
    dataset.diffCurrent       = cell(nSamples, 1);
    dataset.restCurrent       = cell(nSamples, 1);
    dataset.tripSignal        = cell(nSamples, 1);
    dataset.simulationStatus  = cell(nSamples, 1);

    % Noise / CT metadata
    dataset.noiseLevel        = zeros(nSamples, 1);
    dataset.ctMismatch        = cell(nSamples, 1);

    % Inrush-specific metadata
    dataset.energisationTime  = zeros(nSamples, 1);  % exact t_energise used
    dataset.inrushSeverity    = cell(nSamples, 1);   % 'High'/'Moderate'/'Low'

    hWait = waitbar(0, 'Initialising...', 'Name', 'Inrush Batch Generation');

    try
        for i = 1:nSamples
            if mod(i, 10) == 0
                waitbar(i/nSamples, hWait, ...
                        sprintf('Sample %d/%d  (%.1f%%)...', i, nSamples, i/nSamples*100));
            end

            % ── 1. CHOOSE ENERGISATION TIME ──────────────────────────────
            % Uniform over [0.10, 0.80] s — spans 35 full 50 Hz cycles.
            % Every voltage angle (0–360°) is equally represented because
            % the fractional part of t/T_cycle is uniformly distributed.
            t_energise = 0.10 + 0.70 * rand();

            % Voltage angle at the instant of closure
            T_cycle    = 1 / 50;   % 50 Hz system
            angle_deg  = mod(t_energise, T_cycle) / T_cycle * 360;

            % Classify severity for metadata
            if angle_deg < 30 || angle_deg > 330 || ...
               (angle_deg > 150 && angle_deg < 210)
                severity = 'High';       % near zero crossing
            elseif (angle_deg >= 60 && angle_deg <= 120) || ...
                   (angle_deg >= 240 && angle_deg <= 300)
                severity = 'Low';        % near voltage peak
            else
                severity = 'Moderate';
            end

            % ── 2. CHOOSE SECONDARY BREAKER MODE ─────────────────────────
            switch secModeIdx
                case 1   % No-load (open)
                    secMode = 'noload';
                case 2   % Loaded (closed)
                    secMode = 'loaded';
                case 3   % Random mix
                    secMode = chooseIfElse(rand() < 0.60, 'noload', 'loaded');
                    % 60% no-load (purer inrush), 40% loaded (realistic)
            end

            % ── 3. STORE LABELS ──────────────────────────────────────────
            dataset.zone{i}             = 'Inrush';
            dataset.faultType{i}        = 'None';
            dataset.faultResistance(i)  = 0;
            dataset.inceptionAngle(i)   = angle_deg;
            dataset.inceptionTime(i)    = t_energise;
            dataset.shouldTrip(i)       = false;
            dataset.secondaryMode{i}    = secMode;
            dataset.energisationTime(i) = t_energise;
            dataset.inrushSeverity{i}   = severity;

            % ── 4. CONFIGURE SIMULINK MODEL ───────────────────────────────
            configureInrushSample(model, t_energise, secMode);

            % ── 5. NOISE & CT MISMATCH ────────────────────────────────────
            global_noise_level  = 0.005 + 0.115 * rand();
            ct_mismatches       = 0.95  + 0.10  * rand(6, 1);

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
                    disp('  ⚠ Noise Merging Unit not found — continuing without noise injection');
                end
            end

            % ── 6. RUN SIMULATION ─────────────────────────────────────────
            try
                simOut = sim(model, 'StopTime', '1.0');

                dataset.primaryCurrent{i}   = safeGet(simOut, 'I_primary_abc');
                dataset.secondaryCurrent{i} = safeGet(simOut, 'I_secondary_abc');
                dataset.diffCurrent{i}      = safeGet(simOut, 'I_diff');
                dataset.restCurrent{i}      = safeGet(simOut, 'I_rest');
                dataset.tripSignal{i}       = safeGet(simOut, 'TripSignal');
                dataset.simulationStatus{i} = 'Success';

            catch ME
                dataset.simulationStatus{i} = sprintf('Failed: %s', ME.message);
                dataset.primaryCurrent{i}   = [];
                dataset.secondaryCurrent{i} = [];
                dataset.diffCurrent{i}      = [];
                dataset.restCurrent{i}      = [];
                dataset.tripSignal{i}       = [];
                fprintf('  ✗ Sample %d failed: %s\n', i, ME.message);
            end

            pause(0.01);
        end

        % ── SAVE ──────────────────────────────────────────────────────────
        timestamp = datestr(now, 'yyyymmdd_HHMMSS');
        filename  = sprintf('InrushDataset_%s.mat', timestamp);
        save(filename, 'dataset', '-v7.3');

        close(hWait);

        % ── SUMMARY ──────────────────────────────────────────────────────
        nSuccess  = sum(strcmp(dataset.simulationStatus, 'Success'));
        nHigh     = sum(strcmp(dataset.inrushSeverity, 'High'));
        nMod      = sum(strcmp(dataset.inrushSeverity, 'Moderate'));
        nLow      = sum(strcmp(dataset.inrushSeverity, 'Low'));
        nNoLoad   = sum(strcmp(dataset.secondaryMode, 'noload'));
        nLoaded   = sum(strcmp(dataset.secondaryMode, 'loaded'));

        disp(' ');
        disp('╔═══════════════════════════════════════════════════════════╗');
        disp('║        INRUSH BATCH GENERATION COMPLETED                  ║');
        disp('╚═══════════════════════════════════════════════════════════╝');
        fprintf('✓ Generated    : %d samples (%d successful, %.1f%%)\n', ...
                nSamples, nSuccess, nSuccess/nSamples*100);
        fprintf('✓ Saved to     : %s\n', filename);
        disp(' ');
        disp('Severity distribution:');
        fprintf('  High     (near zero crossing) : %d samples  (%.1f%%)\n', ...
                nHigh, nHigh/nSamples*100);
        fprintf('  Moderate                      : %d samples  (%.1f%%)\n', ...
                nMod,  nMod/nSamples*100);
        fprintf('  Low      (near voltage peak)  : %d samples  (%.1f%%)\n', ...
                nLow,  nLow/nSamples*100);
        disp(' ');
        disp('Secondary breaker mode:');
        fprintf('  No-load (open)   : %d samples\n', nNoLoad);
        fprintf('  Loaded  (closed) : %d samples\n', nLoaded);
        disp(' ');
        disp('Angle distribution (should be ~uniform 0–360°):');
        edges = 0:45:360;
        counts = histcounts(dataset.inceptionAngle, edges);
        for k = 1:length(counts)
            fprintf('  %3.0f°–%3.0f°  : %d samples\n', edges(k), edges(k+1), counts(k));
        end
        disp(' ');
        disp('Next step:');
        disp('  Run FeatureExtractor.m — it will auto-detect this file');
        disp('  (pattern: InrushDataset_*.mat is NOT auto-detected — rename to');
        disp('   TransformerProtection_Dataset_*.mat or update FeatureExtractor.m)');

        msgbox(sprintf(['Generated %d inrush samples (%.1f%% success).\n\n' ...
                        'Severity: %d High / %d Moderate / %d Low\n' ...
                        'Secondary: %d no-load / %d loaded\n\n' ...
                        'Saved: %s'], ...
               nSamples, nSuccess/nSamples*100, ...
               nHigh, nMod, nLow, nNoLoad, nLoaded, filename), ...
               'Inrush Batch Complete', 'help');

    catch ME
        if isvalid(hWait), close(hWait); end
        errordlg(['Batch error: ' ME.message], 'Error');
        rethrow(ME);
    end
end

% =========================================================================
% HELPER FUNCTIONS
% =========================================================================

function configureInrushSample(model, t_energise, secMode)
    %% Configure the Simulink model for one inrush sample.
    %  Called before sim() inside the batch loop.

    % ── Clear all fault blocks (faults must be inactive during inrush) ────
    resetFaultBlocks(model);

    % ── PRIMARY BREAKER: open at t=0, close at t_energise ─────────────────
    % Step block parameters: Before = initial value, After = final value
    set_param([model '/Step1'], ...
              'Before', '0', ...
              'After',  '1', ...
              'Time',   num2str(t_energise, '%.8f'));

    % Try to set the breaker's InitialState to Open (varies by MATLAB ver.)
    trySetBreakerInitialOpen(model, 'Three-Phase Breaker');

    % ── SECONDARY BREAKER ─────────────────────────────────────────────────
    switch secMode
        case 'noload'
            % Secondary stays open: no load → pure magnetising inrush
            set_param([model '/Step2'], 'Before', '0', 'After', '0', 'Time', '10');
        case 'loaded'
            % Secondary closes simultaneously with primary
            set_param([model '/Step2'], ...
                      'Before', '0', ...
                      'After',  '1', ...
                      'Time',   num2str(t_energise, '%.8f'));
            trySetBreakerInitialOpen(model, 'Three-Phase Breaker1');
    end
end


function trySetBreakerInitialOpen(model, breakerName)
    %% Attempt to set the breaker initial state to Open.
    %  Parameter names vary between SimPowerSystems and Simscape Electrical.
    blk = [model '/' breakerName];

    % Try different parameter names used across MATLAB/Simulink versions
    paramAttempts = {'SwitchStatus', 'InitialState', 'InitialCondition'};
    openValues    = {'Open', '0', '0'};

    for k = 1:length(paramAttempts)
        try
            set_param(blk, paramAttempts{k}, openValues{k});
            return;
        catch
        end
    end
    % If none worked: the Step block starting at 0 still controls the state;
    % this is non-fatal — the breaker will open as soon as the simulation
    % initialises with signal = 0.
end


function resetFaultBlocks(model)
    %% Disable all fault blocks and push their Step times beyond simulation end.
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');

    set_param([model '/Internal_Fault'], ...
              'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    try, set_param([model '/Internal_Fault'], 'FaultResistance', '0.01'); catch, end

    set_param([model '/External_Fault'], ...
              'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    try, set_param([model '/External_Fault'], 'FaultResistance', '0.01'); catch, end
end


function val = safeGet(simOut, varName)
    %% Safely extract a To-Workspace variable from simOut.
    try
        val = simOut.get(varName);
        return;
    catch, end
    try
        val = simOut.(varName);
        return;
    catch, end
    val = [];
end


function result = chooseIfElse(condition, a, b)
    if condition
        result = a;
    else
        result = b;
    end
end
