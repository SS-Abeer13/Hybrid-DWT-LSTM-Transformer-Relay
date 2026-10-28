% check_phase_angles_plant_b.m
model = 'TransformerB_v4';
load_system(model);
setappdata(0, 'HybridRelaySkipLSTM', true);
c = onCleanup(@() close_system(model, 0));

out = sim(model, 'StopTime', '0.4', 'ReturnWorkspaceOutputs', 'on');
Ip = ga(out.get('I_primary_abc'));
Is = ga(out.get('I_secondary_abc'));
ts = 6.25e-4;
t = (0:size(Ip,1)-1)' * ts;
idx = (t >= 0.3 & t <= 0.38);

% FFT on steady-state window of 32 samples (one 50 Hz cycle)
win_p = Ip(end-31:end, :);
win_s = Is(end-31:end, :);

F_p = fft(win_p, [], 1);
F_s = fft(win_s, [], 1);

% 50 Hz fundamental is at index 2 (1-based)
fund_p = F_p(2, :);
fund_s = F_s(2, :);

fprintf('=== PLANT B FUNDAMENTAL CURRENT PHASORS ===\n');
for ph = 1:3
    fprintf('Phase %c:\n', 'A' + ph - 1);
    fprintf('  HV: Mag = %.4f A, Angle = %.2f deg\n', abs(fund_p(ph))/16, angle(fund_p(ph))*180/pi);
    fprintf('  LV: Mag = %.4f A, Angle = %.2f deg\n', abs(fund_s(ph))/16, angle(fund_s(ph))*180/pi);
    fprintf('  Angle Difference (LV - HV) = %.2f deg\n', (angle(fund_s(ph)) - angle(fund_p(ph)))*180/pi);
end

% Test transformations
M1 = (1/sqrt(3)) * [1 0 -1; -1 1 0; 0 -1 1];
M2 = (1/sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1];
M3 = (1/sqrt(3)) * [-1 0 1; 1 -1 0; 0 1 -1];
M4 = (1/sqrt(3)) * [-1 1 0; 0 -1 1; 1 0 -1];

matrices = {M1, M2, M3, M4};
for m_idx = 1:4
    M = matrices{m_idx};
    % Test applying to LV: I_diff = M * I_lv - I_hv
    I_lv_comp = (fund_s / 0.8212) * M.';
    I_hv_comp = (fund_p / 0.8252);
    diff = I_lv_comp - I_hv_comp;
    fprintf('Matrix M%d applied to LV: Residual |Idiff| = [%.4f, %.4f, %.4f] pu\n', ...
        m_idx, abs(diff));
    
    % Test applying to HV: I_diff = I_lv - M * I_hv
    I_hv_comp2 = (fund_p / 0.8252) * M.';
    I_lv_comp2 = (fund_s / 0.8212);
    diff2 = I_lv_comp2 - I_hv_comp2;
    fprintf('Matrix M%d applied to HV: Residual |Idiff| = [%.4f, %.4f, %.4f] pu\n', ...
        m_idx, abs(diff2));
end

function x = ga(v)
if isa(v, 'timeseries'), x = double(v.Data); elseif isstruct(v), x = double(v.signals.values); else, x = double(v); end
end
