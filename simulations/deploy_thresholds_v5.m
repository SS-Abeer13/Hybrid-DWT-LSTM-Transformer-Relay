function deploy_thresholds_v5(aiThr, soloThr)
%DEPLOY_THRESHOLDS_V5 Write the validation-tuned thresholds of runs/20261029_v5_final into the Hybrid_87T_Decision chart of both v5 models.
%   deploy_thresholds_v5(0.9950, 0.9980)
% Only the two numbers change. Each model is reloaded pristine, edited, saved, reloaded and re-checked; breaker SwitchTimes must still be '[]'.
assert(soloThr >= aiThr && aiThr > 0.5 && soloThr < 1);
thisDir = fileparts(mfilename('fullpath'));
for m = {'TransformerWithCTSaturation_v5', 'TransformerB_v5'}
    model = m{1}; f = fullfile(thisDir, [model '.slx']);
    bdclose('all'); load_system(f);
    chs = sfroot().find('-isa', 'Stateflow.EMChart');
    chs = chs(arrayfun(@(c) startsWith(c.Path, [model '/']) && contains(c.Script, 'AI_Threshold') && contains(c.Script, 'AI_Solo_Threshold'), chs));
    assert(numel(chs) == 1, '%s: Hybrid_87T_Decision chart found %d times', model, numel(chs));
    s = chs.Script;
    s = regexprep(s, 'AI_Threshold\s*=\s*[0-9.]+\s*;', sprintf('AI_Threshold = %.4f;', aiThr), 'once');
    s = regexprep(s, 'AI_Solo_Threshold\s*=\s*[0-9.]+\s*;', sprintf('AI_Solo_Threshold = %.4f;', soloThr), 'once');
    chs.Script = s;
    save_system(model); close_system(model, 0);
    load_system(f);
    chs = sfroot().find('-isa', 'Stateflow.EMChart');
    chs = chs(arrayfun(@(c) startsWith(c.Path, [model '/']) && contains(c.Script, 'AI_Solo_Threshold'), chs));
    s = chs.Script;
    a = str2double(regexp(s, 'AI_Threshold\s*=\s*([0-9.]+)\s*;', 'tokens', 'once')); b = str2double(regexp(s, 'AI_Solo_Threshold\s*=\s*([0-9.]+)\s*;', 'tokens', 'once'));
    assert(abs(a - aiThr) < 1e-9 && abs(b - soloThr) < 1e-9, 'read-back failed');
    assert(strcmp(get_param(fb(model, 'Three-Phase Breaker'), 'SwitchTimes'), '[]'), 'breaker settings changed');
    close_system(model, 0);
    fprintf('%s: AI_Threshold %.4f, AI_Solo_Threshold %.4f verified in the saved file\n', model, a, b);
end
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
