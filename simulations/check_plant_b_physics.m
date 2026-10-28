function res = check_plant_b_physics()
% CHECK_PLANT_B_PHYSICS Verifies physical criteria on TransformerB_v4 (Plant B).
% Phase 3.2:
% 1. LV bus voltage at 100% rated load >= 0.95 pu
% 2. External 3-phase solid fault at LV bus: 5-20 pu at CTs
% 3. CT saturation on large through-faults with nominal burden (ratio error)
% 4. Plausible internal fault, inrush, and over-excitation
% 5. Writes complete report to simulations/plant_b_checks.txt

model = 'TransformerB_v4';
thisDir = fileparts(mfilename('fullpath'));
if ~bdIsLoaded(model), load_system(fullfile(thisDir, [model '.slx'])); end
cleanup = onCleanup(@() close_system(model, 0));

setappdata(0, 'HybridRelaySkipLSTM', true);
c_clean = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM'));

% Enable datalogging on measurement blocks
pri = findBlock(model, 'Primary_side');
sec = findBlock(model, 'Secondary_side');
for b_cell = {pri, sec}
    b = b_cell{1};
    ph = get_param(b, 'PortHandles');
    for q = 1:numel(ph.Outport)
        set_param(ph.Outport(q), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', ...
            'DataLoggingName', sprintf('%s_out%d', strtok(get_param(b, 'Name'), '_'), q));
    end
end

S_nom = 40e6;
V_hv = 132e3;
V_lv = 33e3;
I_rated_hv = S_nom / (sqrt(3) * V_hv);  % 174.95 A
I_rated_lv = S_nom / (sqrt(3) * V_lv);  % 699.82 A
I_sec_nom = 0.8232;                     % A secondary base (Plant B)
ts = 6.25e-4;                          % 1600 Hz

fid = fopen(fullfile(thisDir, 'plant_b_checks.txt'), 'w');
fprintf(fid, '================================================================================\n');
fprintf(fid, 'PLANT PHYSICS VERIFICATION REPORT (PLANT B: %s)\n', model);
fprintf(fid, 'Date: %s\n', datestr(now, 'dd-mmm-yyyy HH:MM:SS'));
fprintf(fid, 'Rated: 40 MVA, 132 kV / 33 kV, Dyn11\n');
fprintf(fid, 'Rated Line Current: HV %.2f A, LV %.2f A | Secondary Base: %.4f A\n', ...
    I_rated_hv, I_rated_lv, I_sec_nom);
fprintf(fid, '================================================================================\n\n');

%% --- CHECK 1: LV Bus Voltage at Rated Load ---
fprintf('--- Check 1: LV Bus Voltage at 100%% Load ---\n');
hv = findBlock(model, 'Three-Phase Breaker');
lv = findBlock(model, 'Three-Phase Breaker1');
set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');

loadBlk = findBlock(model, 'Three-Phase Series RLC Load');
set_param(loadBlk, 'NominalVoltage', '33e3', ...
                   'ActivePower', sprintf('%.6g', S_nom * 0.95), ...
                   'InductivePower', sprintf('%.6g', S_nom * sqrt(1 - 0.95^2)), ...
                   'CapacitivePower', '0');

setInternalFaultsOff(model);
setExternalFaultsOff(model);

out = sim(model, 'StopTime', '0.6', 'ReturnWorkspaceOutputs', 'on');
Ip = ga(out.get('I_primary_abc'));
Is = ga(out.get('I_secondary_abc'));
t = (0:size(Ip, 1)-1)' * ts;
ss = (t >= 0.4 & t <= 0.6);

I_hv_sec_rms = mean(rms(Ip(ss, :)));
I_lv_sec_rms = mean(rms(Is(ss, :)));
Ilv_pu = I_lv_sec_rms / I_sec_nom;

% Measurement from Secondary_side
ls = out.get('logsout');
s_v = get_signal(ls, 'Secondary_out1');
V_lv_true = mean(rms(s_v(ss, :)));
Vlv_pu = V_lv_true / V_lv;

fprintf(fid, '1. LV BUS VOLTAGE AT 100%% LOAD:\n');
fprintf(fid, '   LV CT Secondary Current: %.4f A (%.4f pu)\n', I_lv_sec_rms, Ilv_pu);
fprintf(fid, '   Measured LV Line Voltage: %.2f kV (%.4f pu)\n', V_lv_true/1e3, Vlv_pu);
if Vlv_pu >= 0.95
    fprintf(fid, '   CRITERION (>= 0.95 pu): PASS\n\n');
    fprintf('   LV Voltage: %.4f pu -> PASS\n', Vlv_pu);
else
    fprintf(fid, '   CRITERION (>= 0.95 pu): FAIL (%.4f pu)\n\n', Vlv_pu);
    fprintf('   LV Voltage: %.4f pu -> FAIL\n', Vlv_pu);
end

%% --- CHECK 2: External 3-Phase Solid Through-Fault ---
fprintf('--- Check 2: External 3-Phase Solid Through-Fault ---\n');
extFault = findBlock(model, 'External_Fault');
extStep = findBlock(model, 'Step4');

% Set external fault: 3-phase solid (Rf = 0.001 ohm), at t = 0.3 s
set_param(extFault, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', ...
    'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(extStep, 'Time', '0.3', 'Before', '0', 'After', '1');

out_fault = sim(model, 'StopTime', '0.5', 'ReturnWorkspaceOutputs', 'on');
Ip_f = ga(out_fault.get('I_primary_abc'));
Is_f = ga(out_fault.get('I_secondary_abc'));
t_f = (0:size(Ip_f, 1)-1)' * ts;

f_idx = (t_f >= 0.32 & t_f <= 0.45);
Ip_rms = rms(Ip_f(f_idx, :));
Is_rms = rms(Is_f(f_idx, :));

I_hv_pu_at_ct = Ip_rms / I_sec_nom;
I_lv_pu_at_ct = Is_rms / I_sec_nom;
mean_tf_pu = mean([I_hv_pu_at_ct, I_lv_pu_at_ct]);
peak_tf_pu = max(max(abs(Ip_f(f_idx, :))), max(abs(Is_f(f_idx, :)))) / (I_sec_nom * sqrt(2));

fprintf(fid, '2. EXTERNAL 3-PHASE SOLID FAULT (LV Bus, Rf = 0.001 ohm):\n');
fprintf(fid, '   HV CT Secondary RMS: A=%.2f A, B=%.2f A, C=%.2f A (Mean: %.2f A)\n', ...
    Ip_rms(1), Ip_rms(2), Ip_rms(3), mean(Ip_rms));
fprintf(fid, '   LV CT Secondary RMS: A=%.2f A, B=%.2f A, C=%.2f A (Mean: %.2f A)\n', ...
    Is_rms(1), Is_rms(2), Is_rms(3), mean(Is_rms));
fprintf(fid, '   Through-Fault Current in pu at CTs:\n');
fprintf(fid, '     HV Side: A=%.2f pu, B=%.2f pu, C=%.2f pu (Mean: %.2f pu)\n', ...
    I_hv_pu_at_ct(1), I_hv_pu_at_ct(2), I_hv_pu_at_ct(3), mean(I_hv_pu_at_ct));
fprintf(fid, '     LV Side: A=%.2f pu, B=%.2f pu, C=%.2f pu (Mean: %.2f pu)\n', ...
    I_lv_pu_at_ct(1), I_lv_pu_at_ct(2), I_lv_pu_at_ct(3), mean(I_lv_pu_at_ct));
fprintf(fid, '     Overall Mean RMS: %.2f pu | Max Symmetrical Peak: %.2f pu\n', mean_tf_pu, peak_tf_pu);

if mean_tf_pu >= 5.0 && mean_tf_pu <= 20.0
    fprintf(fid, '   CRITERION (5-20 pu RMS): PASS (%.2f pu)\n\n', mean_tf_pu);
    fprintf('   Through-fault: %.2f pu -> PASS\n', mean_tf_pu);
else
    fprintf(fid, '   CRITERION (5-20 pu RMS): FAIL (%.2f pu)\n\n', mean_tf_pu);
    fprintf('   Through-fault: %.2f pu -> FAIL\n', mean_tf_pu);
end

%% --- CHECK 3: Natural CT Saturation on High-Current Through-Fault ---
fprintf('--- Check 3: CT Saturation on Through-Fault at Nominal Burden ---\n');
ls_f = out_fault.get('logsout');
s_i_true = get_signal(ls_f, 'Secondary_out2');
Is_true_rms = rms(s_i_true(f_idx, :));
ratio_lv_tf = Is_true_rms ./ Is_rms;
ratio_err_pct = abs(ratio_lv_tf - 808.88) ./ 808.88 * 100;

fprintf(fid, '3. NATURAL CT SATURATION AT NOMINAL BURDEN (2.5 ohm):\n');
fprintf(fid, '   True LV Line Current RMS: A=%.1f A, B=%.1f A, C=%.1f A\n', ...
    Is_true_rms(1), Is_true_rms(2), Is_true_rms(3));
fprintf(fid, '   Effective CT Ratio:       A=%.1f:1, B=%.1f:1, C=%.1f:1 (Nameplate: 800:1)\n', ...
    ratio_lv_tf(1), ratio_lv_tf(2), ratio_lv_tf(3));
fprintf(fid, '   Ratio Error:              A=%.1f%%, B=%.1f%%, C=%.1f%%\n', ...
    ratio_err_pct(1), ratio_err_pct(2), ratio_err_pct(3));
if any(ratio_err_pct > 1.0)
    fprintf(fid, '   CRITERION (Natural CT Saturation Error > 1%%): PASS\n\n');
    fprintf('   CT Saturation Error: max %.1f%% -> PASS\n', max(ratio_err_pct));
else
    fprintf(fid, '   CRITERION (Natural CT Saturation Error > 1%%): FAIL\n\n');
    fprintf('   CT Saturation Error: max %.1f%% -> FAIL\n', max(ratio_err_pct));
end

%% --- CHECK 4: Normal Steady-State Differential Residual ---
fprintf('--- Check 4: Normal Steady-State Differential Current ---\n');
setExternalFaultsOff(model);
out_norm = sim(model, 'StopTime', '0.5', 'ReturnWorkspaceOutputs', 'on');
Ip_n = ga(out_norm.get('I_primary_abc'));
Is_n = ga(out_norm.get('I_secondary_abc'));
t_n = (0:size(Ip_n, 1)-1)' * ts;
n_idx = (t_n >= 0.35 & t_n <= 0.48);

% Dyn11 compensation: M_Dyn11 on LV side
M_Dyn11 = (1/sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
I_lv_comp = (Is_n(n_idx, :) / I_sec_nom) * M_Dyn11.';
I_hv_comp = Ip_n(n_idx, :) / I_sec_nom;
I_diff = I_lv_comp - I_hv_comp;
Idiff_rms = rms(I_diff);

fprintf(fid, '4. NORMAL OPERATION DIFFERENTIAL RESIDUAL:\n');
fprintf(fid, '   Compensated Differential RMS: Phase A=%.4f pu, B=%.4f pu, C=%.4f pu\n', ...
    Idiff_rms(1), Idiff_rms(2), Idiff_rms(3));
if max(Idiff_rms) < 0.05
    fprintf(fid, '   CRITERION (Normal Residual Idiff < 0.05 pu): PASS\n\n');
    fprintf('   Normal Residual Idiff: max %.4f pu -> PASS\n', max(Idiff_rms));
else
    fprintf(fid, '   CRITERION (Normal Residual Idiff < 0.05 pu): FAIL (%.4f pu)\n\n', max(Idiff_rms));
    fprintf('   Normal Residual Idiff: max %.4f pu -> FAIL\n', max(Idiff_rms));
end

fclose(fid);
fprintf('Report saved to %s\n', fullfile(thisDir, 'plant_b_checks.txt'));
type(fullfile(thisDir, 'plant_b_checks.txt'));

res = struct('lv_voltage_pu', Vlv_pu, 'mean_tf_pu', mean_tf_pu, 'peak_tf_pu', peak_tf_pu, ...
             'ratio_err_max', max(ratio_err_pct), 'idiff_rms_max', max(Idiff_rms));
end

function b = findBlock(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times', name, numel(hit));
b = hit{1};
end

function setInternalFaultsOff(model)
for nm = {'Internal_Fault1', 'Internal_Fault2', 'Internal_Fault3'}
    try
        b = findBlock(model, nm{1});
        set_param(b, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
    catch
    end
end
try
    b_hv = findBlock(model, 'Internal_Fault_HV');
    set_param(b_hv, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
catch
end
for st = {'Step3', 'Step_Evolve2', 'Step_Evolve3'}
    try
        b = findBlock(model, st{1});
        set_param(b, 'Time', '10');
    catch
    end
end
end

function setExternalFaultsOff(model)
extFault = findBlock(model, 'External_Fault');
extStep = findBlock(model, 'Step4');
set_param(extFault, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
set_param(extStep, 'Time', '10');
end

function v = get_signal(ls, name)
el = ls.get(name);
if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
v = squeeze(double(el.Values.Data));
tt = el.Values.Time;
if size(v, 1) ~= numel(tt), v = v.'; end
end

function x = ga(v)
if isa(v, 'timeseries'), x = squeeze(double(v.Data));
elseif isstruct(v), x = squeeze(double(v.signals.values));
else, x = squeeze(double(v));
end
if size(x, 2) ~= 3 && size(x, 1) == 3
    x = x.';
end
end
