% Run remaining HiZ sweeps on TransformerWithCTSaturation_v4
warning('off', 'all');
remTypes = {'BC', 'AC', 'ABC', 'AG'};
for i = 1:numel(remTypes)
    t = remTypes{i};
    fprintf('\n=== Starting HiZ sweep for %s ===\n', t);
    try
        hiz_sensitivity_sweep_v4(t);
        fprintf('=== Completed HiZ sweep for %s ===\n', t);
    catch err
        fprintf('Error running HiZ sweep for %s: %s\n', t, err.message);
    end
end
fprintf('\nAll remaining HiZ sweeps finished.\n');
