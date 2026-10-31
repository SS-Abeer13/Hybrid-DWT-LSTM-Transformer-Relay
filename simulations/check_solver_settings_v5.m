function check_solver_settings_v5()
%CHECK_SOLVER_SETTINGS_V5 D1 (BENCHMARK_FAIRNESS_PLAN.md Part 2): solver, step, noise and sampling blocks of both v5 plants. Read-only (nothing is saved).
thisDir = fileparts(mfilename('fullpath'));
fid = fopen(fullfile(thisDir, 'solver_settings_v5.txt'), 'w');
for m = {'TransformerWithCTSaturation_v5', 'TransformerB_v5'}
    model = m{1}; bdclose('all'); load_system(fullfile(thisDir, [model '.slx']));
    pr = @(varargin) printBoth(fid, varargin{:});
    pr('==== %s\n', model);
    for p = {'SolverType', 'Solver', 'FixedStep', 'MaxStep', 'MinStep', 'RelTol', 'AbsTol', 'StartTime', 'StopTime', 'SampleTimeColors', 'SaveFormat', 'Decimation', 'LimitDataPoints'}
        try, pr('  %-18s %s\n', p{1}, num2str(get_param(model, p{1}))); catch, end %#ok<NOCOM>
    end
    gui = find_system(model, 'SearchDepth', 1, 'MaskType', 'PSB option menu block');
    for k = 1:numel(gui)
        for p = {'SimulationMode', 'SampleTime', 'SolverType', 'Frequency'}
            try, pr('  powergui %-14s %s\n', p{1}, num2str(get_param(gui{k}, p{1}))); catch, end %#ok<NOCOM>
        end
    end
    % every block whose name or type carries a sample time of interest
    blks = find_system(model, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
    for k = 1:numel(blks)
        b = blks{k}; bt = get_param(b, 'BlockType'); nm = strtrim(regexprep(get_param(b, 'Name'), '\s+', ' '));
        keys = {};
        if any(strcmp(bt, {'ZeroOrderHold', 'RateTransition', 'Quantizer', 'Buffer', 'ToWorkspace', 'DiscreteFilter', 'UnitDelay'})) || contains(nm, 'Band-Limited') || contains(nm, 'ZOH')
            keys = {'SampleTime', 'Ts', 'QuantizationInterval', 'Decimation', 'OutBufferSize', 'Seed', 'Cov', 'NoisePower'};
        end
        if ~isempty(keys)
            s = '';
            for q = 1:numel(keys), try, s = [s sprintf(' %s=%s', keys{q}, num2str(get_param(b, keys{q})))]; catch, end, end %#ok<NOCOM,AGROW>
            pr('  %-32s [%s]%s\n', nm, bt, s);
        end
    end
    close_system(model, 0);
end
fclose(fid);
end
function printBoth(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end
