function report = verify_feature_parity_v5(plant)
%VERIFY_FEATURE_PARITY_V5 The 12 features the relay chart computes in the v5 plant model vs the offline recomputation (per-unit normalisation).
%   verify_feature_parity_v5('A') | ('B'). Normal and an internal A-G case. PASS = max abs error < 1e-5 (allowing +/-3 samples of log alignment).
% The model is NEVER saved (all changes are in memory; close_system(model, 0)).
if strcmpi(plant, 'A')
    model = 'TransformerWithCTSaturation_v5'; I_base = 1.8610; Mc = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1]; side = 'primary'; S = 300e6;
else
    model = 'TransformerB_v5'; I_base = 0.8658; Mc = (1 / sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1]; side = 'secondary'; S = 40e6; plant = 'B';
end
thisDir = fileparts(mfilename('fullpath'));
bdclose('all'); load_system(fullfile(thisDir, [model '.slx'])); cleanup = onCleanup(@() bdclose('all')); %#ok<NASGU>
setappdata(0, 'HybridRelaySkipLSTM', true); c2 = onCleanup(@() rmappdata(0, 'HybridRelaySkipLSTM')); %#ok<NASGU>
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}, try, set_param(model, m{1}, 'none'); catch, end, end %#ok<NOCOM>
relay = fb(model, 'Hybrid 87T Relay');
ph = get_param(fb(relay, 'DWT Feature Extraction'), 'PortHandles');
set_param(ph.Outport(1), 'DataLogging', 'on', 'DataLoggingNameMode', 'Custom', 'DataLoggingName', 'DWT_Features_Row');
set_param(fb(model, 'Three-Phase Breaker'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(fb(model, 'Three-Phase Breaker1'), 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
for nm = {'Internal_Fault1', 'Internal_Fault2', 'Internal_Fault3', 'External_Fault'}
    set_param(fb(model, nm{1}), 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off');
end
for st = {'Step3', 'Step_Evolve2', 'Step_Evolve3', 'Step4'}, set_param(fb(model, st{1}), 'Time', '10', 'Before', '0', 'After', '1'); end
set_param(fb(model, 'Step3'), 'Time', '0.5');
ld = fb(model, 'Three-Phase Series RLC Load'); pf = 0.9;
set_param(ld, 'ActivePower', sprintf('%.6g', 0.6 * S * pf), 'InductivePower', sprintf('%.6g', 0.6 * S * sqrt(1 - pf ^ 2)), 'CapacitivePower', '0');
cases = {'Normal', false; 'Internal A-G', true};
report = struct('case', {}, 'maxAbsError', {}, 'bestShift', {}, 'pass', {});
for k = 1:2
    f1 = fb(model, 'Internal_Fault1');
    if cases{k, 2}, set_param(f1, 'FaultA', 'on', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'on', 'FaultResistance', '0.1');
    else, set_param(f1, 'FaultA', 'off', 'FaultB', 'off', 'FaultC', 'off', 'GroundFault', 'off'); end
    out = sim(model, 'StopTime', '1.0', 'ReturnWorkspaceOutputs', 'on');
    R = squeeze(double(out.get('logsout').get('DWT_Features_Row').Values.Data)); if size(R, 2) ~= 12, R = R.'; end
    Ip = tw(out, 'I_primary_abc'); Is = tw(out, 'I_secondary_abc');
    if strcmp(side, 'primary'), Idiff = (Ip * Mc - Is) / I_base;   % plant A: HV compensated
    else, Idiff = (Is * Mc.' - Ip) / I_base; end                    %#ok<UNRCH> plant B: LV compensated
    if strcmp(side, 'primary'), Idiff = (Ip * ((1 / sqrt(3)) * [1 0 -1; -1 1 0; 0 -1 1]).' - Is) / I_base; end
    T = features12(Idiff);
    best = inf; bestShift = 0; n = min(size(R, 1), size(T, 1)) - 10;
    for s = -3:3
        a = T(end - n + 1 + min(s, 0):end + min(s, 0), :); b = R(end - n + 1 - max(s, 0):end - max(s, 0), :);
        e = max(abs(a - b), [], 'all'); if e < best, best = e; bestShift = s; end
    end
    report(k) = struct('case', cases{k, 1}, 'maxAbsError', best, 'bestShift', bestShift, 'pass', best < 1e-5);
    fprintf('plant %s %-14s max |relay - offline| = %.3g (shift %+d)  %s\n', plant, cases{k, 1}, best, bestShift, ifelse(best < 1e-5, 'PASS', 'FAIL'));
end
end

function F = features12(I_diff)
W = 32; n = size(I_diff, 1); F = zeros(n - W, 12);
for t = (W + 1):n
    win = I_diff((t - W + 1):t, :);
    for p = 1:3
        [C, L] = wavedec(win(:, p), 2, 'db4'); b = (p - 1) * 3 + 1;
        F(t - W, b) = log(1 + sum(detcoef(C, L, 1) .^ 2)); F(t - W, b + 1) = log(1 + sum(detcoef(C, L, 2) .^ 2)); F(t - W, b + 2) = log(1 + sum(appcoef(C, L, 'db4', 2) .^ 2));
        v = abs(fft(win(:, p))); F(t - W, 9 + p) = min(v(3) / (v(2) + 1e-4), 2.0);
    end
end
end
function x = tw(out, name)
v = out.get(name);
if isa(v, 'timeseries'), x = squeeze(double(v.Data)); elseif isstruct(v), x = squeeze(double(v.signals.values)); else, x = squeeze(double(v)); end
if size(x, 2) ~= 3 && size(x, 1) == 3, x = x.'; end
end
function v = ifelse(c, a, b)
if c, v = a; else, v = b; end
end
function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
