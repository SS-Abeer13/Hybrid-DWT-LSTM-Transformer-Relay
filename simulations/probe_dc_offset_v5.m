function probe_dc_offset_v5(modelName)
%PROBE_DC_OFFSET_V5 DC offset of an external 3-phase fault current vs inception angle (true LV line current, V-I block). In memory only.
if nargin < 1, modelName = 'TransformerWithCTSaturation_v5'; end
model = modelName; thisDir = fileparts(mfilename('fullpath'));
bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
ph2 = get_param(fb(model, 'Secondary_side'), 'PortHandles'); set_param(ph2.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'SI');
set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
ef = fb(model, 'External_Fault'); set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(fb(model, 'Step4'), 'Time', '0.3', 'Before', '0', 'After', '1');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
for deg = [0 45 90]
    for k = 1:3, set_param(vs{k}, 'Phase', sprintf('%.6g', deg + ph0(k))); end
    o = sim(model, 'StopTime', '0.5', 'ReturnWorkspaceOutputs', 'on'); el = o.get('logsout').get('SI'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
    t = el.Values.Time; i = squeeze(double(el.Values.Data)); if size(i, 1) ~= numel(t), i = i.'; end
    dc = zeros(1, 3); for c = 0:3
        w = t >= 0.3 + c * 0.02 & t < 0.32 + c * 0.02; dcc = mean(i(w, :), 1); dc(c + 1, 1:3) = dcc / (15745.92 * sqrt(2)); 
    end
    fprintf('angle %2d deg: cycle-mean (DC) of the fault current per phase, cycles 1..4 after inception, in rated-peak units:\n', deg); disp(round(dc, 2));
end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
