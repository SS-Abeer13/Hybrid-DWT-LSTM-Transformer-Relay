function set_ai_threshold(threshold, saveChanges)
%SET_AI_THRESHOLD Write the validation-tuned LSTM threshold into the Simulink decision chart.
%
% The 'Hybrid_87T_Decision' chart hard-coded AI_Threshold = 0.50. The tuned
% threshold comes from lstm_models/train_trace_split.py (decision_threshold.txt
% in the run folder). Using 0.50 with a model tuned for ~0.9+ lets the 87T vote
% plus a mid-range LSTM score trip on inrush and external faults.
%
%   set_ai_threshold(str2double(fileread('..\runs\20261018_trace_split\decision_threshold.txt')), true)

if nargin < 2, saveChanges = false; end
assert(isscalar(threshold) && threshold > 0 && threshold < 1, 'Threshold must be in (0, 1).');
model = 'TransformerWithCTSaturation';
if ~bdIsLoaded(model), load_system(fullfile(fileparts(mfilename('fullpath')), [model '.slx'])); end

charts = sfroot().find('-isa', 'Stateflow.EMChart');
hit = false;
for c = charts(:).'
    if contains(c.Script, 'AI_Threshold')
        c.Script = regexprep(c.Script, 'AI_Threshold\s*=\s*[0-9.eE+-]+\s*;', ...
            sprintf('AI_Threshold = %.4f;', threshold), 'once');
        fprintf('Set AI_Threshold = %.4f in %s\n', threshold, c.Path);
        hit = true;
    end
end
assert(hit, 'No chart containing AI_Threshold was found.');
if saveChanges, save_system(model); end
end
