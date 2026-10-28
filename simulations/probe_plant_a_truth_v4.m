function res = probe_plant_a_truth_v4()
%PROBE_PLANT_A_TRUTH_V4 Independent measurement (V-I blocks, each on its OWN time base) of the quantities plant_v4_checks.txt derived from the CT ratio.
%   * true LV bus voltage and line current at 100 % load (check 1 used a CT-ratio estimate and the assumption P = const);
%   * true through-fault current of the external 3-phase solid fault, RMS AND peak, next to the CT secondary RMS (check 2 reported only the CT RMS,
%     and accepted 5-25 pu while printing 5-20 pu);
%   * how far the CT secondary under-reads the true current (saturation).
% In-memory only; writes simulations/plant_v4_truth_check.txt.
model = 'TransformerWithCTSaturation_v4'; thisDir = fileparts(mfilename('fullpath'));
load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() close_system(model, 0)); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
S_nom = 300e6; V_lv = 11e3; I_hv = S_nom / (sqrt(3) * 230e3); I_lv = S_nom / (sqrt(3) * V_lv); I_sec_nom = 1.8610; ts = 6.25e-4;
sides = {fb(model, 'Primary_side'), fb(model, 'Secondary_side')};
for k = 1:2
    ph = get_param(sides{k}, 'PortHandles');
    for q = 1:2, set_param(ph.Outport(q), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', sprintf('TR%d_out%d', k, q)); end
end
set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Series RLC Load'), 'ActivePower', sprintf('%.6g', S_nom), 'InductivePower', '0', 'CapacitivePower', '0');
for nm = {'Internal_Fault1', 'Internal_Fault2', 'Internal_Fault3', 'External_Fault'}
    try, set_param(fb(model, nm{1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off'); catch, end %#ok<NOCOM>
end
for st = {'Step3', 'Step_Evolve2', 'Step_Evolve3', 'Step4'}
    try, set_param(fb(model, st{1}), 'Time', '10'); catch, end %#ok<NOCOM>
end
fid = fopen(fullfile(thisDir, 'plant_v4_truth_check.txt'), 'w');
fprintf(fid, 'Independent plant A (v4) measurement with the V-I blocks, %s\n(script: simulations/probe_plant_a_truth_v4.m; every signal on its own time base)\n\n', datestr(now)); %#ok<TNOW1,DATST>

% ---- 1. load case
out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on'); ls = out.get('logsout');
[vlv, tv] = sig(ls, 'TR2_out1'); [ilv, ti] = sig(ls, 'TR2_out2'); w = tv >= 0.4; wi = ti >= 0.4;
Ils = ga(out.get('I_secondary_abc')); t1 = (0:size(Ils, 1) - 1)' * ts;
fprintf(fid, '1. 100 %% LOAD (P = 300 MW, pf 1.0), steady state t >= 0.4 s\n   TRUE LV bus voltage %.3f kV = %.4f pu | TRUE LV line current %.1f A = %.4f pu | LV CT secondary %.4f A = %.4f pu\n\n', ...
    mean(rms(vlv(w, :))) / 1e3, mean(rms(vlv(w, :))) / V_lv, mean(rms(ilv(wi, :))), mean(rms(ilv(wi, :))) / I_lv, mean(rms(Ils(t1 >= 0.4, :))), mean(rms(Ils(t1 >= 0.4, :))) / I_sec_nom);

% ---- 2. external 3-phase solid fault at t = 0.3 s
ef = fb(model, 'External_Fault');
set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(fb(model, 'Step4'), 'Time', '0.3', 'Before', '0', 'After', '1');
out = sim(model, 'StopTime', '0.5', 'ReturnWorkspaceOutputs', 'on'); ls = out.get('logsout');
[ipt, tp] = sig(ls, 'TR1_out2'); [ist, tsx] = sig(ls, 'TR2_out2');
Ip = ga(out.get('I_primary_abc')); Is = ga(out.get('I_secondary_abc')); t = (0:size(Ip, 1) - 1)' * ts;
wf = t >= 0.32 & t <= 0.45; wp = tp >= 0.32 & tp <= 0.45; ws = tsx >= 0.32 & tsx <= 0.45;
ctHV = mean(rms(Ip(wf, :))); ctLV = mean(rms(Is(wf, :))); trHV = mean(rms(ipt(wp, :))); trLV = mean(rms(ist(ws, :)));
pkTrHV = max(abs(ipt(wp, :)), [], 'all') / (I_hv * sqrt(2)); pkTrLV = max(abs(ist(ws, :)), [], 'all') / (I_lv * sqrt(2));
pkCt = max([max(abs(Ip(wf, :)), [], 'all'), max(abs(Is(wf, :)), [], 'all')]) / (I_sec_nom * sqrt(2));
fprintf(fid, '2. EXTERNAL 3-PHASE SOLID FAULT (LV bus, Rf 0.001 ohm), window 0.32-0.45 s\n');
fprintf(fid, '   TRUE line current RMS : HV %.1f A = %.2f pu | LV %.1f A = %.2f pu\n', trHV, trHV / I_hv, trLV, trLV / I_lv);
fprintf(fid, '   TRUE line current PEAK: HV %.2f | LV %.2f  (in units of the rated PEAK current)\n', pkTrHV, pkTrLV);
fprintf(fid, '   CT secondary RMS      : HV %.3f A = %.2f pu | LV %.3f A = %.2f pu  (peak %.2f of rated peak)\n', ctHV, ctHV / I_sec_nom, ctLV, ctLV / I_sec_nom, pkCt);
fprintf(fid, '   CT secondary / (true / nominal ratio): HV %.3f, LV %.3f   (< 1 = CT under-reads = saturation; > 1 would be a scaling error)\n', (ctHV / I_sec_nom) / (trHV / I_hv), (ctLV / I_sec_nom) / (trLV / I_lv));
fprintf(fid, '   Plan criterion 1.5: 5-20 pu RMS at the CTs. TRUE RMS = %.2f pu, CT RMS = %.2f pu. The old check accepted anything up to 25 pu while printing 5-20 pu.\n', mean([trHV / I_hv, trLV / I_lv]), mean([ctHV, ctLV]) / I_sec_nom);
fclose(fid);
type(fullfile(thisDir, 'plant_v4_truth_check.txt'));
res = struct('trueRmsPu', mean([trHV / I_hv, trLV / I_lv]), 'ctRmsPu', mean([ctHV, ctLV]) / I_sec_nom);
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times', name, numel(hit)); blk = hit{1};
end
function [v, t] = sig(ls, name)
el = ls.get(name); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data)); if size(v, 1) ~= numel(t), v = v.'; end
end
function x = ga(v)
if isa(v, 'timeseries'), x = squeeze(double(v.Data)); elseif isstruct(v), x = squeeze(double(v.signals.values)); else, x = squeeze(double(v)); end
if size(x, 2) ~= 3 && size(x, 1) == 3, x = x.'; end
end
