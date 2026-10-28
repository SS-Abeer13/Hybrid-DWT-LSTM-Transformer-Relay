% debug_ip.m
model = 'TransformerB_v4';
load_system(model);
out = sim(model, 'StopTime', '0.1', 'ReturnWorkspaceOutputs', 'on');
p = out.get('I_primary_abc');
disp('Class of I_primary_abc:');
disp(class(p));
if isa(p, 'timeseries')
    disp('Data size:');
    disp(size(p.Data));
    disp('First 3 data rows:');
    disp(p.Data(1:3, :));
else
    disp('Value:');
    disp(p);
end
close_system(model, 0);
exit(0);
