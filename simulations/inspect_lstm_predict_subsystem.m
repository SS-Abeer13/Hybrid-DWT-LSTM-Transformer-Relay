% inspect_lstm_predict_subsystem.m
% Inspect the internal blocks and MATLAB Function block code inside LSTM Predict

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    subsystem = [model '/Hybrid 87T Relay/LSTM Predict'];
    fprintf('Subsystem: %s\n', subsystem);
    
    % Find blocks inside the subsystem (including under masks)
    blocks = find_system(subsystem, 'LookUnderMasks', 'all', 'FollowLinks', 'on');
    fprintf('\nBlocks inside LSTM Predict (under masks):\n');
    for i = 1:numel(blocks)
        fprintf('  %s (Type: %s)\n', blocks{i}, get_param(blocks{i}, 'BlockType'));
    end
    
    % Find MATLAB Function block
    mlfbs = find_system(subsystem, 'LookUnderMasks', 'all', 'FollowLinks', 'on', 'BlockType', 'SubSystem', 'SFBlockType', 'MATLAB Function');
    if ~isempty(mlfbs)
        mlfb = mlfbs{1};
        fprintf('\nFound MATLAB Function block: %s\n', mlfb);
        
        % Read the script of the MATLAB Function block
        rt = sfroot;
        chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', mlfb);
        if ~isempty(chart)
            fprintf('\nMATLAB Function Script:\n');
            disp(chart.Script);
        else
            fprintf('Could not get Stateflow Chart for MATLAB Function block.\n');
        end
    else
        fprintf('\nNo MATLAB Function block found inside LSTM Predict.\n');
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
