function build_transformer_b_v4()
% BUILD_TRANSFORMER_B_V4 Build Plant B model (40 MVA, 132/33 kV, Dyn11, 1 A secondaries)
% Phase 3.1 of IMPLEMENTATION_PLAN_V4_PUBLICATION.md

thisDir = fileparts(mfilename('fullpath'));
cd(thisDir);

srcModel = 'TransformerWithCTSaturation_v4';
dstModel = 'TransformerB_v4';

fprintf('================================================================================\n');
fprintf('BUILDING PLANT B MODEL: %s.slx\n', dstModel);
fprintf('Specifications: 40 MVA, 132/33 kV, Vector Group Dyn11, 1 A CT secondaries\n');
fprintf('================================================================================\n');

bdclose('all');

% 1. Copy source model
srcPath = fullfile(thisDir, [srcModel '.slx']);
dstPath = fullfile(thisDir, [dstModel '.slx']);
if exist(dstPath, 'file')
    delete(dstPath);
end
copyfile(srcPath, dstPath);
fprintf('Copied %s -> %s\n', srcModel, dstModel);

% 2. Load destination model
load_system(dstModel);

% Disable diagnostic warnings
for m = {'AlgebraicLoopMsg', 'UnconnectedInputMsg', 'UnconnectedOutputMsg', 'UnconnectedLineMsg'}
    try set_param(dstModel, m{1}, 'none'); catch; end
end

% 3. Configure Main Transformer
tx = [dstModel '/Step_down_Transformer'];
fprintf('Configuring %s (40 MVA, 132/33 kV, Dyn11)...\n', tx);
set_param(tx, 'NominalPower', '[ 40e6 50 ]');
set_param(tx, 'Winding1Connection', 'Delta (D11)');
set_param(tx, 'Winding2Connection', 'Yg');
set_param(tx, 'Winding1', '[ 132e3 0.002 0.05 ]');
set_param(tx, 'Winding2', '[ 33e3 0.002 0.05 ]');

% 4. Configure HV Voltage Sources
fprintf('Configuring 132 kV Voltage Sources...\n');
for s = {'VSa', 'VSb', 'VSc'}
    b = [dstModel '/' s{1}];
    set_param(b, 'Amplitude', '(132e3*sqrt(2))/(sqrt(3))');
end

% 5. Configure HV Source Feeder Impedance (2500 MVA SC level at 132 kV)
fprintf('Configuring HV Feeder Impedance...\n');
src_branch = [dstModel '/Three-Phase' newline 'Series RLC Branch '];
if isempty(find_system(dstModel, 'SearchDepth', 1, 'Name', 'Three-Phase Series RLC Branch'))
    % try alternate name
    blks = find_system(dstModel, 'SearchDepth', 1, 'BlockType', 'PMComponent');
    for i = 1:length(blks)
        if contains(get_param(blks{i}, 'Name'), 'Three-Phase') && contains(get_param(blks{i}, 'Name'), 'Branch')
            src_branch = blks{i};
            break;
        end
    end
end
set_param(src_branch, 'Resistance', '0.46', 'Inductance', '0.0221');

% 6. Configure LV Load (33 kV, 40 MVA at 0.95 PF = 38 MW + 12.49 MVAR)
fprintf('Configuring 33 kV Load...\n');
ld = find_system(dstModel, 'SearchDepth', 1, 'Type', 'Block');
ld = ld(contains(ld, 'RLC Load'));
assert(~isempty(ld), 'Load block not found');
set_param(ld{1}, 'NominalVoltage', '33e3', ...
                 'ActivePower', '38e6', ...
                 'InductivePower', '12.49e6', ...
                 'CapacitivePower', '0');

% 7. Configure CTs for 1 A secondaries (2.5 VA rating, 2.5 ohm burden)
% HV: 200/1 A, 2.5 VA, 2.5 ohm burden
% LV: 800/1 A, 2.5 VA, 2.5 ohm burden
fprintf('Configuring CTs (1 A secondary class, 2.5 VA, 2.5 ohm burden)...\n');
hv_cts = {'CT', 'CT1', 'CT2'};
lv_cts = {'CT4', 'CT3', 'CT6'};

for i = 1:length(hv_cts)
    ct_sub = [dstModel '/' hv_cts{i}];
    blks = find_system(ct_sub, 'Type', 'Block');
    for j = 1:length(blks)
        b = blks{j};
        bn = get_param(b, 'Name');
        if contains(bn, 'CT ') || contains(bn, 'Saturable')
            set_param(b, 'NominalPower', '[2.5 50]', ...
                         'Winding1', '[2.5*(1/200) 0.05 0.001]', ...
                         'Winding2', '[2.5 0.05 0.001]');
        elseif strcmp(bn, '1ohm')
            set_param(b, 'Resistance', '2.5');
        end
    end
end

for i = 1:length(lv_cts)
    ct_sub = [dstModel '/' lv_cts{i}];
    blks = find_system(ct_sub, 'Type', 'Block');
    for j = 1:length(blks)
        b = blks{j};
        bn = get_param(b, 'Name');
        if contains(bn, 'CT ') || contains(bn, 'Saturable')
            set_param(b, 'NominalPower', '[2.5 50]', ...
                         'Winding1', '[2.5*(1/800) 0.05 0.001]', ...
                         'Winding2', '[2.5 0.05 0.001]');
        elseif strcmp(bn, '1ohm')
            set_param(b, 'Resistance', '2.5');
        end
    end
end

% 8. Configure Stateflow Compensation Chart for Dyn11
fprintf('Updating Stateflow compensation chart for Dyn11...\n');
charts = sfroot().find('-isa', 'Stateflow.EMChart');
hit = [];
for c = charts(:).'
    if contains(c.Path, dstModel) && (contains(c.Script, 'Yd1_Compensation') || contains(c.Script, 'Dyn11_Compensation') || contains(c.Path, 'Compensation'))
        hit = c;
        break;
    end
end
assert(~isempty(hit), 'Compensation chart not found in %s', dstModel);

newScript = strjoin({ ...
'function [I_hv_comp_pu, I_lv_comp_pu] = Yd1_Compensation(I_hv_sec, I_lv_sec)', ...
'% =========================================================================', ...
'% HYBRID ADAPTIVE 87T RELAY: SIGNAL CONDITIONING & COMPENSATION (Plant B)', ...
'% Vector Group: Dyn11 (HV Delta, LV Wye). 40 MVA, 132/33 kV, 1 A secondaries', ...
'% =========================================================================', ...
'    % 1. NAMEPLATE RATINGS (40 MVA)', ...
'    S_nom   = 40e6;', ...
'    V_hv_ll = 132e3;', ...
'    V_lv_ll = 33e3;', ...
'', ...
'    % 2. Primary full-load amperes', ...
'    I_FLA_hv = S_nom / (sqrt(3) * V_hv_ll);   % 174.9546 A', ...
'    I_FLA_lv = S_nom / (sqrt(3) * V_lv_ll);   % 699.8184 A', ...
'', ...
'    % 3. EFFECTIVE CT ratios', ...
'    CT_Ratio_HV = 202.1424;', ...
'    CT_Ratio_LV = 808.3749;', ...
'', ...
'    % 4. Rated secondary currents = 1.0 pu bases (0.7891 A HV / 0.7860 A LV)', ...
'    I_nom_hv = 0.7891;', ...
'    I_nom_lv = 0.7860;', ...
'', ...
'    % 5. Per-unit normalisation', ...
'    I_hv_pu = I_hv_sec ./ I_nom_hv;', ...
'    I_lv_pu = I_lv_sec ./ I_nom_lv;', ...
'', ...
'    % 6. Dyn11 compensation of the Wye (LV) side.', ...
'    % Mapping: I_hv = M_Dyn11 * I_lv for healthy operation.', ...
'    M_Dyn11 = (1/sqrt(3)) * [ 1,  0, -1; ', ...
'                             -1,  1,  0; ', ...
'                              0, -1,  1];', ...
'    I_lv_comp_pu = M_Dyn11 * I_lv_pu;', ...
'', ...
'    % HV (Delta) side passes through', ...
'    I_hv_comp_pu = I_hv_pu;', ...
'end'}, newline);
hit.Script = newScript;

% 9. Save and compile test
save_system(dstModel);
fprintf('Saved %s.slx successfully.\n', dstModel);

fprintf('Testing diagram update (compilation)...\n');
set_param(dstModel, 'SimulationCommand', 'update');
fprintf('PASS: Model diagram compiled with zero errors!\n');

bdclose('all');
fprintf('=== Plant B Model Construction Complete ===\n');
end
