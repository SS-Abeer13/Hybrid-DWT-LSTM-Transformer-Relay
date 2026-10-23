function fix_lstm_input_raw_idiff(saveChanges)
%FIX_LSTM_INPUT_RAW_IDIFF Feed the LSTM branch the SAME differential current it was trained on.
%
% ROOT CAUSE of the closed-loop failures (Inrush -> TRIP, External -> TRIP,
% internal fault getting the LOWEST LSTM score):
%   Training  (datasets/extract_12_features.m):  I_diff = Ip - Is
%             raw CT-secondary amps (I_primary_abc - I_secondary_abc), no compensation.
%   Relay     (before this fix): 'I_diff' = Yd1-COMPENSATED, PER-UNIT currents, opposite sign.
%             Yd1 compensation mixes phases, so the DWT sees a different signal.
%
% FIX: add 'I_diff_LSTM' = Mux - Mux1 (relay inputs 1-3 minus 4-6, i.e. exactly the
% signals the two To Workspace blocks log) and route it into 'Reshape 1' -> ZOH ->
% I_diff_window -> DWT. The conventional 87T path (Yd1 compensation, Idiff_rms,
% Irest_rms, high-set) is NOT touched. The DWT chart code is not changed
% (test_hybrid_relay.m writes the 12-feature code).
%
%   fix_lstm_input_raw_idiff        % apply to the loaded model only
%   fix_lstm_input_raw_idiff(true)  % apply and save
% Then run verify_lstm_feature_parity.

if nargin < 1, saveChanges = false; end
model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
if ~bdIsLoaded(model), load_system(fullfile(thisDir, [model '.slx'])); end
relay  = [model '/Hybrid 87T Relay'];
newSum = [relay '/I_diff_LSTM'];

if getSimulinkBlockHandle(newSum) == -1
    pos = get_param([relay '/I_diff'], 'Position');
    add_block('simulink/Math Operations/Sum', newSum, 'Inputs', '+-', ...
        'IconShape', 'rectangular', 'Position', pos + [0 90 0 90]);
end
set_param(newSum, 'Inputs', '+-');
connectTo(relay, 'Mux/1',  'I_diff_LSTM', 1);
connectTo(relay, 'Mux1/1', 'I_diff_LSTM', 2);
connectTo(relay, 'I_diff_LSTM/1', 'Reshape 1', 1);   % replaces the compensated I_diff feed

ph = get_param(newSum, 'PortHandles');
set_param(ph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_LSTM');

% The compensated I_diff must still drive the 87T path, and nothing else may feed the LSTM.
pc = get_param([relay '/Reshape 1'], 'PortConnectivity');   % struct array; inputs are listed first
srcHandle = pc(1).SrcBlock;
assert(~isempty(srcHandle) && srcHandle ~= -1 && strcmp(get_param(srcHandle, 'Name'), 'I_diff_LSTM'), ...
    'Reshape 1 is not fed by I_diff_LSTM');
pcAbs = get_param([relay '/Abs2'], 'PortConnectivity');          % 87T Idiff_rms path
assert(pcAbs(1).SrcBlock ~= -1 && strcmp(get_param(pcAbs(1).SrcBlock, 'Name'), 'I_diff'), ...
    '87T path broken: Abs2 is no longer fed by the compensated I_diff');
assert(strcmp(get_param([relay '/ZOH_1600'], 'SampleTime'), '6.25e-4'));
assert(strcmp(get_param([relay '/I_diff_window'], 'N'), '32'));

if saveChanges
    save_system(model);
    fprintf('Saved %s: LSTM branch now uses raw I_diff = Ip - Is (training definition).\n', model);
else
    fprintf('Applied to the loaded model only (not saved).\n');
end
end

function connectTo(sys, src, dstBlock, dstPort)
% Remove ONLY the connection into dstBlock/dstPort (deleting the line handle
% would also delete its branches, e.g. the compensated I_diff feeding the 87T RMS path).
dst = sprintf('%s/%d', dstBlock, dstPort);
pc = get_param([sys '/' dstBlock], 'PortConnectivity');
oldSrc = pc(dstPort).SrcBlock;
if ~isempty(oldSrc) && oldSrc ~= -1
    oldSrcPort = sprintf('%s/%d', get_param(oldSrc, 'Name'), pc(dstPort).SrcPort + 1);
    if strcmp(oldSrcPort, src), return; end            % already connected as wanted
    delete_line(sys, oldSrcPort, dst);
end
add_line(sys, src, dst, 'autorouting', 'on');
end
