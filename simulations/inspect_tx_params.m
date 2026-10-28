% inspect_tx_params.m
model = 'TransformerWithCTSaturation_v4';
load_system(model);

tx = [model '/Step_down_Transformer'];
fprintf('=== Transformer Parameters ===\n');
names = fieldnames(get_param(tx, 'DialogParameters'));
for i = 1:length(names)
    p = names{i};
    v = get_param(tx, p);
    if ischar(v) || isnumeric(v)
        fprintf('  %s: %s\n', p, num2str(v));
    end
end

ct1 = [model '/CT1'];
fprintf('=== CT1 Parameters ===\n');
names = fieldnames(get_param(ct1, 'DialogParameters'));
for i = 1:length(names)
    p = names{i};
    v = get_param(ct1, p);
    if ischar(v) || isnumeric(v)
        fprintf('  %s: %s\n', p, num2str(v));
    end
end

% Check inside CT1
blks_ct1 = find_system(ct1, 'Type', 'Block');
for i = 1:length(blks_ct1)
    b = blks_ct1{i};
    fprintf('CT1 Sub-block: %s (%s)\n', get_param(b, 'Name'), get_param(b, 'BlockType'));
    try
        pnames = fieldnames(get_param(b, 'DialogParameters'));
        for j = 1:length(pnames)
            pn = pnames{j};
            pv = get_param(b, pn);
            if ischar(pv) || isnumeric(pv)
                fprintf('    %s: %s\n', pn, num2str(pv));
            end
        end
    catch
    end
end

close_system(model, 0);
exit(0);
