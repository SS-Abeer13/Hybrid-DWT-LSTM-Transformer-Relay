% rewire_cts_series_v4.m
% Phase 1.2: Re-wire CTs in series so that 100% of line current flows through each CT primary.
%
% Methodology:
% 1. Start from pristine TransformerWithCTSaturation.slx copied to TransformerWithCTSaturation_v4.slx.
% 2. Delete the 6 parallel bypass resistors:
%      HV: Series RLC Branch3, Series RLC Branch4, Series RLC Branch5
%      LV: Series RLC Branch, Series RLC Branch1, Series RLC Branch2
% 3. Set the remaining series resistors in the CT branches:
%      HV: Series RLC Branch6, Series RLC Branch7, Series RLC Branch8
%      LV: Series RLC Branch11, Series RLC Branch10, Series RLC Branch9
%    to R = 1e-3 ohm (1 mOhm, negligible series impedance).
% 4. Save and run compile/simulation sanity check.

cd('F:\Transformer Thesis\simulations');
model_name = 'TransformerWithCTSaturation_v4';
bdclose('all');

% Restore from pristine thesis model
copyfile('TransformerWithCTSaturation.slx', 'TransformerWithCTSaturation_v4.slx');
load_system(model_name);

fprintf('=== Phase 1.2: Re-wiring CTs in series in %s ===\n', model_name);

% 1. Delete lines of the 6 parallel bypass resistors
bypass_blocks = {
    'Series RLC Branch3', 'Series RLC Branch4', 'Series RLC Branch5', ... % HV Phase A, B, C bypass
    'Series RLC Branch',  'Series RLC Branch1', 'Series RLC Branch2'   ... % LV Phase A, B, C bypass
};

for i = 1:length(bypass_blocks)
    b_name = bypass_blocks{i};
    b_path = [model_name '/' b_name];
    if ~isempty(find_system(model_name, 'SearchDepth', 1, 'Name', b_name))
        lh = get_param(b_path, 'LineHandles');
        all_lines = [lh.LConn, lh.RConn];
        for l = all_lines
            if l ~= -1 && ishandle(l)
                try delete_line(l); catch; end
            end
        end
        delete_block(b_path);
        fprintf('Deleted bypass resistor: %s\n', b_name);
    else
        fprintf('Bypass block not found: %s\n', b_name);
    end
end

% 2. Set series branch resistors in the CT path to 1 mOhm (1e-3 ohm)
series_ct_blocks = {
    'Series RLC Branch6', 'Series RLC Branch7', 'Series RLC Branch8', ... % HV Phase A, B, C CT series
    'Series RLC Branch11', 'Series RLC Branch10', 'Series RLC Branch9'  ... % LV Phase A, B, C CT series
};

for i = 1:length(series_ct_blocks)
    b_name = series_ct_blocks{i};
    b_path = [model_name '/' b_name];
    if ~isempty(find_system(model_name, 'SearchDepth', 1, 'Name', b_name))
        set_param(b_path, 'Resistance', '0.001');
        fprintf('Set %s resistance to 0.001 ohm (1 mOhm).\n', b_name);
    else
        warning('Series block not found: %s\n', b_name);
    end
end

% 3. Save model
save_system(model_name);
fprintf('Saved %s.slx successfully.\n', model_name);

% 4. Test compilation (diagram update)
fprintf('Updating diagram (compile test)...\n');
set_param(model_name, 'SimulationCommand', 'update');
fprintf('PASS: Model diagram compiled with zero errors!\n');

% 5. Test brief simulation run (50 ms)
fprintf('Testing brief 50 ms simulation run...\n');
sim_out = sim(model_name, 'StopTime', '0.05');
fprintf('PASS: 50 ms simulation ran successfully!\n');

bdclose('all');
fprintf('=== Phase 1.2 Complete ===\n');
