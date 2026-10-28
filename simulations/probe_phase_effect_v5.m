function probe_phase_effect_v5()
%PROBE_PHASE_EFFECT_V5 Does the voltage-source 'Phase' parameter change the instant-on-wave of a fault? (in memory only)
% Same external 3-phase fault at t = 0.3 s with source phase 90 deg (fault at the voltage peak) and 0 deg (voltage zero): compare the first-cycle fault currents.
model = 'TransformerWithCTSaturation_v5'; thisDir = fileparts(mfilename('fullpath'));
bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
ph = get_param(fb(model, 'Primary_side'), 'PortHandles');
set_param(ph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'PV');
ph2 = get_param(fb(model, 'Secondary_side'), 'PortHandles');
set_param(ph2.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'SI');
set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
ef = fb(model, 'External_Fault'); set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(fb(model, 'Step4'), 'Time', '0.3', 'Before', '0', 'After', '1');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
fprintf('source Phase parameter now: %s\n', get_param(vs{1}, 'Phase'));
res = struct();
for deg = [90 0]
    for k = 1:3, set_param(vs{k}, 'Phase', sprintf('%.6g', deg + ph0(k))); end
    o = sim(model, 'StopTime', '0.45', 'ReturnWorkspaceOutputs', 'on'); ls = o.get('logsout');
    el = ls.get('PV'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
    tv = el.Values.Time; v = squeeze(double(el.Values.Data)); if size(v, 1) ~= numel(tv), v = v.'; end
    el = ls.get('SI'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
    ti = el.Values.Time; i = squeeze(double(el.Values.Data)); if size(i, 1) ~= numel(ti), i = i.'; end
    % HV line-to-line voltage A-B at t = 0.29 and its phase: value at the fault instant
    k0 = find(tv >= 0.3, 1); w = ti >= 0.3 & ti <= 0.34; Ipk = max(abs(i(w, :)), [], 1) / (15745.92 * sqrt(2));
    fprintf('Phase %3d deg: HV V_AB at t=0.3 s = %9.1f V (peak %.0f V) | first 40 ms fault peak per phase / rated peak: %.2f %.2f %.2f | max %.2f\n', deg, v(k0, 1), max(abs(v(:, 1))), Ipk, max(Ipk));
    res.(sprintf('p%d', deg)) = Ipk;
end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
