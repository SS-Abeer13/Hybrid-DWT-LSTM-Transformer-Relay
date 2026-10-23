function fix_lstm_input_plant_idiff(saveChanges)
%FIX_LSTM_INPUT_PLANT_IDIFF Feed the LSTM the plant-compensated differential (run 20261020_v2_plant).
%
% WHY: on healthy traces this plant obeys  LV_amps = (1/sqrt3)*[1 0 -1; -1 1 0; 0 -1 1] * HV_amps
% (raw CT amps, no per-unit scaling). The raw Ip - Is the LSTM used to see therefore carries a
% load-proportional "differential" (~51 % of load) and the model false-tripped on external faults
% and inrush. The new model was trained on  d = Is - Ip*M_Yd1  (features12.plant_compensated_diff):
% healthy residual ~2.5 % of load.
%
% WHAT: adds Gain 'Yd1_plant_map' = (1/sqrt(3))*[1 0 -1; -1 1 0; 0 -1 1] (Matrix K*u) on the
% primary vector (Mux) and makes 'I_diff_LSTM' = Yd1_plant_map(Ip) - Is. Sign is irrelevant
% (features use squares and magnitudes). The conventional 87T path (Yd1 Compensation, Idiff_rms,
% high-set) is NOT touched.
%
%   fix_lstm_input_plant_idiff        % apply to the loaded model only
%   fix_lstm_input_plant_idiff(true)  % apply and save
% Then run verify_lstm_feature_parity_plant.

if nargin < 1, saveChanges = false; end
model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
if ~bdIsLoaded(model), load_system(fullfile(thisDir, [model '.slx'])); end
relay = [model '/Hybrid 87T Relay'];

if getSimulinkBlockHandle([relay '/I_diff_LSTM']) == -1
    fix_lstm_input_raw_idiff(false);          % builds I_diff_LSTM = Mux - Mux1 first
end

K = '(1/sqrt(3))*[1 0 -1; -1 1 0; 0 -1 1]';
g = [relay '/Yd1_plant_map'];
if getSimulinkBlockHandle(g) == -1
    pos = get_param([relay '/I_diff_LSTM'], 'Position');
    add_block('simulink/Math Operations/Gain', g, 'Position', pos + [-120 -10 -60 -10]);
    add_line(relay, 'Mux/1', 'Yd1_plant_map/1', 'autorouting', 'on');
end
set_param(g, 'Gain', K, 'Multiplication', 'Matrix(K*u)');
connectTo(relay, 'Yd1_plant_map/1', 'I_diff_LSTM', 1);     % replaces Mux -> I_diff_LSTM/1 only

% ---- assertions: wiring is exactly as intended and the 87T path is intact -------------------
pc = get_param([relay '/I_diff_LSTM'], 'PortConnectivity');
assert(strcmp(get_param(pc(1).SrcBlock, 'Name'), 'Yd1_plant_map'), 'I_diff_LSTM input 1 is not Yd1_plant_map');
assert(strcmp(get_param(pc(2).SrcBlock, 'Name'), 'Mux1'), 'I_diff_LSTM input 2 is not Mux1 (secondary)');
pg = get_param(g, 'PortConnectivity');
assert(strcmp(get_param(pg(1).SrcBlock, 'Name'), 'Mux'), 'Yd1_plant_map is not fed by Mux (primary)');
pr = get_param([relay '/Reshape 1'], 'PortConnectivity');
assert(strcmp(get_param(pr(1).SrcBlock, 'Name'), 'I_diff_LSTM'), 'Reshape 1 is not fed by I_diff_LSTM');
py = get_param([relay '/Yd1 Compensation'], 'PortConnectivity');
assert(strcmp(get_param(py(1).SrcBlock, 'Name'), 'Mux') && strcmp(get_param(py(2).SrcBlock, 'Name'), 'Mux1'), ...
    '87T Yd1 Compensation inputs changed');
pa = get_param([relay '/Abs2'], 'PortConnectivity');
assert(strcmp(get_param(pa(1).SrcBlock, 'Name'), 'I_diff'), '87T path broken: Abs2 no longer fed by I_diff');
fprintf('Wiring OK: I_diff_LSTM = Yd1_plant_map(primary) - secondary -> Reshape 1 -> ZOH -> window -> DWT. 87T path intact.\n');

if saveChanges
    save_system(model);
    fprintf('Saved %s.\n', model);
else
    fprintf('Applied to the loaded model only (not saved).\n');
end
end

function connectTo(sys, src, dstBlock, dstPort)
% Remove ONLY the connection into dstBlock/dstPort (deleting the line handle would also delete
% its branches), then connect src -> dstBlock/dstPort.
dst = sprintf('%s/%d', dstBlock, dstPort);
pc = get_param([sys '/' dstBlock], 'PortConnectivity');
oldSrc = pc(dstPort).SrcBlock;
if ~isempty(oldSrc) && oldSrc ~= -1
    oldSrcPort = sprintf('%s/%d', get_param(oldSrc, 'Name'), pc(dstPort).SrcPort + 1);
    if strcmp(oldSrcPort, src), return; end
    delete_line(sys, oldSrcPort, dst);
end
add_line(sys, src, dst, 'autorouting', 'on');
end
