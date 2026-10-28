% inspect_sources_v4.m
model = 'TransformerWithCTSaturation_v4';
load_system(model);

fprintf('=== Voltage Sources ===\n');
for s = {'VSa', 'VSb', 'VSc'}
    b = [model '/' s{1}];
    try
        p = get_param(b, 'DialogParameters');
        fprintf('Block %s:\n', s{1});
        for fn = fieldnames(p)'
            v = get_param(b, fn{1});
            if ischar(v) || isnumeric(v)
                fprintf('  %s: %s\n', fn{1}, num2str(v));
            end
        end
    catch ME
        fprintf('Error reading %s: %s\n', s{1}, ME.message);
    end
end

fprintf('=== Source Impedance / Series Branch ===\n');
blks = find_system(model, 'SearchDepth', 1, 'Type', 'Block');
for i = 1:length(blks)
    b = blks{i};
    nm = get_param(b, 'Name');
    if contains(nm, 'Series') || contains(nm, 'Source') || contains(nm, 'Branch')
        fprintf('Block: %s\n', nm);
        try
            p = get_param(b, 'DialogParameters');
            for fn = {'BranchType', 'Resistance', 'Inductance', 'Capacitance'}
                if isfield(p, fn{1})
                    fprintf('  %s: %s\n', fn{1}, num2str(get_param(b, fn{1})));
                end
            end
        catch
        end
    end
end

close_system(model, 0);
exit(0);
