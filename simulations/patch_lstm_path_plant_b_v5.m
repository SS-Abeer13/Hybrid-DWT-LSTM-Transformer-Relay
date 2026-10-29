function patch_lstm_path_plant_b_v5()
%PATCH_LSTM_PATH_PLANT_B_V5 Give the LSTM input path of TransformerB_v5 the Dyn11 plant map (V8 option (a), 2026-10-29).
%
% Found by verify_feature_parity_v5('B') (max error 0.45 / 7.1): in the v4/v5 plant-B model the block 'Yd1_plant_map' (plant-A matrix, Yd1) was applied to the
% HV currents in I_diff_LSTM = K*Ip - Is, while the Python/generator features of plant B use the Dyn11 map on the LV currents (Is*Mpl' - Ip).
% Change (only this): the map block gets (1/sqrt(3))*[1 -1 0; 0 1 -1; -1 0 1] and is fed with the LV currents (Mux1); I_diff_LSTM = Ip - Mpl*Is
% (sign opposite to the Python convention; the 12 features are sign-invariant: log energies and FFT magnitudes).
thisDir = fileparts(mfilename('fullpath')); m = 'TransformerB_v5'; f = fullfile(thisDir, [m '.slx']);
bdclose('all'); load_system(f);
r = [m '/Hybrid 87T Relay'];
assert(strcmp(strtrim(get_param([r '/I_diff_LSTM'], 'Inputs')), '+-'));
delete_line(r, 'Mux/1', 'Yd1_plant_map/1');
delete_line(r, 'Mux1/1', 'I_diff_LSTM/2');
delete_line(r, 'Yd1_plant_map/1', 'I_diff_LSTM/1');
add_line(r, 'Mux1/1', 'Yd1_plant_map/1', 'autorouting', 'on');
add_line(r, 'Yd1_plant_map/1', 'I_diff_LSTM/2', 'autorouting', 'on');
add_line(r, 'Mux/1', 'I_diff_LSTM/1', 'autorouting', 'on');
set_param([r '/Yd1_plant_map'], 'Gain', '(1/sqrt(3))*[1 -1 0; 0 1 -1; -1 0 1]');
save_system(m); close_system(m, 0);
% ---- verify the saved file
load_system(f);
ph = get_param([r '/Yd1_plant_map'], 'PortHandles'); src = get_param(get_param(ph.Inport(1), 'Line'), 'SrcBlockHandle');
assert(strcmp(get_param(src, 'Name'), 'Mux1'), 'map is not fed by Mux1');
ph2 = get_param([r '/I_diff_LSTM'], 'PortHandles');
s1 = get_param(get_param(ph2.Inport(1), 'Line'), 'SrcBlockHandle'); s2 = get_param(get_param(ph2.Inport(2), 'Line'), 'SrcBlockHandle');
assert(strcmp(get_param(s1, 'Name'), 'Mux') && strcmp(get_param(s2, 'Name'), 'Yd1_plant_map'), 'sum wiring wrong');
assert(contains(get_param([r '/Yd1_plant_map'], 'Gain'), '[1 -1 0; 0 1 -1; -1 0 1]'));
assert(strcmp(get_param(fb(m, 'Three-Phase Breaker'), 'SwitchTimes'), '[]'), 'breaker settings changed');
close_system(m, 0);
fprintf('%s: LSTM path now Ip - Dyn11*Is (verified in the saved file)\n', m);
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
