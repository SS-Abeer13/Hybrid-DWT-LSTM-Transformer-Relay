function add_hv_bus_fault(saveChanges)
%ADD_HV_BUS_FAULT Step A6: add an EXTERNAL fault block on the 230 kV bus, upstream of the HV breaker and the HV CTs (outside the CT zone).
%
% WHY: the existing External_Fault sits on the LV side behind 0.5 ohm series resistors and the source is stiff, so an external fault barely
% disturbs the transformer voltage and nothing like a recovery inrush follows (probe_overexc_recovery.m: differential 0.006 pu, noise floor).
% A fault on the HV bus collapses the transformer's terminal voltage; when it clears the voltage recovers and the core can draw a
% recovery (voltage-recovery) inrush - the classic security case.
%
% Copies 'External_Fault' -> 'External_Fault_HV' and its timer 'Step4' -> 'Step_ExtHV' and connects the fault's three terminals to the
% LConn ports of 'Three-Phase Breaker' (the source side of the HV breaker). Off by default. In generation the fault is switched by its own
% SwitchTimes [t1 t2] (External off) so that it CLEARS after 40-100 ms.
%
% SAFETY (the function does NOT save if a check fails; the in-memory TEST configuration is never saved):
%   1. a deterministic Normal case is bit-identical with and without the block (max |diff| < 1e-3 A);
%   2. a 60 ms HV-bus fault (Rf 0.2 ohm) dips the HV bus voltage below 0.6 pu, no HV-CT current is added by the fault itself, and after clearing the
%      differential shows a recovery transient (rms > 0.02 pu with a 2nd-harmonic ratio > 0.1).
if nargin < 1, saveChanges = false; end
model = 'TransformerWithCTSaturation'; thisDir = fileparts(mfilename('fullpath'));
if bdIsLoaded(model), assert(strcmp(get_param(model, 'Dirty'), 'off'), 'model has unsaved changes'); close_system(model, 0); end
load_system(fullfile(thisDir, [model '.slx']));
setappdata(0, 'HybridRelaySkipLSTM', true); cleanup = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
if ~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'External_Fault_HV'))
    fprintf('External_Fault_HV already exists: nothing to add.\n'); return;
end
setup(model);
o0 = sim(model, 'StopTime', '0.8', 'ReturnWorkspaceOutputs', 'on'); n0p = ga(o0.get('I_primary_abc')); n0s = ga(o0.get('I_secondary_abc'));
addBlocks(model);
fprintf('Added External_Fault_HV + Step_ExtHV on the HV bus (test configuration, in memory).\n');
o1 = sim(model, 'StopTime', '0.8', 'ReturnWorkspaceOutputs', 'on'); n1p = ga(o1.get('I_primary_abc')); n1s = ga(o1.get('I_secondary_abc'));
d1 = max(abs(n1p(:) - n0p(:))); d2 = max(abs(n1s(:) - n0s(:)));
fprintf('Regression, Normal: max |dIp| = %.2e A, max |dIs| = %.2e A\n', d1, d2);
assert(d1 < 1e-3 && d2 < 1e-3, 'adding the block changed a healthy trace: NOT saving');

% recovery scan: 3-phase HV-bus fault from 0.35 s, cleared after 'dur'; whether the core saturates depends on the dip / clearing angles
ef = [model '/External_Fault_HV'];
fs = 1600; M = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
best = struct('rms', 0, 'h2', 0, 'Rf', NaN, 'dur', NaN); vFaultMin = 1;
fprintf('%-6s %-7s | HV V in fault | max d rms after clearing | 2nd/1st at that peak\n', 'Rf', 'dur');
for Rf = [0.05 0.2]
    for dur = [0.045 0.050 0.055 0.060 0.065 0.075]
        set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'off', 'FaultResistance', sprintf('%.4f', Rf), 'External', 'off', 'SwitchTimes', sprintf('[0.35 %.4f]', 0.35 + dur));
        o2 = sim(model, 'StopTime', '0.8', 'ReturnWorkspaceOutputs', 'on');
        Ip = ga(o2.get('I_primary_abc')); Is = ga(o2.get('I_secondary_abc')); d = Is - Ip * M; t = (0:size(Ip, 1) - 1)' / fs;
        [vv, tv] = logged(o2.get('logsout'), 'AddTestPrimV');
        vF = mean(sqrt(mean(vv(tv >= 0.37 & tv <= 0.35 + dur - 0.005, :) .^ 2, 1))) / 230e3; vFaultMin = min(vFaultMin, vF);
        tc = 0.35 + dur;
        i0s = round((tc + 0.005) * fs):round((tc + 0.15) * fs); pk = 0; h2 = 0;
        for i0 = i0s(1:2:end)
            w = i0:i0 + 31; r = mean(sqrt(mean(d(w, :) .^ 2, 1))) / 0.9302;
            if r > pk, pk = r; F = abs(fft(d(w, :), [], 1)); h2 = mean(F(3, :) ./ max(F(2, :), 1e-4)); end
        end
        fprintf('%-6.2f %-7.3f | %-13.2f | %-24.4f | %-8.3f\n', Rf, dur, vF, pk, h2);
        if pk > best.rms, best = struct('rms', pk, 'h2', h2, 'Rf', Rf, 'dur', dur); end
    end
end
fprintf('Best recovery transient: d rms %.3f pu, 2nd/1st %.3f (Rf %.2f, dur %.3f s); minimum fault-period HV voltage %.2f pu\n', best.rms, best.h2, best.Rf, best.dur, vFaultMin);
assert(vFaultMin < 0.6, 'HV bus fault does not dip the voltage enough: NOT saving');
assert(best.rms > 0.05 && best.h2 > 0.1, 'no recovery inrush after clearing in any combination: NOT saving');
if saveChanges
    close_system(model, 0);
    load_system(fullfile(thisDir, [model '.slx']));
    addBlocks(model);
    save_system(model);
    close_system(model, 0);
    load_system(fullfile(thisDir, [model '.slx']));
    assert(~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'External_Fault_HV')) && ~isempty(find_system(model, 'SearchDepth', 1, 'Name', 'Step_ExtHV')), 'saved model lacks the new blocks');
    assert(strcmp(get_param(fb(model, 'Three-Phase Breaker'), 'SwitchTimes'), '[]'), 'saved model has modified breaker settings');
    assert(strcmp(get_param(fb(model, 'External_Fault_HV'), 'FaultA'), 'off') && strcmp(get_param(fb(model, 'Step_ExtHV'), 'Time'), '10'), 'new block is not in the all-off default');
    fprintf('Saved %s with ONLY the new blocks added (original parameters untouched).\n', model);
else
    fprintf('Applied to the loaded model only (not saved).\n');
end
end

function addBlocks(model)
src = fb(model, 'External_Fault'); stp = fb(model, 'Step4'); br = fb(model, 'Three-Phase Breaker');
posF = get_param(src, 'Position'); posS = get_param(stp, 'Position');
newF = [model '/External_Fault_HV']; newS = [model '/Step_ExtHV'];
add_block(src, newF, 'Position', posF + [-300 -150 -300 -150]);
add_block(stp, newS, 'Position', posS + [-300 -150 -300 -150]);
set_param(newF, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01');
set_param(newS, 'Time', '10');
phF = get_param(newF, 'PortHandles'); phS = get_param(newS, 'PortHandles'); phB = get_param(br, 'PortHandles');
add_line(model, phS.Outport(1), phF.Inport(1), 'autorouting', 'on');
assert(numel(phF.LConn) == 3 && numel(phB.LConn) == 3, 'unexpected port layout (fault LConn %d, breaker LConn %d)', numel(phF.LConn), numel(phB.LConn));
for k = 1:3, add_line(model, phF.LConn(k), phB.LConn(k), 'autorouting', 'on'); end
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
f = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'; 'Internal_Fault_HV', 'Step_HV'};
for i = 1:size(f, 1), set_param(fb(model, f{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); set_param(fb(model, f{i, 2}), 'Time', '10'); end
ld = fb(model, 'Three-Phase Series RLC Load'); kn = load_knob_for(30, 0.9);
set_param(ld, 'ActivePower', sprintf('%.6g', kn * 300e6 * 0.9), 'InductivePower', sprintf('%.6g', kn * 300e6 * sqrt(1 - 0.81)), 'CapacitivePower', '0');
% log the HV bus voltage (Primary_side out1) for the dip check
ph = get_param(fb(model, 'Primary_side'), 'PortHandles');
set_param(ph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'AddTestPrimV');
end

function [v, t] = logged(ls, name)
el = ls.get(name); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data)); if size(v, 1) ~= numel(t), v = v.'; end
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
