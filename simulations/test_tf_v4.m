model = 'TransformerWithCTSaturation_v4';
load_system(model);
cleanup = onCleanup(@() finish(model));

setappdata(0, 'HybridRelaySkipLSTM', true);

hv = findBlock(model, 'Three-Phase Breaker');
lv = findBlock(model, 'Three-Phase Breaker1');
set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');

extFault = findBlock(model, 'External_Fault');
extStep = findBlock(model, 'Step4');
set_param(extFault, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', ...
    'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(extStep, 'Time', '0.3', 'Before', '0', 'After', '1');

out = sim(model, 'StopTime', '0.5');
Ip = double(out.get('I_primary_abc'));
Is = double(out.get('I_secondary_abc'));

ts = 6.25e-4; % 1600 Hz sample time
t = (0:size(Ip, 1)-1)' * ts;

idx = (t >= 0.32 & t <= 0.45);
Isec_base = 1.8610;

hv_rms = rms(Ip(idx, :));
lv_rms = rms(Is(idx, :));

fprintf('===============================================\n');
fprintf('EXTERNAL 3-PHASE THROUGH-FAULT CURRENT CHECK:\n');
fprintf('===============================================\n');
fprintf('Fault window: t = 0.32 - 0.45 s (%d samples at 1600 Hz)\n', sum(idx));
fprintf('HV CT Secondary RMS: A=%.2f A, B=%.2f A, C=%.2f A (Mean: %.2f A)\n', ...
    hv_rms(1), hv_rms(2), hv_rms(3), mean(hv_rms));
fprintf('LV CT Secondary RMS: A=%.2f A, B=%.2f A, C=%.2f A (Mean: %.2f A)\n', ...
    lv_rms(1), lv_rms(2), lv_rms(3), mean(lv_rms));
fprintf('Through-Fault Current in Per Unit (HV CT): %.2f pu (Range: %.2f - %.2f pu)\n', ...
    mean(hv_rms)/Isec_base, min(hv_rms)/Isec_base, max(hv_rms)/Isec_base);
fprintf('Through-Fault Current in Per Unit (LV CT): %.2f pu (Range: %.2f - %.2f pu)\n', ...
    mean(lv_rms)/Isec_base, min(lv_rms)/Isec_base, max(lv_rms)/Isec_base);

% Pre-fault load current check (t = 0.15 - 0.25 s)
pre_idx = (t >= 0.15 & t <= 0.25);
pre_hv = rms(Ip(pre_idx, :));
pre_lv = rms(Is(pre_idx, :));
fprintf('Pre-fault load (t = 0.15 - 0.25 s): HV = %.2f A (%.2f pu), LV = %.2f A (%.2f pu)\n', ...
    mean(pre_hv), mean(pre_hv)/Isec_base, mean(pre_lv), mean(pre_lv)/Isec_base);
fprintf('Fault multiplication factor: HV = %.2fx, LV = %.2fx\n', ...
    mean(hv_rms)/mean(pre_hv), mean(lv_rms)/mean(pre_lv));
fprintf('===============================================\n');

function blk = findBlock(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
normName = @(s) strtrim(regexprep(s, '\s+', ' '));
hit = c(strcmp(cellfun(@(s) normName(get_param(s, 'Name')), c, 'UniformOutput', false), normName(name)));
hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'CalLoad:Block', 'Expected exactly one block "%s" under %s, found %d.', name, parent, numel(hit));
blk = hit{1};
end

function finish(model)
if isappdata(0, 'HybridRelaySkipLSTM'), rmappdata(0, 'HybridRelaySkipLSTM'); end
if bdIsLoaded(model), close_system(model, 0); end
end
