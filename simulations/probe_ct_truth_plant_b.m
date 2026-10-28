function res = probe_ct_truth_plant_b()
% PROBE_CT_TRUTH_PLANT_B True transformer line currents vs CT-secondary signals on Plant B.
% Step 3.2: Measures true CT ratios, rated secondary currents, and voltages on Plant B model.

model = 'TransformerB_v4';
thisDir = fileparts(mfilename('fullpath'));
cd(thisDir);
load_system(fullfile(thisDir, [model '.slx']));
cleanup = onCleanup(@() close_system(model, 0));

setappdata(0, 'HybridRelaySkipLSTM', true);
c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM'));

for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}
    try set_param(model, m{1}, 'none'); catch; end
end

fn = @(n) {fb(model, n)};
pri = fn('Primary_side'); sec = fn('Secondary_side');
assert(numel(pri) == 1 && numel(sec) == 1);

for b = [pri sec]
    ph = get_param(b{1}, 'PortHandles');
    for q = 1:numel(ph.Outport)
        set_param(ph.Outport(q), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', ...
            'DataLoggingName', sprintf('%s_out%d', strtok(get_param(b{1}, 'Name'), '_'), q));
    end
end

hv = fn('Three-Phase Breaker'); lv = fn('Three-Phase Breaker1');
set_param(hv{1}, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(lv{1}, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');

for nm = {'Internal_Fault1', 'Internal_Fault2', 'Internal_Fault3', 'External_Fault'}
    b = fn(nm{1});
    set_param(b{1}, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
end

try
    b_hv = fn('Internal_Fault_HV');
    set_param(b_hv{1}, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
catch
end

for st = {'Step3', 'Step_Evolve2', 'Step_Evolve3', 'Step4'}
    try b = fn(st{1}); set_param(b{1}, 'Time', '10'); catch; end
end

nmu = fn('Noise Merging Unit');
for k = 1:6
    set_param([nmu{1} '/Noise_Gain_' num2str(k)], 'Gain', '0');
    set_param([nmu{1} '/CT_Gain_Mismatch_' num2str(k)], 'Gain', '1');
end

all_b = find_system(model, 'SearchDepth', 1, 'Type', 'Block');
ld = all_b(contains(all_b, 'RLC Load'));
assert(numel(ld) == 1, 'load block not unique');
ld = ld{1};

fs = 1600;
Srated = 40e6;
pf = 0.95;
Vhv_rated = 132e3;
Vlv_rated = 33e3;
I_rated_pri = Srated / (sqrt(3) * Vhv_rated); % 174.95 A
I_rated_sec_line = Srated / (sqrt(3) * Vlv_rated); % 699.82 A

out_file = fullfile(thisDir, 'ct_calibration_plant_b.txt');
fid = fopen(out_file, 'w');

fprintf(fid, '================================================================================\n');
fprintf(fid, 'CT TRUTH & CALIBRATION REPORT (PLANT B: %s)\n', model);
fprintf(fid, 'Date: %s\n', datestr(now));
fprintf(fid, 'Rated Plant Parameters: 40 MVA, 132 kV / 33 kV, Dyn11\n');
fprintf(fid, 'Rated Line Current HV: %.2f A, LV: %.2f A\n', I_rated_pri, I_rated_sec_line);
fprintf(fid, '================================================================================\n\n');

res = struct();
knobs = [0.1, 0.5, 1.0, 1.5, 2.0];

for idx = 1:length(knobs)
    knob = knobs(idx);
    S = knob * Srated;
    set_param(ld, 'NominalVoltage', '33e3', ...
                  'ActivePower', sprintf('%.6g', S * pf), ...
                  'InductivePower', sprintf('%.6g', S * sqrt(1 - pf^2)), ...
                  'CapacitivePower', '0');
    
    out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
    ls = out.get('logsout');
    
    Ip = ga(out.get('I_primary_abc'));
    Is = ga(out.get('I_secondary_abc'));
    t2 = (0:size(Ip, 1) - 1)' / fs;
    ok2 = t2 > 0.3;
    
    % True currents & voltages from Primary_side & Secondary_side
    p_v = get_signal(ls, 'Primary_out1');
    p_i = get_signal(ls, 'Primary_out2');
    s_v = get_signal(ls, 'Secondary_out1');
    s_i = get_signal(ls, 'Secondary_out2');
    
    Ihv_true = mean(rms_steady(p_i, ok2));
    Ilv_true = mean(rms_steady(s_i, ok2));
    Vhv_true = mean(rms_steady(p_v, ok2));
    Vlv_true = mean(rms_steady(s_v, ok2));
    
    Ihv_sec = mean(rms_steady(Ip, ok2));
    Ilv_sec = mean(rms_steady(Is, ok2));
    
    ratio_hv = Ihv_true / Ihv_sec;
    ratio_lv = Ilv_true / Ilv_sec;
    
    Vlv_pu = Vlv_true / Vlv_rated;
    Vhv_pu = Vhv_true / Vhv_rated;
    
    fprintf(fid, '--- Knob %.2f (%.1f%% Load, S = %.1f MVA) ---\n', knob, knob*100, S/1e6);
    fprintf(fid, '  True HV Line: %.2f A, CT Sec HV: %.4f A -> Ratio HV: %.4f : 1 (Nameplate: 200.0 : 1)\n', Ihv_true, Ihv_sec, ratio_hv);
    fprintf(fid, '  True LV Line: %.2f A, CT Sec LV: %.4f A -> Ratio LV: %.4f : 1 (Nameplate: 800.0 : 1)\n', Ilv_true, Ilv_sec, ratio_lv);
    fprintf(fid, '  Voltages: HV = %.2f kV (%.3f pu), LV = %.2f kV (%.3f pu)\n\n', ...
        Vhv_true/1e3, Vhv_pu, Vlv_true/1e3, Vlv_pu);
    
    if knob == 1.0
        res.ratio_hv_rated = ratio_hv;
        res.ratio_lv_rated = ratio_lv;
        res.I_rated_sec_hv = Ihv_sec;
        res.I_rated_sec_lv = Ilv_sec;
        res.Vlv_pu_at_rated = Vlv_pu;
    end
end

fprintf(fid, '================================================================================\n');
fprintf(fid, 'SUMMARY (PLANT B AT 100%% RATED LOAD):\n');
fprintf(fid, 'Effective CT Ratio HV: %.4f : 1 (Nameplate: 200.0 : 1)\n', res.ratio_hv_rated);
fprintf(fid, 'Effective CT Ratio LV: %.4f : 1 (Nameplate: 800.0 : 1)\n', res.ratio_lv_rated);
fprintf(fid, 'Rated CT-Secondary Current HV: %.4f A\n', res.I_rated_sec_hv);
fprintf(fid, 'Rated CT-Secondary Current LV: %.4f A\n', res.I_rated_sec_lv);
fprintf(fid, 'LV Bus Voltage at Rated Load: %.3f pu\n', res.Vlv_pu_at_rated);
fprintf(fid, '================================================================================\n');

fclose(fid);
fprintf('CT Truth probe for Plant B complete. Results written to %s\n', out_file);
type(out_file);
end

function r = rms_steady(x, mask)
x_part = x(mask, :);
r = sqrt(mean(x_part.^2, 1));
end

function b = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times', name, numel(hit));
b = hit{1};
end

function v = get_signal(ls, name)
el = ls.get(name);
if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
v = squeeze(double(el.Values.Data));
tt = el.Values.Time;
if size(v, 1) ~= numel(tt), v = v.'; end
end

function x = ga(v)
if isa(v, 'timeseries'), x = double(v.Data); elseif isstruct(v), x = double(v.signals.values); else, x = double(v); end
end
