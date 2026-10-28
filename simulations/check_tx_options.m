% check_tx_options.m
model = 'TransformerWithCTSaturation_v4';
load_system(model);
tx = [model '/Step_down_Transformer'];
p = get_param(tx, 'ObjectParameters');
if isfield(p, 'Winding1Connection')
    disp('Winding1Connection Type:');
    disp(p.Winding1Connection);
end
if isfield(p, 'Winding2Connection')
    disp('Winding2Connection Type:');
    disp(p.Winding2Connection);
end
close_system(model, 0);
exit(0);
