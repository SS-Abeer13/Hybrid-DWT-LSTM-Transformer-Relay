function build_plants_v5()
%BUILD_PLANTS_V5 Create TransformerWithCTSaturation_v5.slx and TransformerB_v5.slx from the v4 models (V8 option (a), 2026-10-28).
%
% WHY: the v4 plants had (A) transformer leakage ~2 % and (B) ~1 % -> true through-faults of 23.9 pu (A) and 37.6 pu (B), and CTs whose saturation knee sits at
% ~1.2 pu of rated voltage, so every solid external fault saturated them heavily and, on plant B, high burden x high load saturated them in steady state
% (the 87T then voted on healthy traces). V8 option (a): realistic impedances and CTs sized so that the maximum SYMMETRICAL through-fault is linear at nominal
% burden; saturation only from DC offset, high burden (or remanence, not modelled).
%
% CHANGES (the only ones; everything else is copied unchanged from v4):
%   plant A: transformer Winding1/2 L 0.01 -> 0.055 pu each (X = 11 %), R 0.0025 -> 0.0027 pu each (0.54 % total, X/R 20), source branch R 0.1 -> 0.12 ohm, L 1 mH -> 11.2 mH (2 % of 300 MVA at 230 kV, X/R 29)
%   plant B: transformer Winding1/2 L 0.005 -> 0.05 pu each (X = 10 %), R 0.002 -> 0.0025 pu each (0.5 % total, X/R 20), source branch unchanged (R 0.46 ohm, L 22.1 mH = 1.6 %)
% X/R ~ 20 (v4: plant A ~4 because the leakage was only 2 %, plant B ~40 in the first v5 trial where R was 0.1 %): the DC offset of a fault decays in about 60 ms,
% long enough to saturate a CT in the first cycles but not to wind the flux up for 100+ ms (probe_flux_demand_v5.m: plant B 124 pu with X/R 40).
%   all 12 CTs of a plant: flux column of the v4 Saturation curve replaced by CT_BASE * CT_SCALE (knee ~9 pu plant A, ~108 pu plant B).
% Safety: the v4 files are never modified; every change is read back; the saved v5 file is reloaded and re-checked; the breaker settings must still be the originals.
thisDir = fileparts(mfilename('fullpath'));
CT_BASE = [0 0; 0.0002 4; 0.0006 11; 0.0015 17; 0.004 19.5; 0.05 21.5; 0.5 24];   % flux column in pu of rated-voltage flux, knee ~18 pu (v4: ~1.2 pu)
% flux scale per plant, from probe_knee_sweep_v5.m (X/R 20): A knee ~9 pu (linear in steady state, saturates in the first cycles with DC offset);
% B knee ~108 pu (1 A CT with 2.5 ohm = rated burden: 8.6 pu through-fault flux plus offset reaches ~90 pu, knee 54 pu still saturated 19 % in steady state)
CT_SCALE = [0.5 6];
plants = struct( ...
    'src', {'TransformerWithCTSaturation_v4', 'TransformerB_v4'}, ...
    'dst', {'TransformerWithCTSaturation_v5', 'TransformerB_v5'}, ...
    'w1',  {'[230e3 0.0027 0.055]', '[132e3 0.0025 0.05]'}, ...
    'w2',  {'[11e3 0.0027 0.055]',  '[33e3 0.0025 0.05]'}, ...
    'srcR', {'0.12', ''}, 'srcL', {'0.0112', ''}, 'sc', {CT_SCALE(1), CT_SCALE(2)});
for k = 1:numel(plants)
    P = plants(k); cur = CT_BASE; cur(:, 2) = cur(:, 2) * P.sc; CT_SAT = mat2str(cur, 6);
    srcFile = fullfile(thisDir, [P.src '.slx']); dstFile = fullfile(thisDir, [P.dst '.slx']);
    assert(isfile(srcFile), 'missing %s', srcFile);
    assert(~isfile(dstFile), '%s already exists: not overwriting', dstFile);
    bdclose('all');
    copyfile(srcFile, dstFile);
    load_system(dstFile);
    m = P.dst;
    xf = fb(m, 'Step_down_Transformer');
    set_param(xf, 'Winding1', P.w1, 'Winding2', P.w2);
    assert(strcmp(strtrim(get_param(xf, 'Winding1')), P.w1) && strcmp(strtrim(get_param(xf, 'Winding2')), P.w2), 'transformer read-back failed');
    if ~isempty(P.srcR)
        sb = fb(m, 'Three-Phase Series RLC Branch');
        set_param(sb, 'Resistance', P.srcR, 'Inductance', P.srcL);
        assert(strcmp(get_param(sb, 'Resistance'), P.srcR) && strcmp(get_param(sb, 'Inductance'), P.srcL), 'source impedance read-back failed');
    end
    for ct = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'}
        cb = fb(m, ct{1});
        kids = find_system(cb, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
        hit = kids(contains(kids, 'CT ') & ~contains(kids, 'ohm'));
        assert(numel(hit) == 1, 'CT transformer not unique in %s', ct{1});
        set_param(hit{1}, 'Saturation', CT_SAT);
        assert(strcmp(strtrim(get_param(hit{1}, 'Saturation')), CT_SAT), 'CT saturation read-back failed in %s', ct{1});
    end
    save_system(m); close_system(m, 0);
    % ---- verify the SAVED file
    load_system(dstFile);
    xf = fb(m, 'Step_down_Transformer');
    assert(strcmp(strtrim(get_param(xf, 'Winding1')), P.w1), 'saved transformer differs');
    assert(strcmp(get_param(fb(m, 'Three-Phase Breaker'), 'SwitchTimes'), '[]'), 'breaker settings changed');
    close_system(m, 0);
    fprintf('%s created and verified (transformer %s / %s, CT flux scale %g)\n', P.dst, P.w1, P.w2, P.sc);
end
end

function blk = fb(parent, name)
c = find_system(parent, 'SearchDepth', 1, 'FollowLinks', 'on', 'LookUnderMasks', 'all', 'Type', 'Block');
nn = @(x) strtrim(regexprep(x, '\s+', ' '));
hit = c(strcmp(cellfun(@(x) nn(get_param(x, 'Name')), c, 'UniformOutput', false), nn(name))); hit = hit(~strcmp(hit, parent));
assert(numel(hit) == 1, 'block %s found %d times under %s', name, numel(hit), parent); blk = hit{1};
end
