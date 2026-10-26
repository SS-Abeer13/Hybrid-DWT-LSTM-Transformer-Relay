model = 'TransformerWithCTSaturation_v4';
if ~bdIsLoaded(model)
    load_system(model);
end
relay = [model '/Hybrid 87T Relay'];

blocks = {'Yd1_plant_map', 'I_diff_LSTM', 'Reshape 1', 'ZOH_1600', 'Feature Window', 'DWT Feature Extraction'};
for i = 1:numel(blocks)
    b = [relay '/' blocks{i}];
    if getSimulinkBlockHandle(b) ~= -1
        fprintf('Block: %s\n', blocks{i});
        pc = get_param(b, 'PortConnectivity');
        for p = 1:numel(pc)
            srcName = '';
            dstName = '';
            if ~isempty(pc(p).SrcBlock) && pc(p).SrcBlock ~= -1
                srcName = get_param(pc(p).SrcBlock, 'Name');
            end
            if ~isempty(pc(p).DstBlock) && any(pc(p).DstBlock ~= -1)
                for d = 1:numel(pc(p).DstBlock)
                    if pc(p).DstBlock(d) ~= -1
                        dstName = [dstName, ' ', get_param(pc(p).DstBlock(d), 'Name')];
                    end
                end
            end
            fprintf('  Port %s: Src=%s (port %s), Dst=%s\n', ...
                pc(p).Type, srcName, mat2str(pc(p).SrcPort), dstName);
        end
    else
        fprintf('Block %s NOT found\n', blocks{i});
    end
end
