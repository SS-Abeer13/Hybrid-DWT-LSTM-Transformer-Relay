function add_hv_internal_fault(saveChanges)
%ADD_HV_INTERNAL_FAULT Step A5: add an internal fault block on the HV (230 kV) winding terminals, inside the HV CT zone.
%
% Copies 'Internal_Fault1' -> 'Internal_Fault_HV' and its timer 'Step3' -> 'Step_HV' (same library blocks, External = on, switching by the
% step), and connects the fault's three terminals to the transformer's HV terminals (Step_down_Transformer LConn 1-3). The HV CTs sit
% between the source and these terminals, so a fault here is an INTERNAL fault (HV CT current flows, LV CT current does not).
% Everything is off by default (phases off, step time 10 s). Back up the .slx first (done by the caller).
% The test configuration used for the checks is applied IN MEMORY ONLY; the saved file gets just the two blocks and their wiring.
%
% SAFETY CHECKS (the function stops and does NOT save if any fails):
%   1. a deterministic Normal case gives the same CT currents with and without the new block (max |diff| < 1e-3 A);
%   2. an LV A-B fault still gives the same faultDiffPu as before (+/-1 %), and an HV A-G solid fault at 0.4 s gives faultDiffPu > 1 pu.
%
%   add_hv_internal_fault        % apply to the loaded model only
%   add_hv_internal_fault(true)  % apply, verify, save
if nargin < 1, saveChanges = false; end
model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
if bdIsLoaded(model), assert(strcmp(get_param(model, 'Dirty'), 'off'), 'model has unsaved changes'); close_system(model, 0); end
load_system(fullfile(thisDir, [model '.slx']));
setappdata(0, 'HybridRelaySkipLSTM', true); cleanup = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>

if ~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'Internal_Fault_HV'))
    fprintf('Internal_Fault_HV already exists: nothing to add.\n'); return;
end
setup(model);
before = measure(model);              % baseline Normal + LV A-B fault, without the new block

addBlocks(model);
fprintf('Added Internal_Fault_HV + Step_HV, wired to the transformer HV terminals (test configuration, in memory).\n');

after = measure(model);
d1 = max(abs(after.normalIp(:) - before.normalIp(:))); d2 = max(abs(after.normalIs(:) - before.normalIs(:)));
fprintf('Regression, Normal: max |dIp| = %.2e A, max |dIs| = %.2e A\n', d1, d2);
assert(d1 < 1e-3 && d2 < 1e-3, 'adding the block changed a healthy trace: NOT saving');
fprintf('Regression, LV A-B fault: faultDiffPu %.3f -> %.3f\n', before.lvFaultDiff, after.lvFaultDiff);
assert(abs(after.lvFaultDiff - before.lvFaultDiff) <= 0.01 * before.lvFaultDiff, 'LV fault result changed: NOT saving');
fprintf('HV A-G solid fault: faultDiffPu = %.2f pu (HV CT peak %.1f A, LV CT peak %.2f A)\n', after.hvFaultDiff, after.hvPeakHV, after.hvPeakLV);
assert(after.hvFaultDiff > 1, 'HV fault is not seen by the differential: NOT saving');
if saveChanges
    % The test configuration above (noise off, breakers, load, burden ...) must NOT be saved. Reload the pristine file, add only the two
    % blocks and their wiring, save, then verify the saved file by reloading it.
    close_system(model, 0);
    load_system(fullfile(thisDir, [model '.slx']));
    addBlocks(model);
    save_system(model);
    close_system(model, 0);
    load_system(fullfile(thisDir, [model '.slx']));
    assert(~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'Internal_Fault_HV')) && ~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'Step_HV')), 'saved model lacks the new blocks');
    assert(strcmp(get_param(fb(model, 'Three-Phase Breaker'), 'SwitchTimes'), '[]'), 'saved model has modified breaker settings');
    assert(strcmp(get_param([model '/Internal_Fault_HV'], 'FaultA'), 'off') && strcmp(get_param([model '/Step_HV'], 'Time'), '10'), 'new block is not in the all-off default');
    fprintf('Saved %s with ONLY the new blocks added (original parameters untouched).\n', model);
else
    fprintf('Applied to the loaded model only (not saved).\n');
end
end

function addBlocks(model)
src = fb(model, 'Internal_Fault1'); stp = fb(model, 'Step3'); xf = fb(model, 'Step_down_Transformer');
posF = get_param(src, 'Position'); posS = get_param(stp, 'Position');
newF = [model '/Internal_Fault_HV']; newS = [model '/Step_HV'];
add_block(src, newF, 'Position', posF + [-250 0 -250 0]);
add_block(stp, newS, 'Position', posS + [-250 0 -250 0]);
set_param(newF, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');
set_param(newS, 'Time', '10');
phF = get_param(newF, 'PortHandles'); phS = get_param(newS, 'PortHandles'); phX = get_param(xf, 'PortHandles');
add_line(model, phS.Outport(1), phF.Inport(1), 'autorouting', 'on');
assert(numel(phF.LConn) == 3 && numel(phX.LConn) == 3, 'unexpected port layout (fault LConn %d, transformer LConn %d)', numel(phF.LConn), numel(phX.LConn));
for k = 1:3, add_line(model, phF.LConn(k), phX.LConn(k), 'autorouting', 'on'); end
end

function setup(model)
hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1');
set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Step_down_Transformer'), 'SetInitialFlux', 'off');
vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')}; ph0 = [0 -120 120];
for k = 1:3, set_param(vs{k}, 'Amplitude', sprintf('%.6g', 230e3 * sqrt(2) / sqrt(3)), 'Phase', sprintf('%.6g', 30 + ph0(k))); end
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
ct = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}; for k = 1:6, set_param(fb(fb(model, ct{k}), '1ohm'), 'Resistance', '1'); end
f = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'};
for i = 1:4, set_param(fb(model, f{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); set_param(fb(model, f{i, 2}), 'Time', '10'); end
ld = fb(model, 'Three-Phase Series RLC Load'); kn = load_knob_for(60, 0.9);
set_param(ld, 'ActivePower', sprintf('%.6g', kn * 300e6 * 0.9), 'InductivePower', sprintf('%.6g', kn * 300e6 * sqrt(1 - 0.81)), 'CapacitivePower', '0');
dph = get_param(fb(fb(model, 'Hybrid 87T Relay'), 'I_diff'), 'PortHandles');
set_param(dph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'I_diff_comp');
end

function r = measure(model)
fs = 1600; tF = 0.4;
o = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on'); r.normalIp = ga(o.get('I_primary_abc')); r.normalIs = ga(o.get('I_secondary_abc'));
set_param(fb(model, 'Internal_Fault1'), 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'off', 'GroundFault', 'off'); set_param(fb(model, 'Step3'), 'Time', sprintf('%.4f', tF));
o = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on'); r.lvFaultDiff = diffRise(o, tF);
set_param(fb(model, 'Internal_Fault1'), 'FaultA', 'off', 'FaultB', 'off'); set_param(fb(model, 'Step3'), 'Time', '10');
r.hvFaultDiff = NaN; r.hvPeakHV = NaN; r.hvPeakLV = NaN;
if ~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'Internal_Fault_HV'))
    set_param([model '/Internal_Fault_HV'], 'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on', 'FaultResistance', '0.01'); set_param([model '/Step_HV'], 'Time', sprintf('%.4f', tF));
    o = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on'); r.hvFaultDiff = diffRise(o, tF);
    Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc')); t = (0:size(Ip, 1) - 1)' / fs; w = t >= tF & t <= tF + 0.05;
    r.hvPeakHV = max(abs(Ip(w, :)), [], 'all'); r.hvPeakLV = max(abs(Is(w, :)), [], 'all');
    set_param([model '/Internal_Fault_HV'], 'FaultA', 'off', 'GroundFault', 'off'); set_param([model '/Step_HV'], 'Time', '10');
end
end

function d = diffRise(o, tF)
el = o.get('logsout').get('I_diff_comp'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
tc = el.Values.Time; dc = squeeze(double(el.Values.Data)); if size(dc, 2) ~= 3, dc = dc.'; end
rm = @(a, b) sqrt(mean(dc(tc >= a & tc < b, :) .^ 2, 1));
d = max(rm(tF + 0.04, tF + 0.06) - rm(tF - 0.03, tF - 0.01));
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
function x = ga(v)
if isa(v, 'timeseries'), x = double(v.Data); elseif isstruct(v), x = double(v.signals.values); else, x = double(v); end
end
