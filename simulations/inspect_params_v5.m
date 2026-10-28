function inspect_params_v5()
%INSPECT_PARAMS_V5 Print the transformer, source-impedance and CT parameters of both v4 plants (read-only; nothing is saved).
models = {'TransformerWithCTSaturation_v4', 'TransformerB_v4'};
thisDir = fileparts(mfilename('fullpath'));
fid = fopen(fullfile(thisDir, 'inspect_params_v5.txt'), 'w');
for mi = 1:numel(models)
    m = models{mi}; load_system(fullfile(thisDir, [m '.slx']));
    fprintf(fid, '=== %s ===\n', m);
    all = find_system(m, 'SearchDepth', 1, 'Type', 'Block');
    nn = @(x) strtrim(regexprep(get_param(x, 'Name'), '\s+', ' '));
    for k = 1:numel(all)
        b = all{k}; n = nn(b);
        if strcmp(n, 'Step_down_Transformer') || strcmp(n, 'Three-Phase Series RLC Branch') || strcmp(n, 'Three-Phase Series RLC Load') || startsWith(n, 'VS')
            fprintf(fid, '[%s] ', n);
            for p = {'NominalPower', 'Winding1', 'Winding2', 'Winding1Connection', 'Winding2Connection', 'Rm', 'Lm', 'Saturation', 'SetSaturation', 'Resistance', 'Inductance', 'Capacitance', 'BranchType', 'Amplitude', 'Frequency', 'NominalVoltage', 'ActivePower'}
                try, fprintf(fid, '%s=%s | ', p{1}, get_param(b, p{1})); catch, end %#ok<NOCOM>
            end
            fprintf(fid, '\n');
        end
    end
    for ctn = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}
        cb = [m '/' ctn{1}];
        try
            kids = find_system(cb, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
            for q = 1:numel(kids)
                n = nn(kids{q});
                if contains(n, 'CT ') || contains(n, 'ohm') || contains(n, 'Burden') || contains(n, 'Saturable')
                    fprintf(fid, '[%s/%s] ', ctn{1}, n);
                    for p = {'NominalPower', 'Winding1', 'Winding2', 'Saturation', 'CoreLoss', 'InitialFlux', 'Resistance', 'Inductance', 'SetSaturation', 'Rm', 'Lm'}
                        try, fprintf(fid, '%s=%s | ', p{1}, get_param(kids{q}, p{1})); catch, end %#ok<NOCOM>
                    end
                    fprintf(fid, '\n');
                end
            end
        catch ME
            fprintf(fid, '[%s] could not inspect: %s\n', ctn{1}, ME.message);
        end
    end
    fprintf(fid, '\n'); close_system(m, 0);
end
fclose(fid); type(fullfile(thisDir, 'inspect_params_v5.txt'));
end
