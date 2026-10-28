% inspect_blocks_v4.m
model = 'TransformerWithCTSaturation_v4';
load_system(model);
blks = find_system(model, 'SearchDepth', 1, 'Type', 'Block');
for i = 1:length(blks)
    b = blks{i};
    bt = get_param(b, 'BlockType');
    ref = '';
    try ref = get_param(b, 'ReferenceBlock'); catch; end
    fprintf('%s | %s | %s\n', get_param(b, 'Name'), bt, ref);
end
close_system(model, 0);
exit(0);
