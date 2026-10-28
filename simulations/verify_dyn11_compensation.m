% verify_dyn11_compensation.m
model = 'TransformerB_v4';
load_system(model);
setappdata(0, 'HybridRelaySkipLSTM', true);
c = onCleanup(@() close_system(model, 0));

% Set breakers closed and load active using robust fb()
hv = fb(model, 'Three-Phase Breaker');
lv = fb(model, 'Three-Phase Breaker1');
set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');

ld = fb(model, 'Three-Phase Series RLC Load');
set_param(ld, 'NominalVoltage', '33e3', ...
             'ActivePower', sprintf('%.6g', 40e6 * 0.95), ...
             'InductivePower', sprintf('%.6g', 40e6 * sqrt(1 - 0.95^2)), ...
             'CapacitivePower', '0');

out = sim(model, 'StopTime', '0.4', 'ReturnWorkspaceOutputs', 'on');
Ip = ga(out.get('I_primary_abc'));
Is = ga(out.get('I_secondary_abc'));
ts = 6.25e-4;
t = (0:size(Ip,1)-1)' * ts;
ss = (t >= 0.3 & t <= 0.38);

fprintf('Ip size: %s, mean RMS: %.4f A\n', mat2str(size(Ip)), mean(rms(Ip(ss, :))));
fprintf('Is size: %s, mean RMS: %.4f A\n', mat2str(size(Is)), mean(rms(Is(ss, :))));

I_base = 0.8232;
Ip_pu = Ip(ss, :) / I_base;
Is_pu = Is(ss, :) / I_base;

% Test various standard matrices:
% M1: (1/sqrt3) * [1 0 -1; -1 1 0; 0 -1 1]
% M2: (1/sqrt3) * [1 -1 0; 0 1 -1; -1 0 1]
% M3: (1/sqrt3) * [-1 0 1; 1 -1 0; 0 1 -1]
% M4: (1/sqrt3) * [-1 1 0; 0 -1 1; 1 0 -1]
% M5: transpose of M1
% M6: negative of M1

M_cands = {
    (1/sqrt(3)) * [1 0 -1; -1 1 0; 0 -1 1], ...
    (1/sqrt(3)) * [1 -1 0; 0 1 -1; -1 0 1], ...
    (1/sqrt(3)) * [-1 0 1; 1 -1 0; 0 1 -1], ...
    (1/sqrt(3)) * [-1 1 0; 0 -1 1; 1 0 -1], ...
    (1/sqrt(3)) * [1 -1 0; -1 1 0; 0 -1 1].', ...
    (1/sqrt(3)) * [0 1 -1; -1 0 1; 1 -1 0], ...
};

for i = 1:length(M_cands)
    M = M_cands{i};
    % Test applying to LV: Idiff = Is * M' - Ip
    Idiff_lv = Is_pu * M.' - Ip_pu;
    rms_lv = rms(Idiff_lv);
    
    % Test applying to HV: Idiff = Is - Ip * M'
    Idiff_hv = Is_pu - Ip_pu * M.';
    rms_hv = rms(Idiff_hv);
    
    % Test negative: Idiff = -Is * M' - Ip
    Idiff_lv_neg = (-Is_pu * M.') - Ip_pu;
    rms_lv_neg = rms(Idiff_lv_neg);

    Idiff_hv_neg = Is_pu - (-Ip_pu * M.');
    rms_hv_neg = rms(Idiff_hv_neg);

    fprintf('M%d: max RMS (M on LV)=%.4f pu | (M on HV)=%.4f pu | (neg M on LV)=%.4f pu | (neg M on HV)=%.4f pu\n', ...
        i, max(rms_lv), max(rms_hv), max(rms_lv_neg), max(rms_hv_neg));
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times', name, numel(hit));
blk = hit{1};
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
