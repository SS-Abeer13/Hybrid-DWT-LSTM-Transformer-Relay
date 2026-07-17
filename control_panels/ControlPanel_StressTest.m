function ControlPanel_StressTest
% =========================================================================
% TRANSFORMER PROTECTION — COMPREHENSIVE STRESS-TEST DATASET GENERATOR
% =========================================================================
%
% PURPOSE
%   Generates a maximally-diverse dataset covering every fault type,
%   energisation mode, and stress condition required to train and validate
%   the 87T differential relay DWT-LSTM model.
%
% SCENARIO CLASSES
%   Zone        shouldTrip  Fault types / stress modes
%   ----------  ----------  ---------------------------------------------------
%   Normal      false       Healthy steady-state (various load levels)
%   Inrush      false       No-load / loaded energisation via Step1 / Step2
%   Internal    true        AG BG CG  ABG BCG ACG  AB BC AC  ABC  ABCG
%   Internal    true        High-impedance (Rf = 50–300 Ω)
%   Internal    true        Evolving (single → double → triple phase)
%   External    false       AG BG CG  ABG BCG ACG  AB BC AC  ABC  ABCG
%   Stress      true/false  CT-saturation  |  fault-during-inrush
%
% STEP1 / STEP2 BREAKER CONTROL
%   Normal / Fault scenarios:
%     Step1.Before=0  Step1.After=1  Step1.Time=t_close    (primary closes at t_close)
%     Step2.Before=0  Step2.After=1  Step2.Time=t_close    (secondary closes at t_close)
%     Step5.Time=10   (internal fault inactive)
%     Step4.Time=10   (external fault inactive)
%     t_close = 0.05 s (breakers closed well before fault inception)
%   Inrush scenarios:
%     Step1.Before=0  Step1.After=1  Step1.Time=t_energise  (sweeps 0.10–0.80 s)
%     Step2: 'noload'→stays open | 'loaded'→closes with primary
%
% OUTPUT FILE
%   StressTestDataset_YYYYMMDD_HHMMSS.mat  (FeatureExtractor.m v2 compatible)
%   Followed by 3 post-generation diagnostic figures + console report.
%
% USAGE
%   1. Open your Simulink model.
%   2. Run:  ControlPanel_StressTest
%   3. Test individual scenarios with the manual buttons.
%   4. Set sample count and click  ⚡ GENERATE STRESS-TEST DATASET.
%
% =========================================================================

    modelName = gcs;
    if isempty(modelName)
        errordlg('Please open your Simulink model first.','No Model'); return;
    end
    modelName = bdroot(modelName);

    % ── Colour palette ────────────────────────────────────────────────────
    bgColor      = [0.93 0.95 0.98];
    panelColor   = [1.00 1.00 1.00];
    cNormal      = [0.72 0.95 0.72];
    cInrush      = [1.00 0.88 0.55];
    cInternal    = [1.00 0.72 0.72];
    cExternal    = [0.72 0.86 1.00];
    cStress      = [0.90 0.72 1.00];
    cBatch       = [0.95 0.85 1.00];
    cRun         = [0.85 0.93 1.00];
    cTxtNorm     = [0.10 0.48 0.10];
    cTxtInrush   = [0.55 0.35 0.00];
    cTxtInternal = [0.60 0.08 0.08];
    cTxtExternal = [0.08 0.28 0.60];
    cTxtStress   = [0.38 0.08 0.55];
    cTxtBatch    = [0.38 0.08 0.55];

    % ── Figure ────────────────────────────────────────────────────────────
    f = figure('Name','Stress-Test Dataset Generator','NumberTitle','off', ...
               'Position',[200 30 560 970],'MenuBar','none', ...
               'Resize','off','Color',bgColor);

    % ── Title ─────────────────────────────────────────────────────────────
    uicontrol('Parent',f,'Style','text', ...
              'Position',[10 928 540 32], ...
              'String','TRANSFORMER STRESS-TEST GENERATOR', ...
              'FontSize',13,'FontWeight','bold', ...
              'ForegroundColor',[0.18 0.25 0.50], ...
              'BackgroundColor',bgColor,'HorizontalAlignment','center');

    uicontrol('Parent',f,'Style','text', ...
              'Position',[10 908 540 20], ...
              'String',['Model: ' modelName '   |   All fault types  +  Step1/Step2 breaker control'], ...
              'FontSize',8,'FontAngle','italic', ...
              'ForegroundColor',[0.40 0.40 0.40], ...
              'BackgroundColor',bgColor,'HorizontalAlignment','center');

    % =====================================================================
    % PANEL 1 — Normal & Inrush
    % =====================================================================
    pNI = uipanel('Parent',f,'Title','Normal & Inrush Scenarios', ...
                  'FontSize',10,'FontWeight','bold', ...
                  'ForegroundColor',cTxtInrush,'BackgroundColor',panelColor, ...
                  'Position',[0.02 0.82 0.96 0.105]);

    bW = 240; bH = 34; bX1 = 18; bX2 = 278; bFS = 9;

    uicontrol('Parent',pNI,'Style','pushbutton', ...
              'Position',[bX1 22 bW bH],'String','NORMAL OPERATION', ...
              'BackgroundColor',cNormal,'ForegroundColor',cTxtNorm, ...
              'FontSize',bFS,'FontWeight','bold', ...
              'TooltipString','Both breakers closed, no faults', ...
              'Callback',@(s,e) manualNormal(modelName));

    uicontrol('Parent',pNI,'Style','pushbutton', ...
              'Position',[bX2 22 bW bH],'String','INRUSH — No-Load  (0° worst case)', ...
              'BackgroundColor',cInrush,'ForegroundColor',cTxtInrush, ...
              'FontSize',bFS,'FontWeight','bold', ...
              'TooltipString','Primary closes at voltage zero crossing — max DC offset', ...
              'Callback',@(s,e) manualInrush(modelName, 0.500, 'noload'));

    % =====================================================================
    % PANEL 2 — Internal Faults
    % =====================================================================
    pInt = uipanel('Parent',f,'Title','Internal Faults  (shouldTrip = TRUE)', ...
                   'FontSize',10,'FontWeight','bold', ...
                   'ForegroundColor',cTxtInternal,'BackgroundColor',panelColor, ...
                   'Position',[0.02 0.60 0.96 0.215]);

    % Row layout: 3 columns × 4 rows
    intFaults = { ...
        'INT  A–G',       @() manualFault(modelName,'Internal',1,0,0,1,0.1); ...
        'INT  B–G',       @() manualFault(modelName,'Internal',0,1,0,1,0.1); ...
        'INT  C–G',       @() manualFault(modelName,'Internal',0,0,1,1,0.1); ...
        'INT  A–B–G',     @() manualFault(modelName,'Internal',1,1,0,1,0.1); ...
        'INT  B–C–G',     @() manualFault(modelName,'Internal',0,1,1,1,0.1); ...
        'INT  A–C–G',     @() manualFault(modelName,'Internal',1,0,1,1,0.1); ...
        'INT  A–B',       @() manualFault(modelName,'Internal',1,1,0,0,0.1); ...
        'INT  B–C',       @() manualFault(modelName,'Internal',0,1,1,0,0.1); ...
        'INT  A–C',       @() manualFault(modelName,'Internal',1,0,1,0,0.1); ...
        'INT  A–B–C',     @() manualFault(modelName,'Internal',1,1,1,0,0.1); ...
        'INT  A–B–C–G',   @() manualFault(modelName,'Internal',1,1,1,1,0.1); ...
        'INT  A–G  HiZ',  @() manualFault(modelName,'Internal',1,0,0,1,100); ...
    };
    layoutButtons(pInt, intFaults, cInternal, cTxtInternal, bFS, 3, 190, 32, 8, 8);

    % =====================================================================
    % PANEL 3 — External Faults
    % =====================================================================
    pExt = uipanel('Parent',f,'Title','External Faults  (shouldTrip = FALSE)', ...
                   'FontSize',10,'FontWeight','bold', ...
                   'ForegroundColor',cTxtExternal,'BackgroundColor',panelColor, ...
                   'Position',[0.02 0.435 0.96 0.165]);

    extFaults = { ...
        'EXT  A–G',       @() manualFault(modelName,'External',1,0,0,1,0.1); ...
        'EXT  B–G',       @() manualFault(modelName,'External',0,1,0,1,0.1); ...
        'EXT  C–G',       @() manualFault(modelName,'External',0,0,1,1,0.1); ...
        'EXT  A–B–G',     @() manualFault(modelName,'External',1,1,0,1,0.1); ...
        'EXT  B–C–G',     @() manualFault(modelName,'External',0,1,1,1,0.1); ...
        'EXT  A–C–G',     @() manualFault(modelName,'External',1,0,1,1,0.1); ...
        'EXT  A–B',       @() manualFault(modelName,'External',1,1,0,0,0.1); ...
        'EXT  A–B–C',     @() manualFault(modelName,'External',1,1,1,0,0.1); ...
        'EXT  A–B–C–G',   @() manualFault(modelName,'External',1,1,1,1,0.1); ...
    };
    layoutButtons(pExt, extFaults, cExternal, cTxtExternal, bFS, 3, 190, 32, 8, 8);

    % =====================================================================
    % PANEL 4 — Stress Scenarios
    % =====================================================================
    pStr = uipanel('Parent',f,'Title','Stress Scenarios', ...
                   'FontSize',10,'FontWeight','bold', ...
                   'ForegroundColor',cTxtStress,'BackgroundColor',panelColor, ...
                   'Position',[0.02 0.325 0.96 0.108]);

    stressFaults = { ...
        'EVOLVING  A→AB→ABC',       @() manualEvolving(modelName); ...
        'FAULT DURING INRUSH',      @() manualFaultInrush(modelName); ...
        'EXT FAULT DURING INRUSH',  @() manualExtInrush(modelName); ...
        'CT SATURATION STRESS',     @() manualCTSat(modelName); ...
        'HiZ INT  A–G  (100 Ω)',    @() manualFault(modelName,'Internal',1,0,0,1,100); ...
        'HiZ EXT  A–B–C–G (60 Ω)', @() manualFault(modelName,'External',1,1,1,1,60); ...
    };
    layoutButtons(pStr, stressFaults, cStress, cTxtStress, bFS, 3, 160, 34, 8, 10);

    % ── Run single simulation ─────────────────────────────────────────────
    uicontrol('Parent',f,'Style','pushbutton', ...
              'Position',[160 306 240 26], ...
              'String','▶ RUN SINGLE SIMULATION', ...
              'FontSize',9,'FontWeight','bold', ...
              'BackgroundColor',cRun,'ForegroundColor',[0.08 0.28 0.60], ...
              'Callback',@(s,e) runSingleSim(modelName));

    % =====================================================================
    % PANEL 5 — Batch Generator
    % =====================================================================
    pBatch = uipanel('Parent',f,'Title','Stress-Test Batch Generator', ...
                     'FontSize',10,'FontWeight','bold', ...
                     'ForegroundColor',cTxtBatch,'BackgroundColor',panelColor, ...
                     'Position',[0.02 0.04 0.96 0.27]);

    % Sample count
    uicontrol('Parent',pBatch,'Style','text', ...
              'Position',[18 188 180 18],'String','Total samples:', ...
              'FontSize',9,'HorizontalAlignment','left','BackgroundColor',panelColor);
    hNSamples = uicontrol('Parent',pBatch,'Style','edit', ...
                          'Position',[200 186 80 22],'String','1000', ...
                          'FontSize',10,'BackgroundColor',[1 1 1]);

    % Stop-time
    uicontrol('Parent',pBatch,'Style','text', ...
              'Position',[18 160 180 18],'String','Sim stop time (s):', ...
              'FontSize',9,'HorizontalAlignment','left','BackgroundColor',panelColor);
    hStopTime = uicontrol('Parent',pBatch,'Style','edit', ...
                          'Position',[200 158 80 22],'String','1.0', ...
                          'FontSize',10,'BackgroundColor',[1 1 1]);

    % Save visualisation checkbox
    hSaveViz = uicontrol('Parent',pBatch,'Style','checkbox', ...
                         'Position',[18 132 300 20], ...
                         'String','Save diagnostic figures as PNG after generation', ...
                         'FontSize',9,'Value',1,'BackgroundColor',panelColor);

    % Scenario allocation display (read-only)
    uicontrol('Parent',pBatch,'Style','text', ...
              'Position',[18 78 510 52], ...
              'String',['Scenario allocation (weighted):' newline ...
                        '  Normal 10% | Inrush 10% | Internal LowZ (11 types) ~38% |' newline ...
                        '  Internal HiZ (11 types) ~18% | Evolving 4% | Ext LowZ (9) ~21%' newline ...
                        '  Ext HiZ AG/ABG/ABCG 6% | FaultInInrush 3% | ExtInInrush 2% | CTSat 3%'], ...
              'FontSize',8,'ForegroundColor',[0.35 0.35 0.35], ...
              'BackgroundColor',[0.97 0.97 1.00],'HorizontalAlignment','left');

    uicontrol('Parent',pBatch,'Style','pushbutton', ...
              'Position',[80 10 380 50], ...
              'String','⚡  GENERATE STRESS-TEST DATASET', ...
              'FontSize',11,'FontWeight','bold', ...
              'BackgroundColor',cBatch,'ForegroundColor',cTxtBatch, ...
              'TooltipString','Generate full stress-test batch, save .mat, show diagnostic figures', ...
              'Callback',@(s,e) generateStressBatch(modelName, hNSamples, hStopTime, hSaveViz));
end

% =========================================================================
% HELPER: Build a button grid inside a panel
% =========================================================================
function layoutButtons(parent, items, bgCol, fgCol, fs, nCols, bW, bH, xPad, yPad)
    n     = size(items,1);
    nRows = ceil(n / nCols);
    pPos  = get(parent,'Position');
    % convert normalised position to pixel height
    figH  = 970;
    panH  = pPos(4) * figH;

    for k = 1:n
        row = floor((k-1)/nCols);
        col = mod( (k-1), nCols);
        x   = xPad + col*(bW + xPad);
        y   = panH - 44 - row*(bH + yPad);
        uicontrol('Parent',parent,'Style','pushbutton', ...
                  'Position',[x y bW bH], ...
                  'String', items{k,1}, ...
                  'BackgroundColor',bgCol,'ForegroundColor',fgCol, ...
                  'FontSize',fs,'FontWeight','bold', ...
                  'Callback', items{k,2});
    end
end

% =========================================================================
% MANUAL SCENARIO CALLBACKS
% =========================================================================
function manualNormal(model)
    configureBreakersClosed(model, 0.05);
    resetFaultBlocks(model);
    fprintf('\n▶ NORMAL OPERATION  (both breakers closed at t=0.05 s)\n');
    fprintf('  shouldTrip = false\n');
end

function manualInrush(model, t_energise, secMode)
    configureInrushSample(model, t_energise, secMode);
    angle_deg = mod(t_energise, 1/50) / (1/50) * 360;
    fprintf('\n▶ INRUSH  t_energise=%.4f s  angle=%.1f°  secondary=%s\n', ...
            t_energise, angle_deg, secMode);
    fprintf('  shouldTrip = false\n');
end

function manualFault(model, zone, fA, fB, fC, fG, Rf)
    configureBreakersClosed(model, 0.05);
    resetFaultBlocks(model);
    t_fault = 0.40 + 0.20*rand();
    % Internal_Fault1 is the actual block name in this model
    if strcmp(zone,'Internal')
        blockName = 'Internal_Fault1';
        set_param([model '/Step5'], 'Time', num2str(t_fault,'%.6f'));
    else
        blockName = [zone '_Fault'];
        set_param([model '/Step4'], 'Time', num2str(t_fault,'%.6f'));
    end
    applyFaultConfig(model, blockName, fA, fB, fC, fG, Rf);
    tag = buildFaultTag(fA, fB, fC, fG);
    fprintf('\n▶ %s FAULT  %s  Rf=%.2f Ω  t_fault=%.4f s\n', ...
            upper(zone), tag, Rf, t_fault);
    fprintf('  shouldTrip = %s\n', ifelse(strcmp(zone,'Internal'),'true','false'));
end

function manualEvolving(model)
    configureBreakersClosed(model, 0.05);
    resetFaultBlocks(model);
    t_fault = 0.40;
    set_param([model '/Step5'], 'Time', num2str(t_fault,'%.6f'));
    applyFaultConfig(model, 'Internal_Fault1', 1, 0, 0, 1, 0.1);
    fprintf('\n▶ EVOLVING FAULT  Phase A-G at t=%.2f s\n', t_fault);
    fprintf('  (In batch mode this evolves to multi-phase via Rf sweep)\n');
    fprintf('  shouldTrip = true\n');
end

function manualFaultInrush(model)
    t_energise = 0.500;
    configureInrushSample(model, t_energise, 'noload');
    t_fault = t_energise + 0.05 + 0.05*rand();
    set_param([model '/Step5'], 'Time', num2str(t_fault,'%.6f'));
    applyFaultConfig(model, 'Internal_Fault1', 1, 1, 0, 1, 0.5);
    fprintf('\n▶ FAULT DURING INRUSH  t_energise=%.4f s  t_fault=%.4f s\n', ...
            t_energise, t_fault);
    fprintf('  shouldTrip = true  (fault occurs after inrush)\n');
end

function manualExtInrush(model)
    t_energise = 0.500;
    configureInrushSample(model, t_energise, 'noload');
    t_fault = t_energise + 0.05 + 0.05*rand();
    set_param([model '/Step4'], 'Time', num2str(t_fault,'%.6f'));
    applyFaultConfig(model, 'External_Fault', 1, 0, 0, 1, 1.0);
    fprintf('\n▶ EXTERNAL FAULT DURING INRUSH  t_energise=%.4f s  t_fault=%.4f s\n', ...
            t_energise, t_fault);
    fprintf('  shouldTrip = false  (external fault — relay must restrain)\n');
end

function manualCTSat(model)
    configureBreakersClosed(model, 0.05);
    resetFaultBlocks(model);
    t_fault = 0.40 + 0.10*rand();
    set_param([model '/Step5'], 'Time', num2str(t_fault,'%.6f'));
    applyFaultConfig(model, 'Internal_Fault1', 1, 0, 0, 1, 0.05);
    fprintf('\n▶ CT SATURATION STRESS  high noise + large CT mismatch\n');
    fprintf('  Rf=0.05 Ω  t_fault=%.4f s  shouldTrip = true\n', t_fault);
end

function runSingleSim(model)
    status = get_param(model,'SimulationStatus');
    if strcmp(status,'running'), disp('Simulation already running.'); return; end
    fprintf('\n>>> Running simulation...\n');
    try
        sim(model,'StopTime','1.0');
        fprintf('✓ Simulation complete.\n');
    catch ME
        errordlg(['Simulation error: ' ME.message],'Simulation Error');
    end
end

% =========================================================================
% BATCH GENERATION
% =========================================================================
function generateStressBatch(model, hN, hT, hSaveViz)

    nSamples = round(str2double(get(hN,'String')));
    stopTime = strtrim(get(hT,'String'));
    saveViz  = get(hSaveViz,'Value');

    if isnan(nSamples) || nSamples < 1
        errordlg('Enter a valid sample count (e.g. 1000).'); return;
    end
    if isnan(str2double(stopTime))
        errordlg('Enter a valid stop time (e.g. 1.0).'); return;
    end

    % ── Scenario table ────────────────────────────────────────────────────
    % Fields: name | zone | block | fA fB fC fG | Rf_lo Rf_hi | shouldTrip | weight
    ST = buildScenarioTable();

    % Normalise weights → integer counts
    weights   = [ST.weight];
    counts    = max(1, round(nSamples * weights / sum(weights)));
    % Adjust rounding error on first scenario
    counts(1) = counts(1) + (nSamples - sum(counts));

    totalActual = sum(counts);

    ans_dlg = questdlg( ...
        sprintf(['Generate %d stress-test samples?\n\n' ...
                 'Scenarios: %d types\n' ...
                 'Stop time: %s s\n' ...
                 'Estimated time: ~%d min\n\n' ...
                 'Breakdown printed to console after generation.'], ...
                totalActual, numel(ST), stopTime, round(totalActual*1.5/60)), ...
        'Confirm Stress-Test Batch','Generate','Cancel','Generate');
    if ~strcmp(ans_dlg,'Generate'), return; end

    % ── Pre-allocate dataset ───────────────────────────────────────────────
    dataset = preallocateDataset(totalActual, model);

    hWait = waitbar(0,'Initialising...','Name','Stress-Test Batch Generation');

    globalIdx = 0;
    try
        for si = 1:numel(ST)
            sc  = ST(si);
            cnt = counts(si);

            fprintf('\n[%2d/%2d] %-30s  %d samples\n', si, numel(ST), sc.name, cnt);

            for k = 1:cnt
                globalIdx = globalIdx + 1;

                % ── Update progress bar every 5 samples ────────────────────
                if mod(globalIdx,5)==0
                    waitbar(globalIdx/totalActual, hWait, ...
                            sprintf('%s  [%d/%d]', sc.name, globalIdx, totalActual));
                end

                % ── Randomise parameters ───────────────────────────────────
                [t_fault, t_energise, Rf, noiseLevel, ctMismatch, secMode, angle_deg] = ...
                    randomiseParams(sc, k, cnt);

                % ── Configure Simulink model ───────────────────────────────
                configureScenario(model, sc, t_fault, t_energise, Rf, secMode);

                % ── Inject noise / CT mismatch ─────────────────────────────
                injectNoiseCT(model, noiseLevel, ctMismatch);

                % ── Store metadata ─────────────────────────────────────────
                dataset.zone{globalIdx}            = sc.zone;
                dataset.faultType{globalIdx}       = sc.faultTag;
                dataset.faultResistance(globalIdx) = Rf;
                dataset.inceptionAngle(globalIdx)  = angle_deg;
                dataset.inceptionTime(globalIdx)   = t_fault;
                dataset.energisationTime(globalIdx)= t_energise;
                dataset.shouldTrip(globalIdx)      = sc.shouldTrip;
                dataset.scenarioName{globalIdx}    = sc.name;
                dataset.noiseLevel(globalIdx)      = noiseLevel;
                dataset.ctMismatch{globalIdx}      = ctMismatch;
                dataset.secondaryMode{globalIdx}   = secMode;

                % ── Run simulation ─────────────────────────────────────────
                try
                    simOut = sim(model, 'StopTime', stopTime);
                    dataset.primaryCurrent{globalIdx}   = safeGet(simOut,'I_primary_abc');
                    dataset.secondaryCurrent{globalIdx} = safeGet(simOut,'I_secondary_abc');
                    dataset.diffCurrent{globalIdx}      = safeGet(simOut,'I_diff');
                    dataset.restCurrent{globalIdx}      = safeGet(simOut,'I_rest');
                    dataset.tripSignal{globalIdx}       = safeGet(simOut,'TripSignal');
                    dataset.simulationStatus{globalIdx} = 'Success';
                catch ME
                    dataset.simulationStatus{globalIdx} = sprintf('Failed: %s', ME.message);
                    fprintf('  ✗ sample %d failed: %s\n', globalIdx, ME.message);
                end

                pause(0.01);
            end
        end

        % ── Save ──────────────────────────────────────────────────────────
        timestamp = datestr(now,'yyyymmdd_HHMMSS');
        filename  = sprintf('StressTestDataset_%s.mat', timestamp);
        save(filename, 'dataset', '-v7.3');
        close(hWait);

        % ── Console report + figures ──────────────────────────────────────
        printVerificationReport(dataset, totalActual, ST, counts);
        plotDiagnostics(dataset, totalActual, ST, counts, saveViz, timestamp);

        msgbox(sprintf(['Stress-test batch complete.\n\n' ...
                        '%d samples generated.\n' ...
                        'Success rate: %.1f%%\n\n' ...
                        'Saved: %s\n\n' ...
                        'See diagnostic figures and console report.'], ...
               totalActual, ...
               sum(strcmp(dataset.simulationStatus,'Success'))/totalActual*100, ...
               filename), 'Batch Complete', 'help');

    catch ME
        if isvalid(hWait), close(hWait); end
        errordlg(['Batch error: ' ME.message],'Error');
        rethrow(ME);
    end
end

% =========================================================================
% SCENARIO TABLE  — defines every scenario and its sampling weights
% =========================================================================
function ST = buildScenarioTable()
    % Each entry:  name | zone | block | fA fB fC fG | Rf_lo Rf_hi | shouldTrip | weight(%)
    rows = {
    %  name                   zone       block         fA fB fC fG  Rlo    Rhi   trip  wt
      'Normal'               'Normal'   'none'          0  0  0  0   0.00   0.00  false  10
      'Inrush_NoLoad'        'Inrush'   'inrush'        0  0  0  0   0.00   0.00  false   6
      'Inrush_Loaded'        'Inrush'   'inrush_load'   0  0  0  0   0.00   0.00  false   4
      'Internal_AG'          'Internal' 'Internal_Fault1' 1  0  0  1  0.01   2.0   true    5
      'Internal_BG'          'Internal' 'Internal_Fault1' 0  1  0  1  0.01   2.0   true    4
      'Internal_CG'          'Internal' 'Internal_Fault1' 0  0  1  1  0.01   2.0   true    4
      'Internal_ABG'         'Internal' 'Internal_Fault1' 1  1  0  1  0.01   2.0   true    4
      'Internal_BCG'         'Internal' 'Internal_Fault1' 0  1  1  1  0.01   2.0   true    3
      'Internal_ACG'         'Internal' 'Internal_Fault1' 1  0  1  1  0.01   2.0   true    3
      'Internal_AB'          'Internal' 'Internal_Fault1' 1  1  0  0  0.01   2.0   true    2
      'Internal_BC'          'Internal' 'Internal_Fault1' 0  1  1  0  0.01   2.0   true    2
      'Internal_AC'          'Internal' 'Internal_Fault1' 1  0  1  0  0.01   2.0   true    2
      'Internal_ABC'         'Internal' 'Internal_Fault1' 1  1  1  0  0.01   2.0   true    4
      'Internal_ABCG'        'Internal' 'Internal_Fault1' 1  1  1  1  0.01   2.0   true    4
      % ── HiZ: all 11 internal fault types ──────────────────────────────
      'Internal_HiZ_AG'      'Internal' 'Internal_Fault1' 1  0  0  1  50.0   300   true    3
      'Internal_HiZ_BG'      'Internal' 'Internal_Fault1' 0  1  0  1  50.0   300   true    2
      'Internal_HiZ_CG'      'Internal' 'Internal_Fault1' 0  0  1  1  50.0   300   true    2
      'Internal_HiZ_ABG'     'Internal' 'Internal_Fault1' 1  1  0  1  50.0   300   true    3
      'Internal_HiZ_BCG'     'Internal' 'Internal_Fault1' 0  1  1  1  50.0   300   true    2
      'Internal_HiZ_ACG'     'Internal' 'Internal_Fault1' 1  0  1  1  50.0   300   true    2
      'Internal_HiZ_AB'      'Internal' 'Internal_Fault1' 1  1  0  0  50.0   300   true    1
      'Internal_HiZ_BC'      'Internal' 'Internal_Fault1' 0  1  1  0  50.0   300   true    1
      'Internal_HiZ_AC'      'Internal' 'Internal_Fault1' 1  0  1  0  50.0   300   true    1
      'Internal_HiZ_ABC'     'Internal' 'Internal_Fault1' 1  1  1  0  50.0   300   true    2
      'Internal_HiZ_ABCG'    'Internal' 'Internal_Fault1' 1  1  1  1  50.0   300   true    2
      % ── Evolving fault (A-G → AB-G → ABC-G, handled in configureScenario)
      'Internal_Evolving'    'Internal' 'evolving'       1  0  0  1  0.01   0.5   true    4
      % ── External faults: standard (low-Z) ────────────────────────────
      'External_AG'          'External' 'External_Fault' 1  0  0  1  0.01   5.0   false   3
      'External_BG'          'External' 'External_Fault' 0  1  0  1  0.01   5.0   false   2
      'External_CG'          'External' 'External_Fault' 0  0  1  1  0.01   5.0   false   2
      'External_ABG'         'External' 'External_Fault' 1  1  0  1  0.01   5.0   false   2
      'External_BCG'         'External' 'External_Fault' 0  1  1  1  0.01   5.0   false   2
      'External_ACG'         'External' 'External_Fault' 1  0  1  1  0.01   5.0   false   2
      'External_AB'          'External' 'External_Fault' 1  1  0  0  0.01   5.0   false   2
      'External_ABC'         'External' 'External_Fault' 1  1  1  0  0.01   5.0   false   3
      'External_ABCG'        'External' 'External_Fault' 1  1  1  1  0.01   5.0   false   3
      % ── External HiZ (should NOT trip — critical for specificity) ────
      'External_HiZ_AG'      'External' 'External_Fault' 1  0  0  1  20.0   100   false   2
      'External_HiZ_ABG'     'External' 'External_Fault' 1  1  0  1  20.0   100   false   2
      'External_HiZ_ABCG'    'External' 'External_Fault' 1  1  1  1  20.0   100   false   2
      % ── Stress scenarios ─────────────────────────────────────────────
      'Stress_FaultInInrush' 'Internal' 'fault_inrush'   1  1  0  1  0.01   1.0   true    3
      'Stress_ExtInInrush'   'Inrush'   'ext_inrush'     1  0  0  1  0.01   5.0   false   2
      'Stress_CTSat'         'Internal' 'Internal_Fault1' 1  0  0  1  0.01   0.1   true    3
    };

    ST = struct();
    for i = 1:size(rows,1)
        ST(i).name       = rows{i,1};
        ST(i).zone       = rows{i,2};
        ST(i).block      = rows{i,3};
        ST(i).fA         = rows{i,4};
        ST(i).fB         = rows{i,5};
        ST(i).fC         = rows{i,6};
        ST(i).fG         = rows{i,7};
        ST(i).Rf_lo      = rows{i,8};
        ST(i).Rf_hi      = rows{i,9};
        ST(i).shouldTrip = rows{i,10};
        ST(i).weight     = rows{i,11};
        ST(i).faultTag   = buildFaultTag(rows{i,4},rows{i,5},rows{i,6},rows{i,7});
    end
end

% =========================================================================
% PARAMETER RANDOMISATION
% =========================================================================
function [t_fault, t_energise, Rf, noiseLevel, ctMismatch, secMode, angle_deg] = ...
          randomiseParams(sc, k, cnt)

    T_cycle   = 1/50;  % 50 Hz

    % Defaults
    t_energise = 0;
    angle_deg  = 0;
    secMode    = 'none';

    % ── Inrush scenarios ──────────────────────────────────────────────────
    if strcmp(sc.block,'inrush') || strcmp(sc.block,'inrush_load') || ...
       strcmp(sc.block,'fault_inrush')
        % Stratified angle sweep: divide [0.10, 0.80] into cnt equal bins,
        % then jitter within each bin → guaranteed uniform angle coverage
        binWidth   = 0.70 / cnt;
        t_energise = 0.10 + (k-1)*binWidth + rand()*binWidth;
        angle_deg  = mod(t_energise, T_cycle) / T_cycle * 360;

        if strcmp(sc.block,'inrush')
            secMode = 'noload';
        else
            secMode = 'loaded';
        end
    end

    % ── Fault inception time: uniform [0.30, 0.75] s ─────────────────────
    t_fault = 0.30 + 0.45*rand();

    % ── Fault resistance: log-uniform sampling within scenario range ──────
    if sc.Rf_lo >= sc.Rf_hi
        Rf = sc.Rf_lo;
    else
        logLo = log10(max(sc.Rf_lo, 1e-4));
        logHi = log10(sc.Rf_hi);
        Rf    = 10^(logLo + (logHi-logLo)*rand());
    end

    % ── Evolving fault: start low-Rf, allow to grow ───────────────────────
    % (Rf_lo is already very small for 'Evolving', no extra logic needed)

    % ── Noise level: uniform [0.003, 0.15] ───────────────────────────────
    noiseLevel = 0.003 + 0.147*rand();

    % ── CT saturation stress: heavy noise ─────────────────────────────────
    if strcmp(sc.name,'Stress_CTSat')
        noiseLevel = 0.10 + 0.15*rand();   % 10–25% noise
    end

    % ── CT gain mismatch: 6 channels, uniform [0.93, 1.07] ───────────────
    ctMismatch = 0.93 + 0.14*rand(6,1);

    if strcmp(sc.name,'Stress_CTSat')
        ctMismatch = 0.85 + 0.30*rand(6,1);  % severe mismatch ±15%
    end

    % ── Inception angle for fault scenarios ───────────────────────────────
    if strcmp(sc.zone,'Internal') || strcmp(sc.zone,'External')
        angle_deg = mod(t_fault, T_cycle) / T_cycle * 360;
    end
end

% =========================================================================
% SIMULINK CONFIGURATION
% =========================================================================
function configureBreakersClosed(model, t_close)
    %% Both breakers controlled via Step1/Step2 (External=on, signal=1→closed).
    %  Before=0 means breaker open at t=0; After=1 closes it at t_close.
    %  With t_close=0.05 s both breakers are fully closed well before any fault.
    set_param([model '/Step1'], 'Before','0','After','1', ...
              'Time', num2str(t_close,'%.6f'));
    set_param([model '/Step2'], 'Before','0','After','1', ...
              'Time', num2str(t_close,'%.6f'));
end

function configureInrushSample(model, t_energise, secMode)
    %% Configure for inrush using Step1/Step2 breaker control.
    %  Primary closes at t_energise; secondary depends on secMode.
    %  Breakers use External=on — signal=0 → open, signal=1 → closed.
    resetFaultBlocks(model);

    % Primary: Before=0 (open at t=0), After=1 (closes at t_energise)
    set_param([model '/Step1'], 'Before','0','After','1', ...
              'Time', num2str(t_energise,'%.8f'));

    switch secMode
        case 'noload'
            % Secondary stays open (no load connected during inrush)
            set_param([model '/Step2'], 'Before','0','After','0','Time','10');
        case 'loaded'
            % Secondary closes with primary (loaded energisation)
            set_param([model '/Step2'], 'Before','0','After','1', ...
                      'Time', num2str(t_energise,'%.8f'));
        otherwise
            set_param([model '/Step2'], 'Before','0','After','0','Time','10');
    end
end

function configureScenario(model, sc, t_fault, t_energise, Rf, secMode)
    switch sc.block
        case 'none'
            % Normal: both breakers closed, no faults
            configureBreakersClosed(model, 0.05);
            resetFaultBlocks(model);

        case {'inrush','inrush_load'}
            configureInrushSample(model, t_energise, secMode);

        case 'fault_inrush'
            % Internal fault fires shortly after inrush energisation
            configureInrushSample(model, t_energise, 'noload');
            t_f = t_energise + 0.04 + 0.06*rand();
            set_param([model '/Step5'],'Time', num2str(t_f,'%.6f'));
            applyFaultConfig(model,'Internal_Fault1', sc.fA,sc.fB,sc.fC,sc.fG, Rf);

        case 'ext_inrush'
            % External fault fires shortly after inrush energisation (should NOT trip)
            configureInrushSample(model, t_energise, 'noload');
            t_f = t_energise + 0.04 + 0.06*rand();
            set_param([model '/Step4'],'Time', num2str(t_f,'%.6f'));
            applyFaultConfig(model,'External_Fault', sc.fA,sc.fB,sc.fC,sc.fG, Rf);

        case 'evolving'
            % True three-stage evolving fault: A-G → AB-G → ABC-G
            %   Stage 1 (t_s1): Internal_Fault1 fires A-G via Step5
            %   Stage 2 (t_s2): Internal_Fault2 fires B-G via Step_Evolve2
            %   Stage 3 (t_s3): Internal_Fault3 fires C (no extra G) via Step_Evolve3
            % resetFaultBlocks already set Fault2/Fault3 to all-off.
            % We re-arm them here BEFORE the simulation starts.
            configureBreakersClosed(model, 0.05);
            resetFaultBlocks(model);   % fully disarms Fault1/2/3 and steps

            t_s1 = t_fault;
            t_s2 = t_s1 + 0.020 + 0.010*rand();   % +20–30 ms  A-G → AB-G
            t_s3 = t_s2 + 0.020 + 0.010*rand();   % +20–30 ms  AB-G → ABC-G

            % Stage 1: A-G on Fault1, triggered by Step5
            set_param([model '/Step5'],'Time', num2str(t_s1,'%.6f'));
            applyFaultConfig(model,'Internal_Fault1', 1,0,0,1, Rf);

            % Stage 2: B-G on Fault2, triggered by Step_Evolve2
            try, set_param([model '/Step_Evolve2'],'Time', num2str(t_s2,'%.6f')); catch, end
            try
                set_param([model '/Internal_Fault2'], ...
                    'FaultA','off','FaultB','on','FaultC','off','GroundFault','on', ...
                    'FaultResistance', num2str(Rf,'%.6f'), 'GroundResistance','0.001');
            catch, end

            % Stage 3: C on Fault3 (no separate ground — already grounded via Fault1/2)
            try, set_param([model '/Step_Evolve3'],'Time', num2str(t_s3,'%.6f')); catch, end
            try
                set_param([model '/Internal_Fault3'], ...
                    'FaultA','off','FaultB','off','FaultC','on','GroundFault','off', ...
                    'FaultResistance', num2str(Rf,'%.6f'), 'GroundResistance','1e6');
            catch, end

            fprintf('  Evolving: A-G@%.3fs → AB-G@%.3fs → ABC-G@%.3fs\n', t_s1,t_s2,t_s3);

        otherwise
            % Normal fault scenario: breakers closed before fault
            configureBreakersClosed(model, 0.05);
            resetFaultBlocks(model);

            if strcmp(sc.zone,'Internal')
                set_param([model '/Step5'],'Time', num2str(t_fault,'%.6f'));
                applyFaultConfig(model, sc.block, sc.fA,sc.fB,sc.fC,sc.fG, Rf);
            else
                % External: Step4 fires the external fault
                set_param([model '/Step4'],'Time', num2str(t_fault,'%.6f'));
                applyFaultConfig(model, sc.block, sc.fA,sc.fB,sc.fC,sc.fG, Rf);
            end
    end
end

function applyFaultConfig(model, blockName, fA, fB, fC, fG, Rf)
    %% Configure a Three-Phase Fault block safely.
    %  TWO-STEP PROTOCOL: fully disarm first, then arm only the active phases.
    %  This prevents Simulink topology conflicts when switching between
    %  different multi-phase fault configurations in a batch loop.
    blk = [model '/' blockName];
    onOff = @(x) ifelse(x,'on','off');

    % Step 1: disarm all phases (forces Simulink to recompile from clean state)
    try
        set_param(blk, 'FaultA','off','FaultB','off','FaultC','off','GroundFault','off');
    catch, end

    % Step 2: set fault resistance BEFORE re-arming phases
    try, set_param(blk,'FaultResistance', num2str(Rf,'%.6f')); catch, end

    % Step 3: only set GroundResistance when ground path is actually active.
    %  Setting GroundResistance=0.001 for ungrounded (fG=0) faults creates a
    %  spurious low-Z path and makes HiZ fault ODEs numerically stiff.
    if fG
        try, set_param(blk,'GroundResistance','0.001'); catch, end
    else
        try, set_param(blk,'GroundResistance','1e6'); catch, end  % effectively open
    end

    % Step 4: arm only the requested phases
    try
        set_param(blk, 'FaultA',onOff(fA), 'FaultB',onOff(fB), ...
                       'FaultC',onOff(fC), 'GroundFault',onOff(fG));
    catch, end
end

function injectNoiseCT(model, noiseLevel, ctMismatch)
    try
        for ch = 1:6
            set_param(sprintf('%s/Noise Merging Unit/CT_Gain_Mismatch_%d',model,ch), ...
                      'Gain', num2str(ctMismatch(ch),'%.6f'));
            set_param(sprintf('%s/Noise Merging Unit/Noise_Gain_%d',model,ch), ...
                      'Gain', num2str(noiseLevel,'%.6f'));
        end
    catch
        % Noise block absent — non-fatal
    end
end

function resetFaultBlocks(model)
    %% Reset all fault triggers and restore both breakers to closed state.
    % Step1 / Step2: breaker controls — restore to close at t=0.05 s
    set_param([model '/Step1'], 'Before','0','After','1','Time','0.050000');
    set_param([model '/Step2'], 'Before','0','After','1','Time','0.050000');
    % Step5 / Step4: internal and external fault inception triggers
    set_param([model '/Step5'],'Time','10');
    set_param([model '/Step4'],'Time','10');
    % Step_Evolve2 / Step_Evolve3: evolving-fault stage triggers
    try, set_param([model '/Step_Evolve2'],'Time','10'); catch, end
    try, set_param([model '/Step_Evolve3'],'Time','10'); catch, end

    % Internal_Fault1 (primary internal fault block — A-G stage)
    try
        set_param([model '/Internal_Fault1'], ...
                  'FaultA','off','FaultB','off','FaultC','off','GroundFault','off', ...
                  'FaultResistance','0.01');
    catch, end
    % Internal_Fault2 (evolving stage 2) — ALL phases OFF in reset
    % CRITICAL: must be fully disarmed, not left with FaultB=on.
    % The evolving-fault configureScenario case re-arms it explicitly.
    try
        set_param([model '/Internal_Fault2'], ...
                  'FaultA','off','FaultB','off','FaultC','off','GroundFault','off', ...
                  'FaultResistance','0.01');
    catch, end
    % Internal_Fault3 (evolving stage 3) — ALL phases OFF in reset
    try
        set_param([model '/Internal_Fault3'], ...
                  'FaultA','off','FaultB','off','FaultC','off','GroundFault','off', ...
                  'FaultResistance','0.01');
    catch, end
    % External_Fault
    try
        set_param([model '/External_Fault'], ...
                  'FaultA','off','FaultB','off','FaultC','off','GroundFault','off', ...
                  'FaultResistance','0.01');
    catch, end
end

% =========================================================================
% POST-GENERATION CONSOLE VERIFICATION REPORT
% =========================================================================
function printVerificationReport(dataset, N, ST, counts)

    nSuccess  = sum(strcmp(dataset.simulationStatus,'Success'));
    nFailed   = N - nSuccess;

    fprintf('\n');
    fprintf('╔══════════════════════════════════════════════════════════════╗\n');
    fprintf('║         STRESS-TEST BATCH — VERIFICATION REPORT             ║\n');
    fprintf('╚══════════════════════════════════════════════════════════════╝\n');
    fprintf('Total samples   : %d\n', N);
    fprintf('Successful runs : %d  (%.2f%%)\n', nSuccess, nSuccess/N*100);
    fprintf('Failed runs     : %d  (%.2f%%)\n', nFailed,  nFailed/N*100);

    % ── Per-zone summary ──────────────────────────────────────────────────
    fprintf('\n── Zone distribution ──\n');
    zones = {'Normal','Inrush','Internal','External'};
    for z = zones
        mask = strcmp(dataset.zone, z{1});
        n_z  = sum(mask);
        pct  = n_z/N*100;
        nTrip= sum(dataset.shouldTrip(mask));
        fprintf('  %-10s : %4d  (%5.1f%%)   shouldTrip=%d\n', z{1}, n_z, pct, nTrip);
    end

    % ── Per-scenario count vs target ──────────────────────────────────────
    fprintf('\n── Scenario counts (actual vs target) ──\n');
    for si = 1:numel(ST)
        mask   = strcmp(dataset.scenarioName, ST(si).name);
        actual = sum(mask);
        target = counts(si);
        ok     = abs(actual - target) <= 1;
        fprintf('  %-30s  actual=%4d  target=%4d  %s\n', ...
                ST(si).name, actual, target, ifelse(ok,'✓','⚠'));
    end

    % ── Trip rate per zone (chi-squared test) ─────────────────────────────
    fprintf('\n── Trip rate consistency check ──\n');
    expected_trip = {'Normal',0; 'Inrush',0; 'Internal',1; 'External',0};
    for r = 1:size(expected_trip,1)
        mask   = strcmp(dataset.zone, expected_trip{r,1});
        n_z    = sum(mask);
        if n_z == 0, continue; end
        n_trip = sum(dataset.shouldTrip(mask));
        rate   = n_trip / n_z;
        exp_r  = expected_trip{r,2};
        ok     = abs(rate - exp_r) < 0.01;
        fprintf('  %-10s trip rate = %.4f  (expected %.0f)  %s\n', ...
                expected_trip{r,1}, rate, exp_r, ifelse(ok,'✓','⚠ MISMATCH'));
    end

    % ── Resistance distribution: K-S test (uniform on log scale) ──────────
    fprintf('\n── Fault resistance coverage (internal faults) ──\n');
    intMask = strcmp(dataset.zone,'Internal');
    Rf_int  = dataset.faultResistance(intMask);
    Rf_nonZ = Rf_int(Rf_int > 0.5);   % exclude normal/inrush zeros
    if numel(Rf_nonZ) > 10
        logRf = log10(Rf_nonZ);
        [~,p_ks] = kstest((logRf - min(logRf)) / (max(logRf)-min(logRf)+eps) - 0.5);
        fprintf('  Low-Z  (Rf ≤ 2 Ω)   : %d samples\n', sum(Rf_int <= 2 & Rf_int > 0));
        fprintf('  High-Z (Rf > 2 Ω)   : %d samples\n', sum(Rf_int > 2));
        fprintf('  K-S test on log(Rf): p = %.3f  %s\n', p_ks, ...
                ifelse(p_ks > 0.05,'(log-uniform ✓)','(non-uniform ⚠)'));
    end

    % ── Inception angle uniformity (chi-squared) ──────────────────────────
    fprintf('\n── Inception angle uniformity (internal fault samples) ──\n');
    angles = dataset.inceptionAngle(intMask & dataset.inceptionAngle > 0);
    if numel(angles) > 20
        edges  = 0:45:360;
        obs    = histcounts(angles, edges);
        exp_u  = numel(angles)/8 * ones(1,8);
        chi2   = sum((obs - exp_u).^2 ./ exp_u);
        p_chi  = 1 - chi2cdf(chi2, 7);
        fprintf('  Counts per 45° bin: '); fprintf('%3d ', obs); fprintf('\n');
        fprintf('  χ²(7) = %.2f  p = %.3f  %s\n', chi2, p_chi, ...
                ifelse(p_chi > 0.05,'(uniform ✓)','(non-uniform ⚠)'));
    end

    % ── Inrush angle uniformity ───────────────────────────────────────────
    fprintf('\n── Inrush energisation angle uniformity ──\n');
    irMask  = strcmp(dataset.zone,'Inrush');
    irAngle = dataset.inceptionAngle(irMask);
    if numel(irAngle) > 8
        edges  = 0:45:360;
        obs    = histcounts(irAngle, edges);
        exp_u  = numel(irAngle)/8 * ones(1,8);
        chi2   = sum((obs - exp_u).^2 ./ exp_u);
        p_chi  = 1 - chi2cdf(chi2, 7);
        fprintf('  Counts per 45° bin: '); fprintf('%3d ', obs); fprintf('\n');
        fprintf('  χ²(7) = %.2f  p = %.3f  %s\n', chi2, p_chi, ...
                ifelse(p_chi > 0.05,'(uniform ✓)','(non-uniform ⚠)'));
    end

    % ── Class balance for DL training ─────────────────────────────────────
    nTrip  = sum(dataset.shouldTrip);
    nNoTrip= N - nTrip;
    imb    = max(nTrip,nNoTrip) / max(min(nTrip,nNoTrip),1);
    fprintf('\n── Class balance (binary trip label) ──\n');
    fprintf('  shouldTrip=true  : %d  (%.1f%%)\n', nTrip,   nTrip/N*100);
    fprintf('  shouldTrip=false : %d  (%.1f%%)\n', nNoTrip, nNoTrip/N*100);
    fprintf('  Imbalance ratio  : %.2f  %s\n', imb, ...
            ifelse(imb < 3,'(acceptable ✓)','(high — check pos_weight in training ⚠)'));

    fprintf('\n── pos_weight recommendation for BCEWithLogitsLoss ──\n');
    fprintf('  pos_weight = %.4f  (= n_neg/n_pos)\n', nNoTrip/max(nTrip,1));

    fprintf('\n╔══════════════════════════════════════════════════════════════╗\n');
    fprintf('║              END OF VERIFICATION REPORT                     ║\n');
    fprintf('╚══════════════════════════════════════════════════════════════╝\n\n');
end

% =========================================================================
% POST-GENERATION DIAGNOSTIC FIGURES
% =========================================================================
function plotDiagnostics(dataset, N, ST, counts, saveViz, timestamp)

    nSuccess = sum(strcmp(dataset.simulationStatus,'Success'));

    % ── Colour map for zones ──────────────────────────────────────────────
    zoneColors = containers.Map( ...
        {'Normal','Inrush','Internal','External','Unknown'}, ...
        {[0.40 0.78 0.40],[0.98 0.72 0.20],[0.90 0.30 0.30],[0.30 0.58 0.90],[0.70 0.70 0.70]});

    % =====================================================================
    % FIGURE 1 — Dataset Composition
    % =====================================================================
    fig1 = figure('Name','Stress-Test: Dataset Composition', ...
                  'Position',[50 100 1280 780],'Color','w');

    zones     = {'Normal','Inrush','Internal','External'};
    zoneCounts= cellfun(@(z) sum(strcmp(dataset.zone,z)), zones);
    zColMat   = cell2mat(cellfun(@(z) zoneColors(z), zones,'UniformOutput',false)');

    % 1a: Zone pie chart
    ax1 = subplot(3,4,1);
    pie(ax1, zoneCounts, zones);
    colormap(ax1, zColMat);
    title('Zone Distribution','FontWeight','bold');

    % 1b: shouldTrip bar
    ax2 = subplot(3,4,2);
    tripCounts = [sum(~dataset.shouldTrip), sum(dataset.shouldTrip)];
    bar(ax2, tripCounts, 'FaceColor','flat', ...
        'CData',[0.40 0.70 0.40; 0.90 0.30 0.30]);
    set(ax2,'XTickLabel',{'No-Trip','Trip'},'FontSize',9);
    ylabel(ax2,'Count');
    title('Trip Label Balance','FontWeight','bold');
    for i=1:2, text(i, tripCounts(i)+2, sprintf('%.1f%%',tripCounts(i)/N*100), ...
                    'HorizontalAlignment','center','FontSize',8,'Parent',ax2); end

    % 1c: Scenario actual vs target
    ax3 = subplot(3,4,[3 4]);
    scNames   = {ST.name};
    actCounts = cellfun(@(n) sum(strcmp(dataset.scenarioName,n)), scNames);
    x = 1:numel(ST);
    bar(ax3, x, counts, 0.8, 'FaceColor',[0.80 0.88 1.00],'EdgeColor',[0.5 0.5 0.8]); hold(ax3,'on');
    bar(ax3, x, actCounts, 0.5, 'FaceColor',[0.30 0.58 0.90],'EdgeColor','none');
    hold(ax3,'off');
    set(ax3,'XTick',x,'XTickLabel',scNames,'XTickLabelRotation',45,'FontSize',7);
    ylabel(ax3,'Count'); legend(ax3,{'Target','Actual'},'Location','northeast','FontSize',8);
    title(ax3,'Scenario Counts: Target vs Actual','FontWeight','bold');
    grid(ax3,'on');

    % 1d: Per-zone stacked trip/no-trip
    ax4 = subplot(3,4,5);
    tripZ  = cellfun(@(z) sum(strcmp(dataset.zone,z) & dataset.shouldTrip),  zones);
    noTripZ= cellfun(@(z) sum(strcmp(dataset.zone,z) & ~dataset.shouldTrip), zones);
    b = bar(ax4, [noTripZ; tripZ]','stacked');
    b(1).FaceColor = [0.40 0.78 0.40]; b(2).FaceColor = [0.90 0.30 0.30];
    set(ax4,'XTickLabel',zones,'FontSize',9);
    legend(ax4,{'No-Trip','Trip'},'Location','northwest','FontSize',8);
    title(ax4,'Trip/No-Trip per Zone','FontWeight','bold');

    % 1e: Simulation success rate per scenario
    ax5 = subplot(3,4,[6 7 8]);
    succRates = zeros(1,numel(ST));
    for si = 1:numel(ST)
        mask = strcmp(dataset.scenarioName, ST(si).name);
        n_sc = sum(mask);
        if n_sc > 0
            succRates(si) = sum(strcmp(dataset.simulationStatus(mask),'Success')) / n_sc * 100;
        end
    end
    bar(ax5, x, succRates, 'FaceColor','flat', ...
        'CData', repmat([0.35 0.78 0.35], numel(ST), 1));
    set(ax5,'XTick',x,'XTickLabel',scNames,'XTickLabelRotation',45,'FontSize',7);
    ylabel(ax5,'Success (%)'); ylim(ax5,[0 105]);
    yline(ax5, 100,'r--','LineWidth',1.2);
    title(ax5,'Simulation Success Rate per Scenario','FontWeight','bold');
    grid(ax5,'on');

    % 1f: Fault type breakdown (pie of internal fault sub-types)
    ax6 = subplot(3,4,[9 10]);
    intNames = {ST(strcmp({ST.zone},'Internal')).name};
    intCnt   = cellfun(@(n) sum(strcmp(dataset.scenarioName,n)), intNames);
    [~, sI]  = sort(intCnt,'descend');
    pie(ax6, intCnt(sI), intNames(sI));
    title(ax6,'Internal Fault Sub-types','FontWeight','bold');

    % 1g: External fault type breakdown
    ax7 = subplot(3,4,[11 12]);
    extNames = {ST(strcmp({ST.zone},'External')).name};
    extCnt   = cellfun(@(n) sum(strcmp(dataset.scenarioName,n)), extNames);
    [~, sI]  = sort(extCnt,'descend');
    pie(ax7, extCnt(sI), extNames(sI));
    title(ax7,'External Fault Sub-types','FontWeight','bold');

    sgtitle(fig1, sprintf('Dataset Composition  |  N=%d  |  Success %.1f%%', ...
            N, nSuccess/N*100), 'FontSize',13,'FontWeight','bold');

    % =====================================================================
    % FIGURE 2 — Parameter Space Coverage
    % =====================================================================
    fig2 = figure('Name','Stress-Test: Parameter Space Coverage', ...
                  'Position',[80 60 1280 820],'Color','w');

    % 2a: Fault resistance histogram (log scale, internal non-zero)
    ax1 = subplot(3,3,1);
    intMask = strcmp(dataset.zone,'Internal');
    Rf_plt  = dataset.faultResistance(intMask & dataset.faultResistance > 0.005);
    if ~isempty(Rf_plt)
        edges_log = logspace(log10(0.005), log10(350), 40);
        histogram(ax1, Rf_plt, edges_log, 'FaceColor',[0.90 0.40 0.40],'EdgeColor','none');
        set(ax1,'XScale','log');
        xlabel(ax1,'Fault Resistance Rf (Ω)'); ylabel(ax1,'Count');
        title(ax1,'Rf Distribution — Internal Faults','FontWeight','bold');
        xline(ax1, 2,  '--k','LineWidth',1.2,'Label','2 Ω','LabelHorizontalAlignment','center');
        xline(ax1, 50, '--b','LineWidth',1.2,'Label','50 Ω','LabelHorizontalAlignment','center');
        grid(ax1,'on');
    end

    % 2b: Fault resistance histogram (external)
    ax2 = subplot(3,3,2);
    extMask = strcmp(dataset.zone,'External');
    Rf_ext  = dataset.faultResistance(extMask & dataset.faultResistance > 0.005);
    if ~isempty(Rf_ext)
        edges_log2 = logspace(log10(0.005), log10(10), 30);
        histogram(ax2, Rf_ext, edges_log2, 'FaceColor',[0.30 0.58 0.90],'EdgeColor','none');
        set(ax2,'XScale','log');
        xlabel(ax2,'Fault Resistance Rf (Ω)'); ylabel(ax2,'Count');
        title(ax2,'Rf Distribution — External Faults','FontWeight','bold');
        grid(ax2,'on');
    end

    % 2c: Inception angle distribution (fault samples)
    ax3 = subplot(3,3,3);
    fltMask = strcmp(dataset.zone,'Internal') | strcmp(dataset.zone,'External');
    angles  = dataset.inceptionAngle(fltMask & dataset.inceptionAngle > 0);
    if ~isempty(angles)
        polarhistogram(polaraxes(fig2,'Position',get(ax3,'Position')), ...
                       deg2rad(angles), 16, ...
                       'FaceColor',[0.98 0.65 0.20],'EdgeColor','none');
        delete(ax3);
        title(gca,'Inception Angle (fault samples)','FontWeight','bold');
    end

    % 2d: Inrush energisation angle (polar)
    ax4 = subplot(3,3,4);
    irMask = strcmp(dataset.zone,'Inrush');
    irAng  = dataset.inceptionAngle(irMask);
    if ~isempty(irAng)
        polarhistogram(polaraxes(fig2,'Position',get(ax4,'Position')), ...
                       deg2rad(irAng), 16, ...
                       'FaceColor',[0.40 0.80 0.40],'EdgeColor','none');
        delete(ax4);
        title(gca,'Inrush Energisation Angle','FontWeight','bold');
    end

    % 2e: Noise level distribution
    ax5 = subplot(3,3,5);
    histogram(ax5, dataset.noiseLevel, 30, ...
              'FaceColor',[0.55 0.40 0.80],'EdgeColor','none');
    xlabel(ax5,'Noise Level (fraction)'); ylabel(ax5,'Count');
    title(ax5,'Noise Level Distribution','FontWeight','bold');
    xline(ax5, 0.10,'--r','LineWidth',1.2,'Label','Stress threshold');
    grid(ax5,'on');

    % 2f: CT mismatch spread (all channels pooled)
    ax6 = subplot(3,3,6);
    validCT = dataset.ctMismatch(~cellfun(@isempty, dataset.ctMismatch));
    if ~isempty(validCT)
        allCT = cell2mat(validCT);
        histogram(ax6, allCT(:), 40, ...
                  'FaceColor',[0.35 0.70 0.70],'EdgeColor','none');
        xlabel(ax6,'CT Gain Mismatch'); ylabel(ax6,'Count');
        title(ax6,'CT Mismatch Distribution (all channels)','FontWeight','bold');
        xline(ax6, 1.0,'--k','LineWidth',1.2,'Label','Unity gain');
        grid(ax6,'on');
    end

    % 2g: Scatter Rf vs inception angle (internal, coloured by HiZ / LowZ)
    ax7 = subplot(3,3,7);
    intMaskSc = strcmp(dataset.zone,'Internal') & dataset.faultResistance > 0.005;
    Rf_sc   = dataset.faultResistance(intMaskSc);
    ang_sc  = dataset.inceptionAngle(intMaskSc);
    isHiZ   = Rf_sc > 10;
    scatter(ax7, ang_sc(~isHiZ), log10(Rf_sc(~isHiZ)), 10, [0.90 0.30 0.30], ...
            'filled','MarkerFaceAlpha',0.5); hold(ax7,'on');
    scatter(ax7, ang_sc(isHiZ),  log10(Rf_sc(isHiZ)),  14, [0.20 0.40 0.90], ...
            'filled','MarkerFaceAlpha',0.5);
    hold(ax7,'off');
    xlabel(ax7,'Inception Angle (°)'); ylabel(ax7,'log_{10}(Rf)');
    legend(ax7,{'Low-Z (≤10 Ω)','Hi-Z (>10 Ω)'},'Location','northwest','FontSize',8);
    title(ax7,'Rf vs Inception Angle (Internal)','FontWeight','bold');
    grid(ax7,'on');

    % 2h: Noise vs Rf scatter (coloured by zone)
    ax8 = subplot(3,3,8);
    hold(ax8,'on');
    zoneList = {'Normal','Inrush','Internal','External'};
    for z = zoneList
        m = strcmp(dataset.zone, z{1}) & dataset.faultResistance > 0.005;
        if any(m)
            scatter(ax8, log10(dataset.faultResistance(m)+0.001), ...
                         dataset.noiseLevel(m), 8, zoneColors(z{1}), ...
                    'filled','MarkerFaceAlpha',0.4,'DisplayName',z{1});
        end
    end
    hold(ax8,'off'); legend(ax8,'Location','northeast','FontSize',8);
    xlabel(ax8,'log_{10}(Rf)'); ylabel(ax8,'Noise Level');
    title(ax8,'Noise vs Rf (by zone)','FontWeight','bold');
    grid(ax8,'on');

    % 2i: Inception time histogram
    ax9 = subplot(3,3,9);
    histogram(ax9, dataset.inceptionTime(dataset.inceptionTime > 0 & dataset.inceptionTime < 1), ...
              30, 'FaceColor',[0.80 0.55 0.30],'EdgeColor','none');
    xlabel(ax9,'Inception / Energisation Time (s)'); ylabel(ax9,'Count');
    title(ax9,'Fault / Energisation Time Distribution','FontWeight','bold');
    grid(ax9,'on');

    sgtitle(fig2,'Parameter Space Coverage','FontSize',13,'FontWeight','bold');

    % =====================================================================
    % FIGURE 3 — Statistical Verification
    % =====================================================================
    fig3 = figure('Name','Stress-Test: Statistical Verification', ...
                  'Position',[110 40 1280 820],'Color','w');

    % 3a: Trip rate per scenario + 95% confidence interval
    ax1 = subplot(3,3,[1 2]);
    tripRates = zeros(1,numel(ST));
    tripCI    = zeros(1,numel(ST));
    for si = 1:numel(ST)
        mask = strcmp(dataset.scenarioName, ST(si).name);
        n_sc = sum(mask);
        if n_sc == 0, continue; end
        p = sum(dataset.shouldTrip(mask)) / n_sc;
        tripRates(si) = p;
        tripCI(si)    = 1.96 * sqrt(p*(1-p)/max(n_sc,1));  % Wilson 95% CI ≈
    end
    bar(ax1, x, tripRates, 'FaceColor',[0.85 0.40 0.40],'EdgeColor','none'); hold(ax1,'on');
    errorbar(ax1, x, tripRates, tripCI, 'k.', 'LineWidth',1.2,'CapSize',4);
    expectedTrip = double([ST.shouldTrip]);
    scatter(ax1, x, expectedTrip, 40, 'k^', 'filled', 'DisplayName','Expected');
    hold(ax1,'off');
    set(ax1,'XTick',x,'XTickLabel',{ST.name},'XTickLabelRotation',45,'FontSize',7);
    ylabel(ax1,'Trip Rate'); ylim(ax1,[-0.05 1.15]);
    legend(ax1,{'Measured','95% CI','Expected'},'Location','northeast','FontSize',8);
    title(ax1,'Trip Rate per Scenario (± 95% CI)','FontWeight','bold');
    grid(ax1,'on');

    % 3b: Chi-squared angle uniformity (8 bins) per zone
    ax2 = subplot(3,3,3);
    chi2Vals = zeros(1,4); pVals = zeros(1,4);
    zoneList2 = {'Normal','Inrush','Internal','External'};
    for zi = 1:4
        mask = strcmp(dataset.zone, zoneList2{zi});
        ang  = dataset.inceptionAngle(mask & dataset.inceptionAngle > 0);
        if numel(ang) < 8, continue; end
        obs  = histcounts(ang, 0:45:360);
        exp  = numel(ang)/8 * ones(1,8);
        chi2Vals(zi) = sum((obs-exp).^2./exp);
        pVals(zi)    = 1 - chi2cdf(chi2Vals(zi), 7);
    end
    bh = bar(ax2, 1:4, chi2Vals, 'FaceColor','flat');
    bh.CData = repmat([0.55 0.75 0.55],4,1);
    bh.CData(pVals < 0.05,:) = repmat([0.90 0.40 0.40], sum(pVals<0.05), 1);
    yline(ax2, chi2inv(0.95,7),'--r','LineWidth',1.5,'Label','χ²₀.₀₅','LabelHorizontalAlignment','left');
    set(ax2,'XTick',1:4,'XTickLabel',zoneList2,'FontSize',9);
    ylabel(ax2,'χ²(7) statistic'); title(ax2,'Angle Uniformity χ² Test','FontWeight','bold');
    text(1:4, chi2Vals+0.2, arrayfun(@(p) sprintf('p=%.2f',p), pVals,'UniformOutput',false), ...
         'HorizontalAlignment','center','FontSize',8,'Parent',ax2);
    grid(ax2,'on');

    % 3c: K-S test on log(Rf) uniformity — bar showing p-values per zone
    ax3 = subplot(3,3,4);
    ksP = zeros(1,4);
    for zi = 1:4
        mask = strcmp(dataset.zone, zoneList2{zi});
        Rf_z = dataset.faultResistance(mask & dataset.faultResistance > 0.01);
        if numel(Rf_z) < 10, continue; end
        logR = log10(Rf_z);
        U    = (logR - min(logR)) / (max(logR)-min(logR)+eps) - 0.5;
        [~, ksP(zi)] = kstest(U);
    end
    bh2 = bar(ax3, 1:4, ksP, 'FaceColor','flat');
    bh2.CData = repmat([0.40 0.65 0.90],4,1);
    bh2.CData(ksP < 0.05,:) = repmat([0.90 0.40 0.40], sum(ksP<0.05), 1);
    yline(ax3, 0.05,'--r','LineWidth',1.5,'Label','p=0.05');
    set(ax3,'XTick',1:4,'XTickLabel',zoneList2,'FontSize',9);
    ylabel(ax3,'K-S p-value'); ylim(ax3,[0 1.05]);
    title(ax3,'Rf Log-Uniform K-S Test','FontWeight','bold');
    grid(ax3,'on');

    % 3d: Per-fault-type trip rate heat-map (row = zone, col = fault tag)
    ax4 = subplot(3,3,[5 6]);
    uniqueTags = unique(dataset.faultType);
    uniqueTags = uniqueTags(~cellfun(@isempty,uniqueTags));
    zoneList3  = {'Internal','External'};
    heatData   = nan(2, numel(uniqueTags));
    for zi = 1:2
        for ti = 1:numel(uniqueTags)
            mask = strcmp(dataset.zone,zoneList3{zi}) & strcmp(dataset.faultType,uniqueTags{ti});
            n_m  = sum(mask);
            if n_m > 0
                heatData(zi,ti) = sum(dataset.shouldTrip(mask)) / n_m;
            end
        end
    end
    imagesc(ax4, heatData); colormap(ax4, redblue_cmap(256)); caxis(ax4,[0 1]);
    colorbar(ax4);
    set(ax4,'XTick',1:numel(uniqueTags),'XTickLabel',uniqueTags, ...
            'XTickLabelRotation',45,'YTick',1:2,'YTickLabel',zoneList3,'FontSize',8);
    title(ax4,'Trip Rate Heat-map  (zone × fault type)','FontWeight','bold');

    % 3e: Noise level CDF by zone
    ax5 = subplot(3,3,7);
    hold(ax5,'on');
    for z = zoneList
        mask = strcmp(dataset.zone, z{1});
        if sum(mask) < 2, continue; end
        nl   = sort(dataset.noiseLevel(mask));
        cdf  = (1:sum(mask)) / sum(mask);
        plot(ax5, nl, cdf, 'LineWidth',1.8, 'Color', zoneColors(z{1}), ...
             'DisplayName', z{1});
    end
    hold(ax5,'off');
    xlabel(ax5,'Noise Level'); ylabel(ax5,'CDF');
    legend(ax5,'Location','southeast','FontSize',8);
    title(ax5,'Noise Level CDF by Zone','FontWeight','bold');
    grid(ax5,'on');

    % 3f: CT mismatch per channel (box plot)
    ax6 = subplot(3,3,8);
    validCT2 = dataset.ctMismatch(~cellfun(@isempty, dataset.ctMismatch));
    if numel(validCT2) > 5
        CTmat = cell2mat(validCT2)';   % (6 × nSamples)
        boxplot(ax6, CTmat', 'Labels', {'CH1','CH2','CH3','CH4','CH5','CH6'});
        yline(ax6, 1.0,'--k','LineWidth',1.2);
        xlabel(ax6,'CT Channel'); ylabel(ax6,'Gain Mismatch');
        title(ax6,'CT Mismatch per Channel','FontWeight','bold');
        grid(ax6,'on');
    end

    % 3g: Class imbalance with recommended pos_weight annotation
    ax7 = subplot(3,3,9);
    nT  = sum(dataset.shouldTrip);
    nNT = N - nT;
    barh(ax7, [1 2], [nNT nT], 'FaceColor','flat', ...
         'CData',[0.40 0.78 0.40; 0.90 0.30 0.30]);
    set(ax7,'YTick',[1 2],'YTickLabel',{'No-Trip','Trip'},'FontSize',10);
    xlabel(ax7,'Sample Count');
    title(ax7,'Binary Class Balance','FontWeight','bold');
    text(max(nNT,nT)*0.05, 1, sprintf('N=%d (%.1f%%)',nNT,nNT/N*100), ...
         'FontSize',9,'VerticalAlignment','middle','Parent',ax7);
    text(max(nNT,nT)*0.05, 2, sprintf('N=%d (%.1f%%)',nT,nT/N*100), ...
         'FontSize',9,'VerticalAlignment','middle','Parent',ax7);
    text(0.65, 0.05, sprintf('pos\\_weight = %.3f', nNT/max(nT,1)), ...
         'Units','normalized','FontSize',9,'FontWeight','bold', ...
         'Color',[0.20 0.20 0.60],'Parent',ax7);
    grid(ax7,'on');

    sgtitle(fig3,'Statistical Verification & Class Balance', ...
            'FontSize',13,'FontWeight','bold');

    % ── Save figures ──────────────────────────────────────────────────────
    if saveViz
        figDir = fullfile(pwd,'StressTest_Diagnostics');
        if ~exist(figDir,'dir'), mkdir(figDir); end
        names = {'Composition','ParameterCoverage','StatVerification'};
        for fi = 1:3
            fh = eval(sprintf('fig%d',fi));
            saveas(fh, fullfile(figDir, sprintf('%s_%s_%s.png', ...
                   'StressDiag', names{fi}, timestamp)));
        end
        fprintf('Diagnostic figures saved to: %s\n', figDir);
    end
end

% =========================================================================
% PRE-ALLOCATE DATASET STRUCT
% =========================================================================
function dataset = preallocateDataset(N, model)
    dataset.metadata             = struct();
    dataset.metadata.nSamples    = N;
    dataset.metadata.generatedDate = datetime('now');
    dataset.metadata.modelName   = model;
    dataset.metadata.generatorType = 'ControlPanel_StressTest';
    dataset.metadata.description = ['Comprehensive stress-test dataset. ' ...
        'All 11 internal fault types (AG/BG/CG/ABG/BCG/ACG/AB/BC/AC/ABC/ABCG) ' ...
        'plus 9 external, HiZ, evolving, CT-sat, fault-in-inrush scenarios. ' ...
        'Step1/Step2 breaker control throughout (External=on, signal=1→closed).'];

    dataset.zone              = cell(N,1);
    dataset.faultType         = cell(N,1);
    dataset.scenarioName      = cell(N,1);
    dataset.faultResistance   = zeros(N,1);
    dataset.inceptionAngle    = zeros(N,1);
    dataset.inceptionTime     = zeros(N,1);
    dataset.energisationTime  = zeros(N,1);
    dataset.shouldTrip        = false(N,1);
    dataset.noiseLevel        = zeros(N,1);
    dataset.ctMismatch        = cell(N,1);
    dataset.secondaryMode     = cell(N,1);

    dataset.primaryCurrent    = cell(N,1);
    dataset.secondaryCurrent  = cell(N,1);
    dataset.diffCurrent       = cell(N,1);
    dataset.restCurrent       = cell(N,1);
    dataset.tripSignal        = cell(N,1);
    dataset.simulationStatus  = cell(N,1);
end

% =========================================================================
% SHARED UTILITY FUNCTIONS
% =========================================================================

function tag = buildFaultTag(fA, fB, fC, fG)
    phases = '';
    if fA, phases = [phases 'A']; end
    if fB, phases = [phases 'B']; end
    if fC, phases = [phases 'C']; end
    if fG, phases = [phases 'G']; end
    if isempty(phases), tag = 'None'; else, tag = phases; end
end

function val = safeGet(simOut, varName)
    try, val = simOut.get(varName); return; catch, end
    try, val = simOut.(varName);    return; catch, end
    val = [];
end

function result = ifelse(cond, a, b)
    if cond, result = a; else, result = b; end
end

function cmap = redblue_cmap(n)
    % White-centred blue→white→red colour map for heat-maps
    half = floor(n/2);
    r1   = linspace(0.15, 1.00, half)';
    g1   = linspace(0.20, 1.00, half)';
    b1   = ones(half,1);
    r2   = ones(n-half,1);
    g2   = linspace(1.00, 0.20, n-half)';
    b2   = linspace(1.00, 0.15, n-half)';
    cmap = [[r1;r2] [g1;g2] [b1;b2]];
end
