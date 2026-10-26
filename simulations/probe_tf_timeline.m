load_system('TransformerWithCTSaturation_v4');
cleanup = onCleanup(@() finish('TransformerWithCTSaturation_v4'));
setappdata(0, 'HybridRelaySkipLSTM', true);

hv = findBlock('TransformerWithCTSaturation_v4', 'Three-Phase Breaker');
lv = findBlock('TransformerWithCTSaturation_v4', 'Three-Phase Breaker1');
set_param(hv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');
set_param(lv, 'External', 'off', 'InitialState', 'closed', 'SwitchTimes', '[10 11]');

extFault = findBlock('TransformerWithCTSaturation_v4', 'External_Fault');
extStep = findBlock('TransformerWithCTSaturation_v4', 'Step4');
set_param(extFault, 'FaultA', 'on', 'FaultB', 'on', 'FaultC', 'on', 'GroundFault', 'on', ...
    'FaultResistance', '0.001', 'GroundResistance', '0.001');
set_param(extStep, 'Time', '0.3', 'Before', '0', 'After', '1');

out = sim('TransformerWithCTSaturation_v4', 'StopTime', '0.45');
t = out.tout;
Ip = double(out.get('I_primary_abc'));
Is = double(out.get('I_secondary_abc'));

fprintf('Sample times and currents:\n');
for tm = [0.1, 0.25, 0.29, 0.30, 0.31, 0.32, 0.35, 0.40]
    [~, k] = min(abs(t - tm));
    fprintf('t = %.3f s: Ip = [%.2f, %.2f, %.2f], Is = [%.2f, %.2f, %.2f]\n', ...
        t(k), Ip(k,1), Ip(k,2), Ip(k,3), Is(k,1), Is(k,2), Is(k,3));
end

function blk = findBlock(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
normName = @(s) strtrim(regexprep(s, '\s+', ' '));
hit = c(strcmp(cellfun(@(s) normName(get_param(s, 'Name')), c, 'UniformOutput', false), normName(name)));
hit = hit(~strcmp(hit, parent));
blk = hit{1};
end

function finish(model)
if isappdata(0, 'HybridRelaySkipLSTM'), rmappdata(0, 'HybridRelaySkipLSTM'); end
if bdIsLoaded(model), close_system(model, 0); end
end
