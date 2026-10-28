function probe_flux_demand_v5()
%PROBE_FLUX_DEMAND_V5 Flux demand of the LV CT on an external 3-phase solid fault, from the TRUE current: phi = integral( i_true/ratio * (Zburden + R2) ) dt, AC-coupled,
% in units of the CT's rated-voltage flux (V2_rated * sqrt(2) / omega). Both v5 plants, saturation knee made huge so the CT is ideal (in memory only).
plants = {'A', 'TransformerWithCTSaturation_v5', 1.0, 5.0, 0.2, 300e6, 11e3; 'B', 'TransformerB_v5', 2.5, 2.5, 0.05, 40e6, 33e3};
thisDir = fileparts(mfilename('fullpath')); ts = 1 / 1600;
for pi_ = 2
    [nm, model, burden0, V2rated, R2pu, S, Vlv] = plants{pi_, :};
    bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
    setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
    for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
    ph = get_param(fb(model, 'Secondary_side'), 'PortHandles'); set_param(ph.Outport(2), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'IL');
    set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
    set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
    nmu = fb(model, 'Noise Merging Unit');
    for k = 1:6, set_param(fb(nmu, sprintf('Noise_Gain_%d', k)), 'Gain', '0'); set_param(fb(nmu, sprintf('CT_Gain_Mismatch_%d', k)), 'Gain', '1'); end
    ef = fb(model, 'External_Fault'); set_param(ef, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', 'FaultResistance', '0.001', 'GroundResistance', '0.001');
    set_param(fb(model, 'Step4'), 'Time', '0.3', 'Before', '0', 'After', '1');
    ld = fb(model, 'Three-Phase Series RLC Load'); set_param(ld, 'ActivePower', sprintf('%.6g', 0.9 * S), 'InductivePower', sprintf('%.6g', S * sqrt(1 - 0.81)), 'CapacitivePower', '0');
    o = sim(model, 'StopTime', '0.5', 'ReturnWorkspaceOutputs', 'on'); el = o.get('logsout').get('IL'); if isa(el, 'Simulink.SimulationData.Dataset'), el = el{1}; end
    t = el.Values.Time; i = squeeze(double(el.Values.Data)); if size(i, 1) ~= numel(t), i = i.'; end
    Ilv = S / (sqrt(3) * Vlv);
    % nominal ratio of the LV CT (true / secondary): rated line current / rated CT secondary; secondary rated = 1 A (B) or measured 1.861 A (A)
    if strcmp(nm, 'A'), I2rated = 1.861; else, I2rated = 0.8664; end
    ratio = Ilv / I2rated; Zt = burden0 + R2pu * (V2rated ^ 2 / (V2rated * (V2rated / burden0)));   % burden + R2 (R2 pu on the CT base Zb = V2^2/S)
    Zb_base = V2rated ^ 2 / (strcmp(nm, 'A') * 25 + strcmp(nm, 'B') * 2.5); Zt = burden0 + R2pu * Zb_base;
    i2 = i / ratio; v = i2 * Zt; omega = 2 * pi * 50; base = V2rated * sqrt(2) / omega;
    for lohi = [0.30 0.34; 0.30 0.50]'
        sel = t >= lohi(1) & t <= lohi(2); tt = t(sel); phi = zeros(sum(sel), 3);
        for c = 1:3, vv = v(sel, c); phi(:, c) = cumtrapz(tt, vv); phi(:, c) = phi(:, c) - mean(phi(:, c)); end
        fprintf('plant %s: ideal-CT secondary %.2f A rms (rated sec %.3f A), burden+R2 = %.3f ohm, V2 rated %.1f V -> peak flux demand in window %.2f-%.2f s: %.1f pu of rated-voltage flux\n', ...
            nm, mean(rms(i2(t >= 0.4 & t <= 0.46, :))), I2rated, Zt, V2rated, lohi(1), lohi(2), max(abs(phi), [], 'all') / base);
    end
end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
