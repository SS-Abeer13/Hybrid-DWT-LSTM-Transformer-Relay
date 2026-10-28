function res = check_plant_physics_v5(plant)
%CHECK_PLANT_PHYSICS_V5 Physics verification of a v5 plant ('A' = TransformerWithCTSaturation_v5, 'B' = TransformerB_v5), TRUE currents from the V-I blocks.
%   Every signal is used on its OWN time base (the V-I blocks are logged at the solver rate, the relay signals at 1600 Hz) - the v4 plant B check mixed them up.
%   Criteria (IMPLEMENTATION_PLAN_V4_PUBLICATION.md, V8 option (a)):
%     C1 LV bus voltage at 100 % load, pf 1.0 >= 0.95 pu
%     C2 TRUE symmetrical external 3-phase solid through-fault 7-15 pu RMS
%     C3 CTs LINEAR on that through-fault in the steady state (0.40-0.46 s) at nominal burden: ratio deviation < 5 % (RMS-based, both sides)
%     C4 the same fault with maximum DC offset saturates a CT visibly in the first two cycles (deviation > 10 % on at least one side)
%     C5 4 x burden saturates the first two cycles of the fault (deviation > 10 %) - burden stress works
%     C6 CT stays linear to 150 % load at 3 x burden (ratio change < 2 % vs 100 % load) and the normal differential residual stays < 0.05 pu
%   In-memory only; writes simulations/plant_v5_checks_<plant>.txt and returns the measured CT ratios / base current.
if strcmpi(plant, 'A')
    model = 'TransformerWithCTSaturation_v5'; S = 300e6; Vhv = 230e3; Vlv = 11e3; burden0 = 1.0; Msd = (1/sqrt(3)) * [1 0 -1; -1 1 0; 0 -1 1]; side = 'hv';
else
    model = 'TransformerB_v5'; S = 40e6; Vhv = 132e3; Vlv = 33e3; burden0 = 2.5; Msd = (1/sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1]; side = 'lv';
end
Ihv = S / (sqrt(3) * Vhv); Ilv = S / (sqrt(3) * Vlv); fs = 1600; ts = 1 / fs;
thisDir = fileparts(mfilename('fullpath'));
bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
sides = {fb(model, 'Primary_side'), fb(model, 'Secondary_side')};
for k = 1:2
    ph = get_param(sides{k}, 'PortHandles');
    for q = 1:2, set_param(ph.Outport(q), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', sprintf('TR%d_out%d', k, q)); end
end
hv = fb(model, 'Three-Phase Breaker'); lv = fb(model, 'Three-Phase Breaker1');
set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]'); set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Step_down_Transformer'), 'SetInitialFlux', 'off');
nmu = fb(model, 'Noise Merging Unit');
for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
faults = {'Internal_Fault1', 'Step3'; 'Internal_Fault2', 'Step_Evolve2'; 'Internal_Fault3', 'Step_Evolve3'; 'External_Fault', 'Step4'; 'Internal_Fault_HV', 'Step_HV'; 'External_Fault_HV', 'Step_ExtHV'};
for i = 1:size(faults, 1)
    try, set_param(fb(model, faults{i, 1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off', 'FaultResistance', '0.01'); set_param(fb(model, faults{i, 2}), 'Time', '10'); catch, end %#ok<NOCOM>
end
ctn = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}; vs = {fb(model, 'VSa'), fb(model, 'VSb'), fb(model, 'VSc')};
ld = fb(model, 'Three-Phase Series RLC Load'); ef = fb(model, 'External_Fault'); st4 = fb(model, 'Step4');
setBurden = @(mult) setBurdenAll(model, ctn, mult * burden0);
setLoad = @(pct, pf) set_param(ld, 'ActivePower', sprintf('%.6g', pct / 100 * S * pf), 'InductivePower', sprintf('%.6g', pct / 100 * S * sqrt(1 - pf ^ 2)), 'CapacitivePower', '0');
setPhase = @(deg) setPhaseAll(vs, deg);
run = @(stop) sim(model, 'StopTime', sprintf('%.3f', stop), 'ReturnWorkspaceOutputs', 'on');
fid = fopen(fullfile(thisDir, sprintf('plant_v5_checks_%s.txt', upper(plant))), 'w');
fprintf(fid, 'PLANT %s v5 PHYSICS CHECK (%s), %s\nRated line current HV %.2f A, LV %.2f A (S = %.0f MVA, %.0f / %.0f kV). TRUE currents from the V-I blocks, own time base.\n\n', upper(plant), model, datestr(now), Ihv, Ilv, S / 1e6, Vhv / 1e3, Vlv / 1e3); %#ok<TNOW1,DATST>
ok = struct();

% ---------- load cases (steady state, window 0.4-0.6 s) ----------
setPhase(30); setBurden(1); setLoad(100, 1.0);
o = run(0.6); [vL, tv] = sig(o, 'TR2_out1'); [iH, tH] = sig(o, 'TR1_out2'); [iL, tL] = sig(o, 'TR2_out2');
Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc')); t1 = (0:size(Ip, 1) - 1)' * ts;
w = @(t) t >= 0.4 & t <= 0.6;
vpu = mean(rms(vL(w(tv), :))) / Vlv; rHVtrue = mean(rms(iH(w(tH), :))); rLVtrue = mean(rms(iL(w(tL), :)));
ctHV = mean(rms(Ip(w(t1), :))); ctLV = mean(rms(Is(w(t1), :)));
ratioHV = rHVtrue / ctHV; ratioLV = rLVtrue / ctLV; Inom = Ihv / ratioHV; InomLV = Ilv / ratioLV;
fprintf(fid, '1. 100 %% LOAD, pf 1.0, burden 1 x:\n   TRUE LV voltage %.4f pu | TRUE line current HV %.3f pu, LV %.3f pu | measured CT ratio HV %.4f:1, LV %.4f:1 | rated CT secondary HV %.4f A, LV %.4f A\n', vpu, rHVtrue / Ihv, rLVtrue / Ilv, ratioHV, ratioLV, Inom, InomLV);
ok.c1 = vpu >= 0.95; fprintf(fid, '   C1 LV voltage >= 0.95 pu: %s\n\n', pf(ok.c1));
setLoad(100, 0.9); o = run(0.6); [vL, tv] = sig(o, 'TR2_out1');
fprintf(fid, '   (same load at pf 0.9: TRUE LV voltage %.4f pu)\n\n', mean(rms(vL(w(tv), :))) / Vlv);

resid = nan(1, 3); linr = nan(1, 3); k = 0;
for cfgc = [100 1; 150 1; 150 3]'
    k = k + 1; setLoad(cfgc(1), 0.9); setBurden(cfgc(2)); o = run(0.6);
    [iH, tH] = sig(o, 'TR1_out2'); [iL, tL] = sig(o, 'TR2_out2'); Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc'));
    rh = mean(rms(iH(w(tH), :))) / mean(rms(Ip(w(t1), :))); rl = mean(rms(iL(w(tL), :))) / mean(rms(Is(w(t1), :)));
    linr(k) = 0.5 * (rh / ratioHV + rl / ratioLV);
    % per-unit compensated differential
    if strcmp(side, 'hv'), d = (Is / InomLV) - (Ip / Inom) * Msd.'; else, d = (Is / InomLV) * Msd.' - (Ip / Inom); end
    resid(k) = max(rms(d(w(t1), :)));
    fprintf(fid, '2.%d LOAD %d %% (pf 0.9), burden %d x: CT ratio / ratio at 100 %% load = %.4f | normal differential residual (max phase) %.4f pu\n', k, cfgc(1), cfgc(2), linr(k), resid(k));
end
ok.c6 = abs(linr(3) - 1) < 0.02 && max(resid) < 0.05;
fprintf(fid, '   C6 linear to 150 %% load at 3 x burden (ratio change < 2 %%) and residual < 0.05 pu: %s\n\n', pf(ok.c6));

% ---------- through-faults (external 3-phase solid at t = 0.3 s) ----------
% A 3-phase fault cannot be symmetrical in all phases: at 90 deg phase A has no DC offset, B and C have. EARLY window 0.30-0.34 s (first two cycles, DC offset present),
% STEADY window 0.40-0.46 s (offset decayed). CT deviation = max over phases of rms(ratio*CT - true) / rms(true).
set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(st4, 'Time', '0.3', 'Before', '0', 'After', '1'); setLoad(100, 0.9);
cases = {'inception at voltage peak (90 deg)', 90, 1; 'inception at voltage zero (0 deg, maximum DC offset)', 0, 1; 'inception at voltage peak, 4 x burden', 90, 4};
devE = nan(3, 2); devS = nan(3, 2); trueS = nan(1, 3); trueE = nan(1, 3);
for c = 1:3
    setPhase(cases{c, 2}); setBurden(cases{c, 3}); o = run(0.5);
    [iH, tH] = sig(o, 'TR1_out2'); [iL, tL] = sig(o, 'TR2_out2'); Ip = ga(o.get('I_primary_abc')); Is = ga(o.get('I_secondary_abc'));
    for wv = 1:2
        if wv == 1, lo = 0.30; hi = 0.34; else, lo = 0.40; hi = 0.46; end
        sel = t1 >= lo & t1 <= hi; tq = t1(sel); iHq = interp1(tH, iH, tq); iLq = interp1(tL, iL, tq);
        eH = max(sqrt(mean((ratioHV * Ip(sel, :) - iHq) .^ 2, 1)) ./ sqrt(mean(iHq .^ 2, 1)));
        eL = max(sqrt(mean((ratioLV * Is(sel, :) - iLq) .^ 2, 1)) ./ sqrt(mean(iLq .^ 2, 1)));
        trueRmsW = 0.5 * (mean(rms(iHq)) / Ihv + mean(rms(iLq)) / Ilv);
        if wv == 1, devE(c, :) = 100 * [eH eL]; trueE(c) = trueRmsW; else, devS(c, :) = 100 * [eH eL]; trueS(c) = trueRmsW; end
    end
    fprintf(fid, '3.%d THROUGH-FAULT, %s, burden %d x: TRUE RMS steady %.2f pu (first two cycles %.2f pu) | CT deviation first two cycles HV %.1f %%, LV %.1f %% | steady HV %.1f %%, LV %.1f %%\n', ...
        c, cases{c, 1}, cases{c, 3}, trueS(c), trueE(c), devE(c, 1), devE(c, 2), devS(c, 1), devS(c, 2));
end
ok.c2 = trueS(1) >= 7 && trueS(1) <= 15; ok.c3 = max(devS(1, :)) < 5; ok.c4 = max(devE(2, :)) > 10; ok.c5 = max(devE(3, :)) > 10;
fprintf(fid, '   C2 TRUE steady through-fault 7-15 pu RMS (%.2f pu): %s\n   C3 CTs linear in the steady state at nominal burden (max deviation %.1f %% < 5 %%): %s\n', trueS(1), pf(ok.c2), max(devS(1, :)), pf(ok.c3));
fprintf(fid, '   C4 maximum DC offset saturates a CT in the first two cycles (max deviation %.1f %% > 10 %%): %s\n   C5 4 x burden saturates in the first two cycles (max deviation %.1f %% > 10 %%): %s\n\n', max(devE(2, :)), pf(ok.c4), max(devE(3, :)), pf(ok.c5));
trueRms = trueS;
allok = all(structfun(@(x) x, ok));
fprintf(fid, 'OVERALL: %s\n', pf(allok)); fclose(fid); type(fullfile(thisDir, sprintf('plant_v5_checks_%s.txt', upper(plant))));
res = struct('ratioHV', ratioHV, 'ratioLV', ratioLV, 'InomHV', Inom, 'InomLV', InomLV, 'trueSym', trueS(1), 'ok', ok);
end

function s = pf(b)
if b, s = 'PASS'; else, s = 'FAIL'; end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
function [v, t] = sig(o, name)
el = o.get('logsout').get(name); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
t = el.Values.Time; v = squeeze(double(el.Values.Data)); if size(v, 1) ~= numel(t), v = v.'; end
end
function x = ga(v)
if isa(v, 'timeseries'), x = squeeze(double(v.Data)); elseif isstruct(v), x = squeeze(double(v.signals.values)); else, x = squeeze(double(v)); end
if size(x, 2) ~= 3 && size(x, 1) == 3, x = x.'; end
end

function setBurdenAll(model, ctn, ohm)
for k = 1:6
    c = find_system(model, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
    nn = @(x) strtrim(regexprep(get_param(x, 'Name'), '\s+', ' '));
    parent = c(strcmp(cellfun(nn, c, 'UniformOutput', false), ctn{k})); b = find_system(parent{1}, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Name', '1ohm');
    set_param(b{1}, 'Resistance', sprintf('%.6g', ohm));
end
end
function setPhaseAll(vs, deg)
ph0 = [0 -120 120];
for k = 1:3, set_param(vs{k}, 'Phase', sprintf('%.6g', deg + ph0(k))); end
end
