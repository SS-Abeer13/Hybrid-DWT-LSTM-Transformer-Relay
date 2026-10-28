for p = {'A','B'}
    for t = {'AB','BC','AC','ABC','AG'}
        f = sprintf('hiz_sweep_v5_%s_%s.mat', p{1}, t{1});
        if isfile(f), fprintf('skip %s\n', f); continue; end
        hiz_sensitivity_sweep_v5(p{1}, t{1});
    end
end
disp('HIZ_V5_DONE');
