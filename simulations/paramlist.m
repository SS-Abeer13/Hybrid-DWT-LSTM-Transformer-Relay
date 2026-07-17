modelName = 'TransformerWithCTSaturation'; % Ensure model is open
load_system(modelName);

% Find all blocks in the model
allBlocks = find_system(modelName, 'Type', 'block');

for i = 1:length(allBlocks)
    blk = allBlocks{i};
    fprintf('\n--- Block: %s ---\n', blk);
    
    % Get all parameters that appear in the block's dialog box
    params = get_param(blk, 'DialogParameters');
    
    if ~isempty(params)
        fNames = fieldnames(params);
        for j = 1:length(fNames)
            pName = fNames{j};
            pValue = get_param(blk, pName);
            % Only print if it's a simple string or numeric value
            if ischar(pValue) || isnumeric(pValue)
                fprintf('  %s: %s\n', pName, num2str(pValue));
            end
        end
    else
        fprintf('  [No dialog parameters found]\n');
    end
end