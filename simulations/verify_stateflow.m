% verify_stateflow.m
% Test programmatically accessing the Stateflow MATLAB Function block script

try
    model = 'TransformerWithCTSaturation';
    if ~bdIsLoaded(model)
        load_system(model);
    end
    
    rt = sfroot;
    chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', [model '/Hybrid 87T Relay/DWT Feature Extraction']);
    if isempty(chart)
        disp('Chart not found.');
    else
        disp('Chart found successfully!');
        disp('Current script contents:');
        disp(chart.Script);
    end
    
catch ME
    disp(['Error: ' ME.message]);
end
