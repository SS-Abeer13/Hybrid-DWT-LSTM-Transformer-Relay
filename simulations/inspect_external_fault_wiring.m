load_system('TransformerWithCTSaturation_v4');
ext = 'TransformerWithCTSaturation_v4/External_Fault';
pc = get_param(ext, 'PortConnectivity');
for i = 1:numel(pc)
    fprintf('Port %s (type %s):\n', mat2str(i), pc(i).Type);
    if ~isempty(pc(i).SrcBlock) && pc(i).SrcBlock ~= -1
        fprintf('  SrcBlock: %s\n', get_param(pc(i).SrcBlock, 'Name'));
    end
    if ~isempty(pc(i).DstBlock)
        for d = 1:numel(pc(i).DstBlock)
            if pc(i).DstBlock(d) ~= -1
                fprintf('  DstBlock: %s\n', get_param(pc(i).DstBlock(d), 'Name'));
            end
        end
    end
end
