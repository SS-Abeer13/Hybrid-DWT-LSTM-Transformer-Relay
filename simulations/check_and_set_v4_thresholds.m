function check_and_set_v4_thresholds()
% CHECK_AND_SET_V4_THRESHOLDS Set the Phase 2.2 calibrated thresholds in
% TransformerWithCTSaturation_v4.slx's Hybrid_87T_Decision chart.
%
% Values from runs/20261027_v4_final:
%   ai_threshold   = 0.9950
%   solo_threshold = 0.9990

thisDir = fileparts(mfilename('fullpath'));
model = 'TransformerWithCTSaturation_v4';
slxPath = fullfile(thisDir, [model '.slx']);

fprintf('Checking/Setting thresholds in %s...\n', slxPath);

if ~bdIsLoaded(model)
    load_system(slxPath);
end

charts = sfroot().find('-isa', 'Stateflow.EMChart');
hit = [];
for c = charts(:).'
    if contains(c.Path, model) && (contains(c.Script, 'Hybrid_87T_Decision') || contains(c.Script, 'AI_Threshold'))
        hit = c;
        break;
    end
end
assert(~isempty(hit), 'Hybrid_87T_Decision chart not found in %s', model);

s = hit.Script;
fprintf('Current Chart Script excerpts:\n');
lines = splitlines(s);
for i = 1:numel(lines)
    if contains(lines{i}, 'AI_Threshold') || contains(lines{i}, 'AI_Solo_Threshold')
        disp(lines{i});
    end
end

% Set AI_Threshold = 0.9950
s = regexprep(s, 'AI_Threshold\s*=\s*[0-9.]+\s*;', 'AI_Threshold = 0.9950;', 'once');

% Set AI_Solo_Threshold = 0.9990
if contains(s, 'AI_Solo_Threshold')
    s = regexprep(s, 'AI_Solo_Threshold\s*=\s*[0-9.]+\s*;', 'AI_Solo_Threshold = 0.9990;', 'once');
else
    s = regexprep(s, '(AI_Threshold\s*=\s*[0-9.]+\s*;)', ...
        sprintf('$1\n    AI_Solo_Threshold = 0.9990;   %% AI-alone trip path'), 'once');
    soloBlock = sprintf(['\n    %% --- AI-ALONE PATH: a very high CONFIRMED LSTM score trips without an 87T vote ---\n' ...
        '    if Trip_Signal == 0 && lstm_conf ~= -1 && lstm_conf >= AI_Solo_Threshold\n' ...
        '        Trip_Signal = 1;\n    end\n']);
    ix = regexp(s, '\n\s*end\s*$', 'once');
    assert(~isempty(ix), 'could not find end of function');
    s = [s(1:ix-1) soloBlock s(ix:end)];
end

hit.Script = s;
save_system(model);
fprintf('Updated and saved %s successfully with AI_Threshold=0.9950 and AI_Solo_Threshold=0.9990.\n', model);

setappdata(0, 'HybridRelaySkipLSTM', true);
set_param(model, 'SimulationCommand', 'update');
fprintf('Model diagram compiled successfully!\n');

close_system(model, 0);
end
