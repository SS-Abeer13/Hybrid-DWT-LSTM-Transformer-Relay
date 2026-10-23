function fix_ai_solo_trip(soloThreshold, saveChanges)
%FIX_AI_SOLO_TRIP Option 2: let the LSTM trip ALONE when its confirmed score is very high.
%
% Before: trip = high-set OR (any-phase 87T vote AND confirmed LSTM >= AI_Threshold). With the corrected 87T calibration the 87T never
% votes on high-impedance / weak internal faults, so the AI (veto-only) could not trip them (dependability 74.5 %).
% After:  trip = high-set OR (87T vote AND LSTM >= AI_Threshold) OR LSTM >= AI_Solo_Threshold.
% 'lstm_conf' is the CONFIRMED score (minimum of the last cfg.AI_DWELL network outputs), so the solo path also needs the dwell.
% AI_Solo_Threshold is validation-tuned (lstm_models/train_trace_split.py --solo; runs/.../decision_solo_threshold.txt), and must be >= AI_Threshold.
% Fallback mode (lstm_conf == -1) is unchanged: AI disabled, 87T decides alone.
%
%   fix_ai_solo_trip(str2double(fileread('..\runs\20261020_multiseed_v3_solo\seed_20261018\decision_solo_threshold.txt')), true)

if nargin < 2, saveChanges = false; end
assert(isscalar(soloThreshold) && soloThreshold > 0.5 && soloThreshold < 1, 'solo threshold must be in (0.5, 1)');
model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
if ~bdIsLoaded(model), load_system(fullfile(thisDir, [model '.slx'])); end

charts = sfroot().find('-isa', 'Stateflow.EMChart');
hit = [];
for c = charts(:).'
    if contains(c.Script, 'AI_Threshold') && contains(c.Script, 'Hybrid_87T_Decision'), hit = c; end
end
assert(~isempty(hit), 'Hybrid_87T_Decision chart not found');
s = hit.Script;
aiThr = str2double(regexp(s, 'AI_Threshold\s*=\s*([0-9.]+)\s*;', 'tokens', 'once'));
assert(soloThreshold >= aiThr, 'AI_Solo_Threshold (%.4f) must be >= AI_Threshold (%.4f)', soloThreshold, aiThr);

if contains(s, 'AI_Solo_Threshold')
    s = regexprep(s, 'AI_Solo_Threshold\s*=\s*[0-9.]+\s*;', sprintf('AI_Solo_Threshold = %.4f;', soloThreshold), 'once');
else
    s = regexprep(s, '(AI_Threshold\s*=\s*[0-9.]+\s*;)', ...
        sprintf('$1\n    AI_Solo_Threshold = %.4f;   %% option 2: AI-alone trip (no 87T vote needed)', soloThreshold), 'once');
    soloBlock = sprintf(['\n    %% --- AI-ALONE PATH (option 2): a very high CONFIRMED LSTM score trips without an 87T vote ---\n' ...
        '    if Trip_Signal == 0 && lstm_conf ~= -1 && lstm_conf >= AI_Solo_Threshold\n' ...
        '        Trip_Signal = 1;\n    end\n']);
    ix = regexp(s, '\n\s*end\s*$', 'once');           % the final 'end' of the function
    assert(~isempty(ix), 'could not find the end of the function');
    s = [s(1:ix-1) soloBlock s(ix:end)];
end
hit.Script = s;

% ---- self-test of the chart logic (the function text is evaluated stand-alone) ----------------
tmp = fullfile(tempdir, 'Hybrid_87T_Decision.m');
fid = fopen(tmp, 'w'); fwrite(fid, s); fclose(fid);
old = cd(tempdir); cleanup = onCleanup(@() cd(old)); clear Hybrid_87T_Decision
z = [0 0 0]'; hi = [0.5 0 0]'; r = [1 1 1]';
chk = @(v, e, msg) assert(v == e, 'chart self-test failed: %s', msg);
chk(Hybrid_87T_Decision(z, r, 0.0), 0, 'quiet');
chk(Hybrid_87T_Decision(hi, r, 0.0), 0, '87T vote, AI veto');
chk(Hybrid_87T_Decision(hi, r, aiThr + 1e-4), 1, '87T vote + AI confirm');
chk(Hybrid_87T_Decision(z, r, aiThr + 1e-4), 0, 'AI confirm but no 87T vote and below solo threshold');
chk(Hybrid_87T_Decision(z, r, soloThreshold + 1e-5 * (soloThreshold < 0.99999)), 1, 'AI-alone trip');
chk(Hybrid_87T_Decision([20 0 0]', r, 0.0), 1, 'high-set');
chk(Hybrid_87T_Decision(hi, r, -1), 1, 'fallback: 87T alone');
chk(Hybrid_87T_Decision(z, r, -1), 0, 'fallback: quiet');
fprintf('Decision chart updated: AI_Threshold %.4f, AI_Solo_Threshold %.4f; 8 self-tests passed.\n', aiThr, soloThreshold);

if saveChanges
    save_system(model);
    fprintf('Saved %s.\n', model);
else
    fprintf('Applied to the loaded model only (not saved).\n');
end
end
