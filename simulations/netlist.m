function netlist
% =========================================================================
% NETLIST.M  —  Detailed Simulink / Simscape netlist logger
% =========================================================================
%
% Produces a structured log of every block, port, signal line, bus
% connection, and key electrical parameter in the model.
%
% OUTPUT
%   netlist_<modelName>_<timestamp>.txt   — full plain-text report
%   netlist_<modelName>_<timestamp>.csv   — flat CSV for spreadsheet review
%
% USAGE
%   Open the Simulink model, then run:  netlist
%
% =========================================================================

    % ── Resolve model name ───────────────────────────────────────────────
    modelName = gcs;
    if isempty(modelName)
        error('No Simulink model is open. Open your model first.');
    end
    modelName = bdroot(modelName);
    load_system(modelName);

    % ── Output files ─────────────────────────────────────────────────────
    ts       = datestr(now, 'yyyymmdd_HHMMSS');
    txtFile  = sprintf('netlist_%s_%s.txt', modelName, ts);
    csvFile  = sprintf('netlist_%s_%s.csv', modelName, ts);

    fidTxt = fopen(txtFile, 'w');
    fidCsv = fopen(csvFile, 'w');

    % CSV header
    fprintf(fidCsv, 'BlockPath,BlockType,LibraryLink,Parameter,Value\n');

    % =========================================================================
    hdr(fidTxt, sprintf('SIMULINK NETLIST  —  %s', modelName));
    fprintf(fidTxt, 'Generated : %s\n', datestr(now));
    fprintf(fidTxt, 'MATLAB    : %s\n', version);
    fprintf(fidTxt, '\n');

    % =========================================================================
    % SECTION 1 — MODEL SUMMARY
    % =========================================================================
    hdr(fidTxt, '1. MODEL SUMMARY');

    allBlocks = find_system(modelName, 'Type', 'block');
    allLines  = find_system(modelName, 'Type', 'line');
    allPorts  = find_system(modelName, 'Type', 'port');
    subs      = find_system(modelName, 'BlockType', 'SubSystem');

    fprintf(fidTxt, '  Total blocks     : %d\n', numel(allBlocks));
    fprintf(fidTxt, '  Total lines      : %d\n', numel(allLines));
    fprintf(fidTxt, '  Total ports      : %d\n', numel(allPorts));
    fprintf(fidTxt, '  Subsystems       : %d\n', numel(subs));

    % Block-type histogram
    types = cellfun(@(b) get_param(b,'BlockType'), allBlocks, 'UniformOutput', false);
    uTypes = unique(types);
    fprintf(fidTxt, '\n  Block-type inventory:\n');
    for i = 1:numel(uTypes)
        cnt = sum(strcmp(types, uTypes{i}));
        fprintf(fidTxt, '    %-40s : %d\n', uTypes{i}, cnt);
    end

    % =========================================================================
    % SECTION 2 — BLOCK HIERARCHY (TREE)
    % =========================================================================
    hdr(fidTxt, '2. BLOCK HIERARCHY');
    printHierarchy(fidTxt, modelName, modelName, 0);

    % =========================================================================
    % SECTION 3 — FULL BLOCK PARAMETER DUMP
    % =========================================================================
    hdr(fidTxt, '3. BLOCK PARAMETERS (ALL BLOCKS)');

    % Categories of interest for power-systems models
    electricalKeywords = {'Resistance','Inductance','Capacitance','Voltage', ...
                          'Current','Frequency','Power','Impedance','Turns', ...
                          'Ratio','Gain','Time','Threshold','SampleTime', ...
                          'InitialState','SwitchStatus','FaultA','FaultB', ...
                          'FaultC','GroundFault','FaultResistance','Before', ...
                          'After','Noise','Saturation','Flux','Winding', ...
                          'RatedPower','NominalVoltage','MagnetizingCurrent', ...
                          'CoreLoss','LeakageInductance','OpenCircuit'};

    for bi = 1:numel(allBlocks)
        blk      = allBlocks{bi};
        bType    = get_param(blk, 'BlockType');
        libLink  = safeGet(blk, 'ReferenceBlock');
        shortBlk = strrep(blk, [modelName '/'], '');

        fprintf(fidTxt, '\n  ┌─ %s\n', shortBlk);
        fprintf(fidTxt,   '  │  Type     : %s\n', bType);
        if ~isempty(libLink)
            fprintf(fidTxt, '  │  Library  : %s\n', libLink);
        end

        % Get all dialog parameters
        try
            params = get_param(blk, 'DialogParameters');
        catch
            params = [];
        end

        if ~isempty(params)
            fNames = fieldnames(params);
            printedAny = false;

            % First pass: electrically significant params
            fprintf(fidTxt, '  │  Parameters:\n');
            for pi = 1:numel(fNames)
                pName = fNames{pi};
                pVal  = safeGetParam(blk, pName);
                if isempty(pVal), continue; end

                % Flag if this is an electrically significant parameter
                isElec = any(cellfun(@(k) ~isempty(regexpi(pName, k, 'once')), ...
                             electricalKeywords));
                marker = '';
                if isElec, marker = '  ◄'; end

                fprintf(fidTxt, '  │    %-35s = %s%s\n', pName, pVal, marker);
                fprintf(fidCsv, '"%s","%s","%s","%s","%s"\n', ...
                        escCsv(blk), escCsv(bType), escCsv(libLink), ...
                        escCsv(pName), escCsv(pVal));
                printedAny = true;
            end
            if ~printedAny
                fprintf(fidTxt, '  │    [no printable parameters]\n');
            end
        else
            fprintf(fidTxt, '  │  [no dialog parameters]\n');
        end

        % Port info
        try
            portHandles = get_param(blk, 'PortHandles');
            pFields     = fieldnames(portHandles);
            portSummary = '';
            for pf = 1:numel(pFields)
                n = numel(portHandles.(pFields{pf}));
                if n > 0
                    portSummary = [portSummary sprintf('%s×%d ', pFields{pf}, n)]; %#ok<AGROW>
                end
            end
            if ~isempty(portSummary)
                fprintf(fidTxt, '  │  Ports     : %s\n', strtrim(portSummary));
            end
        catch, end

        fprintf(fidTxt, '  └─\n');
    end

    % =========================================================================
    % SECTION 4 — SIGNAL LINE CONNECTIVITY (NETLIST)
    % =========================================================================
    hdr(fidTxt, '4. SIGNAL LINE CONNECTIVITY');
    fprintf(fidTxt, '  %-55s  %-55s  %s\n', 'SOURCE (block:port)', 'DESTINATION (block:port)', 'Signal Name');
    fprintf(fidTxt, '  %s\n', repmat('-', 1, 140));

    % Iterate every line in the model (including inside subsystems)
    allLineHandles = find_system(modelName, 'FindAll','on', 'Type','line');

    for li = 1:numel(allLineHandles)
        lh = allLineHandles(li);
        try
            srcPort  = get(lh, 'SrcPortHandle');
            dstPorts = get(lh, 'DstPortHandles');
            sigName  = get(lh, 'Name');
            if isempty(sigName), sigName = '(unnamed)'; end

            srcStr = portStr(srcPort);

            for di = 1:numel(dstPorts)
                dstStr = portStr(dstPorts(di));
                fprintf(fidTxt, '  %-55s  %-55s  %s\n', srcStr, dstStr, sigName);
            end
        catch
            % Some line handles are invalid or virtual — skip
        end
    end

    % =========================================================================
    % SECTION 5 — BUS & GOTO/FROM CONNECTIONS
    % =========================================================================
    hdr(fidTxt, '5. BUS CREATOR / SELECTOR  &  GOTO / FROM CONNECTIONS');

    % Bus creators
    busCreators = find_system(modelName, 'BlockType', 'BusCreator');
    busSelectors= find_system(modelName, 'BlockType', 'BusSelector');
    gotos       = find_system(modelName, 'BlockType', 'Goto');
    froms       = find_system(modelName, 'BlockType', 'From');

    fprintf(fidTxt, '\n  Bus Creators  : %d\n', numel(busCreators));
    for i = 1:numel(busCreators)
        fprintf(fidTxt, '    %s\n', strrep(busCreators{i},[modelName '/'],''));
    end

    fprintf(fidTxt, '\n  Bus Selectors : %d\n', numel(busSelectors));
    for i = 1:numel(busSelectors)
        sig = safeGetParam(busSelectors{i}, 'OutputSignals');
        fprintf(fidTxt, '    %-50s  signals: %s\n', ...
                strrep(busSelectors{i},[modelName '/'],''), sig);
    end

    fprintf(fidTxt, '\n  Goto/From pairs:\n');
    fprintf(fidTxt, '  %-40s  Tag\n', 'Block');
    fprintf(fidTxt, '  %s\n', repmat('-',1,70));
    for i = 1:numel(gotos)
        tag = safeGetParam(gotos{i}, 'GotoTag');
        fprintf(fidTxt, '  GOTO  %-35s  [%s]\n', ...
                strrep(gotos{i},[modelName '/'],''), tag);
    end
    for i = 1:numel(froms)
        tag = safeGetParam(froms{i}, 'GotoTag');
        fprintf(fidTxt, '  FROM  %-35s  [%s]\n', ...
                strrep(froms{i},[modelName '/'],''), tag);
    end

    % =========================================================================
    % SECTION 6 — STEP / FAULT BLOCK QUICK-REFERENCE TABLE
    % =========================================================================
    hdr(fidTxt, '6. STEP & FAULT BLOCKS  (quick-reference for ControlPanel scripts)');

    stepBlocks = find_system(modelName, 'BlockType', 'Step');
    fprintf(fidTxt, '\n  %-45s  Before  After  Time\n', 'Step Block');
    fprintf(fidTxt, '  %s\n', repmat('-',1,80));
    for i = 1:numel(stepBlocks)
        bef  = safeGetParam(stepBlocks{i}, 'Before');
        aft  = safeGetParam(stepBlocks{i}, 'After');
        t    = safeGetParam(stepBlocks{i}, 'Time');
        fprintf(fidTxt, '  %-45s  %-6s  %-5s  %s\n', ...
                strrep(stepBlocks{i},[modelName '/'],''), bef, aft, t);
    end

    % Three-Phase Fault blocks
    faultBlocks = [
        find_system(modelName, 'BlockType', 'ThreePhaseFault'); ...
        find_system(modelName, 'RegExp','on', 'Name','.*[Ff]ault.*', 'BlockType','SubSystem'); ...
        find_system(modelName, 'RegExp','on', 'MaskType','Three-Phase Fault')
    ];
    faultBlocks = unique(faultBlocks);

    if ~isempty(faultBlocks)
        fprintf(fidTxt, '\n  %-45s  FaultA  FaultB  FaultC  FaultG  Rf\n', 'Fault Block');
        fprintf(fidTxt, '  %s\n', repmat('-',1,100));
        for i = 1:numel(faultBlocks)
            fA = safeGetParam(faultBlocks{i}, 'FaultA');
            fB = safeGetParam(faultBlocks{i}, 'FaultB');
            fC = safeGetParam(faultBlocks{i}, 'FaultC');
            fG = safeGetParam(faultBlocks{i}, 'GroundFault');
            rf = safeGetParam(faultBlocks{i}, 'FaultResistance');
            fprintf(fidTxt, '  %-45s  %-6s  %-6s  %-6s  %-6s  %s\n', ...
                    strrep(faultBlocks{i},[modelName '/'],''), fA, fB, fC, fG, rf);
        end
    end

    % =========================================================================
    % SECTION 7 — BREAKER BLOCKS
    % =========================================================================
    hdr(fidTxt, '7. CIRCUIT BREAKERS');

    breakerTypes = {'ThreePhaseBreaker','Breaker','Three-Phase Breaker'};
    bkrs = {};
    for bt = breakerTypes
        bkrs = [bkrs; find_system(modelName,'BlockType',bt{1})]; %#ok<AGROW>
        bkrs = [bkrs; find_system(modelName,'MaskType',bt{1})];  %#ok<AGROW>
    end
    bkrs = unique(bkrs);

    fprintf(fidTxt, '\n  %-45s  InitialState  SwitchingTimes\n', 'Breaker Block');
    fprintf(fidTxt, '  %s\n', repmat('-',1,90));
    for i = 1:numel(bkrs)
        ist = safeGetParam(bkrs{i}, 'InitialState');
        if isempty(ist), ist = safeGetParam(bkrs{i},'SwitchStatus'); end
        swt = safeGetParam(bkrs{i}, 'SwitchingTimes');
        fprintf(fidTxt, '  %-45s  %-12s  %s\n', ...
                strrep(bkrs{i},[modelName '/'],''), ist, swt);
    end

    % =========================================================================
    % SECTION 8 — TRANSFORMER BLOCKS
    % =========================================================================
    hdr(fidTxt, '8. TRANSFORMER BLOCKS');

    xfmrKeys = {'Transformer','transformer','Linear Transformer','Saturable Transformer'};
    xfmrs = {};
    for xk = xfmrKeys
        xfmrs = [xfmrs; find_system(modelName,'RegExp','on','MaskType',xk{1})]; %#ok<AGROW>
        xfmrs = [xfmrs; find_system(modelName,'RegExp','on','Name',['.*' xk{1} '.*'],'BlockType','SubSystem')]; %#ok<AGROW>
    end
    xfmrs = unique(xfmrs);

    xfmrParams = {'NominalPower','Frequency','Winding1','Winding2','Winding3', ...
                  'Rm','Lm','R1','L1','R2','L2','Winding1Connection', ...
                  'Winding2Connection','CoreType','SaturationCharacteristic'};
    for i = 1:numel(xfmrs)
        shortName = strrep(xfmrs{i},[modelName '/'],'');
        fprintf(fidTxt, '\n  %s\n', shortName);
        for pk = xfmrParams
            v = safeGetParam(xfmrs{i}, pk{1});
            if ~isempty(v)
                fprintf(fidTxt, '    %-35s = %s\n', pk{1}, v);
            end
        end
    end

    % =========================================================================
    % SECTION 9 — MEASUREMENT & OUTPUT BLOCKS
    % =========================================================================
    hdr(fidTxt, '9. MEASUREMENT & OUTPUT BLOCKS');

    measTypes = {'ToWorkspace','Scope','CurrentMeasurement','VoltageMeasurement', ...
                 'Outport','Out1'};
    for mt = measTypes
        blks = find_system(modelName, 'BlockType', mt{1});
        if isempty(blks), continue; end
        fprintf(fidTxt, '\n  %s  (%d)\n', mt{1}, numel(blks));
        for i = 1:numel(blks)
            vn = safeGetParam(blks{i}, 'VariableName');
            if isempty(vn), vn = safeGetParam(blks{i},'ScopeSpecificationString'); end
            if isempty(vn), vn = ''; end
            fprintf(fidTxt, '    %-50s  %s\n', ...
                    strrep(blks{i},[modelName '/'],''), vn);
        end
    end

    % =========================================================================
    % SECTION 10 — SUBSYSTEM INTERFACE SUMMARY
    % =========================================================================
    hdr(fidTxt, '10. SUBSYSTEM PORT INTERFACE');

    % Only top-level subsystems (one level deep)
    topSubs = find_system(modelName, 'SearchDepth', 1, 'BlockType', 'SubSystem');
    topSubs = topSubs(~strcmp(topSubs, modelName));

    for si = 1:numel(topSubs)
        ss = topSubs{si};
        shortSS = strrep(ss, [modelName '/'], '');
        inPorts  = find_system(ss, 'SearchDepth',1, 'BlockType','Inport');
        outPorts = find_system(ss, 'SearchDepth',1, 'BlockType','Outport');
        fprintf(fidTxt, '\n  [%s]  Inputs: %d  Outputs: %d\n', ...
                shortSS, numel(inPorts), numel(outPorts));
        for p = inPorts'
            pName = safeGetParam(p{1}, 'Name');
            fprintf(fidTxt, '    IN   %s\n', strrep(p{1}, [ss '/'], ''));
            if ~isempty(pName) && ~strcmp(pName, strrep(p{1},[ss '/'],''))
                fprintf(fidTxt, '         (%s)\n', pName);
            end
        end
        for p = outPorts'
            fprintf(fidTxt, '    OUT  %s\n', strrep(p{1}, [ss '/'], ''));
        end
    end

    % =========================================================================
    % CLOSE FILES & REPORT
    % =========================================================================
    fclose(fidTxt);
    fclose(fidCsv);

    fprintf('\n╔══════════════════════════════════════════════════════════╗\n');
    fprintf('║              NETLIST GENERATION COMPLETE                ║\n');
    fprintf('╚══════════════════════════════════════════════════════════╝\n');
    fprintf('  Model    : %s\n', modelName);
    fprintf('  Blocks   : %d\n', numel(allBlocks));
    fprintf('  Lines    : %d\n', numel(allLineHandles));
    fprintf('  Text log : %s\n', txtFile);
    fprintf('  CSV log  : %s\n', csvFile);
    fprintf('\n  Open the .txt file for the full annotated netlist.\n');
    fprintf('  Open the .csv file in Excel for sortable parameter view.\n\n');
end

% =========================================================================
% HELPER — print section header
% =========================================================================
function hdr(fid, title)
    fprintf(fid, '\n');
    fprintf(fid, '╔%s╗\n', repmat('═', 1, numel(title)+2));
    fprintf(fid, '║ %s ║\n', title);
    fprintf(fid, '╚%s╝\n', repmat('═', 1, numel(title)+2));
    fprintf(fid, '\n');
end

% =========================================================================
% HELPER — recursive block hierarchy printer
% =========================================================================
function printHierarchy(fid, modelName, parent, depth)
    indent = repmat('  ', 1, depth);
    children = find_system(parent, 'SearchDepth', 1, 'Type', 'block');
    % Remove parent itself
    children = children(~strcmp(children, parent));

    for i = 1:numel(children)
        blk   = children{i};
        bType = get_param(blk, 'BlockType');
        short = strrep(blk, [parent '/'], '');
        fprintf(fid, '%s├─ [%-25s] %s\n', indent, bType, short);
        if strcmp(bType, 'SubSystem')
            try
                printHierarchy(fid, modelName, blk, depth+1);
            catch
                fprintf(fid, '%s  (could not recurse into subsystem)\n', indent);
            end
        end
    end
end

% =========================================================================
% HELPER — safe get_param (returns '' on error)
% =========================================================================
function val = safeGetParam(blk, param)
    try
        raw = get_param(blk, param);
        if ischar(raw)
            val = strtrim(raw);
        elseif isnumeric(raw)
            val = mat2str(raw, 6);
        elseif islogical(raw)
            if raw, val = 'true'; else, val = 'false'; end
        elseif iscell(raw)
            val = strjoin(cellfun(@num2str, raw, 'UniformOutput', false), ', ');
        else
            val = class(raw);
        end
    catch
        val = '';
    end
end

% =========================================================================
% HELPER — safe get on handle-graphics object
% =========================================================================
function val = safeGet(blk, prop)
    try
        val = get_param(blk, prop);
        if ~ischar(val), val = ''; end
    catch
        val = '';
    end
end

% =========================================================================
% HELPER — port handle → "BlockName:PortType#N" string
% =========================================================================
function s = portStr(ph)
    if ph <= 0
        s = '(none)';
        return;
    end
    try
        parent   = get(ph, 'Parent');
        portType = get(ph, 'PortType');
        portNum  = get(ph, 'PortNumber');
        shortP   = regexprep(parent, '^[^/]+/', '');
        s = sprintf('%s:%s%d', shortP, portType, portNum);
    catch
        s = '(invalid handle)';
    end
end

% =========================================================================
% HELPER — escape double-quotes for CSV
% =========================================================================
function s = escCsv(val)
    if isempty(val), s = ''; return; end
    s = strrep(val, '"', '""');
end
