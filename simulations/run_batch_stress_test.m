function run_batch_stress_test()
%RUN_BATCH_STRESS_TEST Execute closed-loop hybrid relay co-simulation across all major stress scenario categories.

model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
projectDir = fileparts(thisDir);

addpath(fullfile(projectDir, 'control_panels'));
addpath(fullfile(projectDir, 'datasets'));
addpath(fullfile(projectDir, 'lstm_models'));
addpath(thisDir);

fprintf('===========================================================\n');
fprintf('   CLOSED-LOOP HYBRID RELAY STRESS TEST SUITE            \n');
fprintf('===========================================================\n');
fprintf(' Model: %s\n', model);
fprintf('===========================================================\n\n');

if ~bdIsLoaded(model)
    load_system(fullfile(thisDir, [model '.slx']));
end

repair_hybrid_relay_for_lstm_verification(false);

% Define representative scenario from each category
test_cases = {
    'Normal Operation'      , 'Normal'   , 0, 0, 0, 0, 0.01, 0.00, false;
    'Inrush (No Load)'      , 'Inrush'   , 0, 0, 0, 0, 0.01, 0.05, false;
    'Internal Low-Z (A-G)'  , 'Internal' , 1, 0, 0, 1, 0.01, 0.05, true;
    'Internal Low-Z (3-Ph)' , 'Internal' , 1, 1, 1, 0, 0.01, 0.05, true;
    'Internal High-Z (A-G)' , 'Internal' , 1, 0, 0, 1, 50.0, 0.05, true;
    'Internal Evolving'     , 'Internal' , 1, 0, 0, 1, 0.01, 0.05, true;
    'External Low-Z (A-G)'  , 'External' , 1, 0, 0, 1, 0.01, 0.05, false;
    'External Low-Z (3-Ph)' , 'External' , 1, 1, 1, 0, 0.01, 0.05, false;
    'External High-Z (A-G)' , 'External' , 1, 0, 0, 1, 20.0, 0.05, false;
    'Severe CT Saturation'  , 'Internal' , 1, 0, 0, 1, 0.01, 0.05, true;
};

nCases = size(test_cases, 1);
results = struct();

passed_count = 0;
startTime = tic;

for k = 1:nCases
    cName = test_cases{k, 1};
    cType = test_cases{k, 2};
    fA    = test_cases{k, 3};
    fB    = test_cases{k, 4};
    fC    = test_cases{k, 5};
    fG    = test_cases{k, 6};
    Rf    = test_cases{k, 7};
    tF    = test_cases{k, 8};
    shouldTrip = test_cases{k, 9};

    fprintf('[%2d/%2d] Running %-24s (Exp: %-5s) ... ', k, nCases, cName, iff(shouldTrip, 'TRIP', 'BLOCK'));

    resetFaultBlocks(model);

    if strcmp(cType, 'Inrush')
        setInrushEnergization(model);
    else
        setBreakersClosed(model);
        if strcmp(cType, 'Internal')
            set_param([model '/Step3'], 'Time', num2str(tF, '%.6f'));
            set_param([model '/Internal_Fault1'], ...
                'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                'FaultResistance', num2str(Rf, '%.6f'), ...
                'SwitchTimes', sprintf('[%.6f 1.10]', tF));
        elseif strcmp(cType, 'External')
            set_param([model '/Step4'], 'Time', num2str(tF, '%.6f'));
            set_param([model '/External_Fault'], ...
                'FaultA', onOff(fA), 'FaultB', onOff(fB), 'FaultC', onOff(fC), 'GroundFault', onOff(fG), ...
                'FaultResistance', num2str(Rf, '%.6f'), ...
                'SwitchTimes', sprintf('[%.6f 1.10]', tF));
        end
    end

    try
        simOut = sim(model, 'StopTime', '1.10', 'ReturnWorkspaceOutputs', 'on');
        logs = simOut.get('logsout');

        lstm_prob = 0;
        try
            lstm_el = logs.get('LSTM_Prediction');
            if ~isempty(lstm_el)
                lstm_prob = max(lstm_el.Values.Data);
            end
        catch
        end

        tripped = false;
        try
            trip_el = getFirstLog(logs, {'TripSignal', 'Trip_Signal', 'Dec_Trip_Signal'});
            if ~isempty(trip_el)
                d_vec = trip_el.Values.Data;
                tripped = any(d_vec > 0.5);
            end
        catch
        end

        passed = (tripped == shouldTrip);
        if passed
            passed_count = passed_count + 1;
            statusStr = 'PASS';
        else
            statusStr = 'FAIL';
        end

        fprintf('Act: %-5s | AI Prob: %.4f | %s\n', iff(tripped, 'TRIP', 'BLOCK'), lstm_prob, statusStr);

    catch ME
        fprintf('ERROR: %s\n', ME.message);
    end
end

elapsed = toc(startTime);
fprintf('\n===========================================================\n');
fprintf('   STRESS TEST RESULTS: %d / %d PASSED (%.1f%%) in %.1f s\n', ...
    passed_count, nCases, (passed_count / nCases)*100, elapsed);
fprintf('===========================================================\n');
end

function str = iff(cond, a, b)
    if cond, str = a; else, str = b; end
end

function str = onOff(val)
    if val, str = 'on'; else, str = 'off'; end
end

function setBreakersClosed(model)
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try set_param(hv, 'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]'); catch; end
    try set_param(lv, 'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]'); catch; end
end

function setInrushEnergization(model)
    hv = [model '/Three-Phase Breaker '];
    lv = [model '/Three-Phase Breaker1 '];
    try set_param(hv, 'External', 'off', 'InitialState', 'open', 'SwitchTimes', '[0.050]'); catch; end
    try set_param(lv, 'External', 'on', 'InitialState', 'closed', 'SwitchTimes', '[]'); catch; end
    try set_param([model '/Step_down_Transformer'], 'SetInitialFlux', 'on', 'InitialFluxes', '[-0.60 0.40 0.15]'); catch; end
end

function resetFaultBlocks(model)
    set_param([model '/Step3'], 'Time', '10');
    set_param([model '/Step4'], 'Time', '10');
    try
        set_param([model '/Internal_Fault1'], ...
            'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', ...
            'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
    catch; end
    try
        set_param([model '/External_Fault'], ...
            'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', ...
            'FaultResistance', '0.01', 'SwitchTimes', '[0.05 1]');
    catch; end
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
        catch; end
    end
end
