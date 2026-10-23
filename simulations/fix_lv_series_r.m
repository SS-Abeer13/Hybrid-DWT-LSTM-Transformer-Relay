function fix_lv_series_r(newR, saveChanges)
%FIX_LV_SERIES_R Lower the three LV series resistors ('Series RLC Branch', 'Series RLC Branch1', 'Series RLC Branch2').
%
% They sit between the transformer secondary (where the Internal_Fault blocks are) and the CT / breaker / load / External_Fault node,
% 0.5 ohm each = 1.24 pu on the 11 kV base. Effects measured with probe_lv_series.m (2026-10-21):
%   * LV bus voltage collapsed under load (0.63 pu at 62 % of rated current, 0.35 pu at 110 %),
%   * external faults were weak (3-phase solid: 1.5 pu rms through the CTs) - no real through-fault / CT saturation stress.
% With 0.02 ohm (0.05 pu): voltage 0.95 pu at 92 % rated, external 3-phase 7.5 pu rms. Internal faults are unchanged.
%   fix_lv_series_r(0.02, true)
if nargin < 1, newR = 0.02; end
if nargin < 2, saveChanges = false; end
model = 'TransformerWithCTSaturation';
thisDir = fileparts(mfilename('fullpath'));
if ~bdIsLoaded(model), load_system(fullfile(thisDir, [model '.slx'])); end
for nm = {'Series RLC Branch', 'Series RLC Branch1', 'Series RLC Branch2'}
    blk = findBlock(model, nm{1});
    assert(strcmp(get_param(blk, 'BranchType'), 'R'), '%s is not a resistor branch', blk);
    old = get_param(blk, 'Resistance');
    set_param(blk, 'Resistance', sprintf('%.6g', newR));
    assert(abs(str2double(get_param(blk, 'Resistance')) - newR) < 1e-12, 'read-back failed for %s', blk);
    fprintf('%-20s Resistance %s -> %s ohm\n', nm{1}, old, get_param(blk, 'Resistance'));
end
if saveChanges, save_system(model); fprintf('Saved %s.\n', model); else, fprintf('Applied to the loaded model only (not saved).\n'); end
end

function blk = findBlock(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times', name, numel(hit)); blk = hit{1};
end
