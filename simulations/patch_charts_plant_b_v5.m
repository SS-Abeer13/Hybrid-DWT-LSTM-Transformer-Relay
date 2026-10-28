function patch_charts_plant_b_v5()
%PATCH_CHARTS_PLANT_B_V5 Put the plant-B v5 calibration into the two chart scripts of TransformerB_v5.slx (V8 option (a), 2026-10-28).
%
% v4 plant B: Yd1_Compensation used I_nom = 0.8232 A and ratios 202.0119 / 808.8849 although 40 MVA / (sqrt(3) 132 kV) / 202.0119 = 0.8661 A, and
% DWT_Feature_Extraction normalised by 1.8610 A (the plant-A base). v5 plant B (plant_v5_checks_B.txt): ratios HV 201.98, LV 808.58; rated secondary
% HV 0.8662 A, LV 0.8655 A -> base 0.8658 A in both charts.
% Only these constants are changed; the file is reloaded and the new scripts are asserted after saving.
thisDir = fileparts(mfilename('fullpath')); m = 'TransformerB_v5'; f = fullfile(thisDir, [m '.slx']);
bdclose('all'); load_system(f);
rt = sfroot;
chs = rt.find('-isa', 'Stateflow.EMChart');
chs = chs(arrayfun(@(c) startsWith(c.Path, [m '/']), chs));
RAT = {'CT_Ratio_HV = 202.0119;', 'CT_Ratio_HV = 201.98;'; 'CT_Ratio_LV = 808.8849;', 'CT_Ratio_LV = 808.58;'; ...
       '% 4. Rated secondary currents = 1.0 pu bases (Mean: 0.8232 A)', '% 4. Rated secondary currents = 1.0 pu bases (v5: HV 0.8662 A / LV 0.8655 A, mean 0.8658 A)'; ...
       'I_nom = 0.8232;', 'I_nom = 0.8658;'; ...
       '% Calibrated: 2026-10-27 from probe_ct_truth_plant_b.m', '% Calibrated: 2026-10-28 (v5 plant) from check_plant_physics_v5.m'};
DWT = {'I_base = 1.8610; % rated CT-secondary base current for v4 (probe_ct_truth_v4.m)', 'I_base = 0.8658; % rated CT-secondary base current of plant B v5 (plant_v5_checks_B.txt)'; ...
       'using rated secondary current (1.8610 A)', 'using rated secondary current (0.8658 A)'};
done = 0;
for k = 1:numel(chs)
    s = chs(k).Script;
    if contains(s, 'function [I_hv_comp_pu, I_lv_comp_pu] = Yd1_Compensation'), R = RAT;
    elseif contains(s, 'function features = DWT_Feature_Extraction'), R = DWT;
    else, continue; end
    for j = 1:size(R, 1)
        assert(contains(s, R{j, 1}), 'pattern not found in %s: %s', chs(k).Path, R{j, 1});
        s = strrep(s, R{j, 1}, R{j, 2});
    end
    chs(k).Script = s; done = done + 1;
end
assert(done == 2, 'expected to patch 2 charts, patched %d', done);
save_system(m); close_system(m, 0);
% ---- verify the saved file
load_system(f); rt = sfroot; chs = rt.find('-isa', 'Stateflow.EMChart'); chs = chs(arrayfun(@(c) startsWith(c.Path, [m '/']), chs));
n = 0;
for k = 1:numel(chs)
    s = chs(k).Script;
    if contains(s, 'Yd1_Compensation'), assert(contains(s, 'I_nom = 0.8658;') && contains(s, 'CT_Ratio_LV = 808.58;') && ~contains(s, '0.8232;')); n = n + 1;
    elseif contains(s, 'DWT_Feature_Extraction'), assert(contains(s, 'I_base = 0.8658;') && ~contains(s, '1.8610;')); n = n + 1; end
end
assert(n == 2); assert(strcmp(get_param(fb(m, 'Three-Phase Breaker'), 'SwitchTimes'), '[]'), 'breaker settings changed');
close_system(m, 0);
fprintf('%s chart scripts patched and verified (I_base 0.8658 A, ratios 201.98 / 808.58)\n', m);
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
