% simulate_all_and_extract_features.m
% Configure scenarios, run 1.0s simulations, log DWT features, and save for Python evaluation.

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    subsys = [model '/Hybrid 87T Relay'];
    lstm_path = [subsys '/LSTM Predict'];
    term_path = [subsys '/Terminator_LSTM'];
    
    % 1. Ensure LSTM Predict block is bypassed to prevent MATLAB heap corruption
    if getSimulinkBlockHandle(lstm_path) ~= -1
        fprintf('Bypassing LSTM Predict block to prevent native crash...\n');
        ph_l = get_param(lstm_path, 'PortHandles');
        line_in = get_param(ph_l.Inport(1), 'Line');
        if line_in ~= -1, delete_line(line_in); end
        line_out = get_param(ph_l.Outport(1), 'Line');
        if line_out ~= -1, delete_line(line_out); end
        delete_block(lstm_path);
    end
    
    % Add Terminator block for Feature Window output if not present
    if getSimulinkBlockHandle(term_path) == -1
        fprintf('Adding Terminator block...\n');
        add_block('built-in/Terminator', term_path);
        add_line(subsys, 'Feature Window/1', 'Terminator_LSTM/1');
    end
    
    % Enable signal logging on Feature Window output port
    fprintf('Enabling signal logging on Feature Window...\n');
    ph_fw = get_param([subsys '/Feature Window'], 'PortHandles');
    set_param(ph_fw.Outport(1), 'DataLogging', 'on');
    set_param(ph_fw.Outport(1), 'DataLoggingNameMode', 'Custom');
    set_param(ph_fw.Outport(1), 'DataLoggingName', 'DWT_Features');

    % NOTE on the trip decision:
    % The model already logs 'Idiff_rms', 'Irest_rms' and 'TripSignal' to logsout.
    % Because the LSTM Predict block was removed, the relay's own TripSignal is
    % gated by the now-unconnected Manual Switch and cannot be trusted. We
    % therefore recompute the conventional 87T trip OFFLINE from the logged
    % differential/restraint currents, using the thesis dual-slope settings
    % (see plotting/plot_percentage_restraint_slope.m).
    RELAY.I_pickup = 0.30;  % Minimum pickup current (A, secondary)
    RELAY.I_knee1  = 3.0;   % First knee point (A) (breakpoint = 3.0 pu)
    RELAY.S1       = 0.25;  % Slope 1 (25%)
    RELAY.S2       = 0.60;  % Slope 2 (60%)
    RELAY.dwell_s  = 0.005; % Operate must persist this long to declare a trip

    % Save model changes
    save_system(model);
    fprintf('✓ Model prepared and saved.\n\n');
    
    % Define Test Scenarios (aligned with 1600 Hz training dataset)
    % Columns: Name | ScenarioType | fA | fB | fC | fG | Rf | t_fault | shouldTrip
    test_cases = { ...
        'Normal Operation',   'Normal',   0,  0,  0,  0,  0.0,  0.00,    false; ...
        'Magnetizing Inrush', 'Inrush',   0,  0,  0,  0,  0.0,  0.05,    false; ...
        'Internal A-G Fault', 'Internal', 1,  0,  0,  1,  0.1,  0.50,    true;  ...
        'External 3Φ Fault',  'External', 1,  1,  1,  0,  0.1,  0.50,    false  ...
    };
    
    simulated_data = struct();
    trip_summary   = struct();   % lightweight: currents + decisions only (no feature cubes)
    T_STOP = 1.0;                % simulation stop time (s), used to rebuild a seconds time base

    fprintf('Starting simulations...\n');
    for k = 1:size(test_cases, 1)
        name = test_cases{k, 1};
        type = test_cases{k, 2};
        fA = test_cases{k, 3}; fB = test_cases{k, 4}; fC = test_cases{k, 5}; fG = test_cases{k, 6};
        Rf = test_cases{k, 7}; t_fault = test_cases{k, 8}; shouldTrip = test_cases{k, 9};
        
        fprintf('  Simulating Case %d/4: %s...\n', k, name);
        resetFaultBlocks(model);
        
        if strcmp(type, 'Inrush')
            setInrushEnergization(model);
        else
            setBreakersClosed(model);
            if strcmp(type, 'Internal')
                set_param([model '/Step3'], 'Time', num2str(t_fault, '%.6f'));
                set_param([model '/Internal_Fault1'], ...
                    'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                    'FaultResistance', num2str(Rf, '%.6f'));
            elseif strcmp(type, 'External')
                set_param([model '/Step4'], 'Time', num2str(t_fault, '%.6f'));
                set_param([model '/External_Fault'], ...
                    'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                    'FaultResistance', num2str(Rf, '%.6f'));
            end
        end
        
        % Run 1.0s simulation
        simOut = sim(model, 'StopTime', '1.0', 'ReturnWorkspaceOutputs', 'on');
        
        % Extract logged features
        logs = simOut.get('logsout');
        feat_el = logs.get('DWT_Features');
        if isempty(feat_el)
            error('DWT_Features signal was not logged! Check configuration.');
        end
        
        % One-time diagnostic: show exactly what is available to log from.
        if k == 1
            try
                fprintf('    [diag] logsout elements: %s\n', strjoin(cellstr(logs.getElementNames()).', ', '));
            catch, end
            try
                fprintf('    [diag] simOut variables: %s\n', strjoin(cellstr(simOut.who).', ', '));
            catch, end
        end

        % ---- Conventional 87T trip, recomputed from logged Idiff/Irest ----
        % Pull the differential and restraint currents (already logged).
        [idiff_t, idiff] = getLog(logs, 'Idiff_rms');
        [irest_t, irest] = getLog(logs, 'Irest_rms');
        if isempty(idiff_t), idiff_t = irest_t; end
        trip_time = idiff_t;

        % Dual-slope percentage-restraint operate boundary.
        tripped_conventional = false;
        trip_time_s = NaN;
        trip_data = [];
        thresh = [];
        trip_source = 'computed:87T_dualslope';
        if ~isempty(idiff) && ~isempty(irest)
            idiff = double(idiff(:));
            irest = double(irest(:));
            n = min(numel(idiff), numel(irest));
            idiff = idiff(1:n); irest = irest(1:n);
            % Build a time base in SECONDS. Prefer the logged time vector; if its
            % length does not match the data, reconstruct it from the stop time.
            tt = trip_time(:);
            if numel(tt) ~= n || isempty(tt) || any(~isfinite(tt))
                tt = linspace(0, T_STOP, n).';
            end
            trip_time = tt;

            thresh = RELAY.I_pickup * ones(n,1);
            m = irest >= RELAY.I_pickup & irest < RELAY.I_knee1;
            thresh(m) = RELAY.I_pickup + RELAY.S1 * (irest(m) - RELAY.I_pickup);
            m = irest >= RELAY.I_knee1;
            thresh(m) = RELAY.I_pickup + RELAY.S1*(RELAY.I_knee1 - RELAY.I_pickup) ...
                        + RELAY.S2*(irest(m) - RELAY.I_knee1);

            operate = idiff > thresh;              % instantaneous operate flag
            trip_data = double(operate);

            % Require the operate condition to persist for RELAY.dwell_s (security).
            if any(operate)
                dt = median(diff(tt)); if ~isfinite(dt) || dt <= 0, dt = 1/1600; end
                need = max(1, round(RELAY.dwell_s / dt));
                run = 0;
                for ii = 1:n
                    if operate(ii)
                        run = run + 1;
                        if run >= need
                            tripped_conventional = true;
                            trip_time_s = tt(ii - need + 1);
                            break;
                        end
                    else
                        run = 0;
                    end
                end
            end
        end

        % Model's own TripSignal, kept only as a (currently unreliable) reference.
        [~, trip_model] = getLog(logs, 'TripSignal');
        if isempty(trip_model), [~, trip_model] = getLog(logs, 'Dec_Trip_Signal'); end

        sanitized_name = regexprep(name, '[^a-zA-Z0-9]', '_');
        sanitized_name = regexprep(sanitized_name, '_+', '_'); % collapse multiple underscores
        sanitized_name = regexprep(sanitized_name, '_$', '');  % strip trailing underscore
        simulated_data.(sanitized_name).features = feat_el.Values.Data;
        simulated_data.(sanitized_name).time = feat_el.Values.Time;
        simulated_data.(sanitized_name).shouldTrip = shouldTrip;
        simulated_data.(sanitized_name).trippedConventional = tripped_conventional;
        simulated_data.(sanitized_name).tripSignal = trip_data;        % instantaneous operate flag
        simulated_data.(sanitized_name).tripTime = trip_time;
        simulated_data.(sanitized_name).tripTimeFirst = trip_time_s;
        simulated_data.(sanitized_name).tripSource = trip_source;
        simulated_data.(sanitized_name).idiffRms = idiff;              % differential current (A)
        simulated_data.(sanitized_name).irestRms = irest;              % restraint current (A)
        simulated_data.(sanitized_name).tripThreshold = thresh;        % dual-slope operate boundary (A)
        simulated_data.(sanitized_name).relaySettings = RELAY;         % pickup/knee/slopes/dwell
        simulated_data.(sanitized_name).tripSignalModel = trip_model;  % model's own (unreliable) trip, for reference
        idiff_pk = 0; if ~isempty(idiff), idiff_pk = max(idiff); end

        % ---- Lightweight trip summary (small: currents + decisions, NO feature cubes) ----
        % Saved incrementally after every case so validation never depends on the
        % fragile ~350 MB feature file, and partial results survive an interrupted run.
        TS = struct();
        TS.shouldTrip           = shouldTrip;
        TS.trippedConventional  = tripped_conventional;
        TS.tripTimeFirst        = trip_time_s;
        TS.tripSource           = trip_source;
        TS.idiffRms             = single(idiff);
        TS.irestRms             = single(irest);
        TS.tripThreshold        = single(thresh);
        TS.tripSignal           = uint8(trip_data);   % 0/1 operate flag
        TS.tripTime             = single(trip_time);
        TS.maxIdiff             = idiff_pk;
        TS.maxIrest             = max([0; irest(:)]);
        TS.relaySettings        = RELAY;
        trip_summary.(sanitized_name) = TS;
        save('simulated_trip_summary.mat', '-struct', 'trip_summary');

        fprintf('    ✓ Done. Features: %s | Trip: %d (t=%.4gs) | max Idiff=%.3fA\n', ...
            mat2str(size(feat_el.Values.Data)), tripped_conventional, trip_time_s, idiff_pk);
    end
    fprintf('✓ Lightweight summary written to simulated_trip_summary.mat\n');

    % Save all simulated features for Python evaluation
    save('simulated_test_features.mat', '-struct', 'simulated_data');
    fprintf('\n✓ All cases simulated and features saved to simulated_test_features.mat.\n');
    
catch ME
    disp(['Error: ' ME.message]);
    disp(ME.getReport());
end

% =========================================================================
% UTILITY HELPER FUNCTIONS (Inline definitions)
% =========================================================================
function val = onOff(cond)
    if cond, val = 'on'; else, val = 'off'; end
end

function [t, x] = getLog(logs, name)
    % Robustly fetch a logged signal's (time, data) from a logsout Dataset.
    t = []; x = [];
    try
        el = logs.get(name);
        if ~isempty(el)
            t = el.Values.Time;
            x = double(el.Values.Data);
        end
    catch
    end
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
        residualFlux = [-0.60 0.40 0.15];
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
