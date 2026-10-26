% check_ct_topology_v4.m
% Step 1.1: Complete and accurate inspection of CTs, branch resistors,
% and terminal connections in simulations/TransformerWithCTSaturation_v4.slx.

cd('F:\Transformer Thesis\simulations');
model_name = 'TransformerWithCTSaturation_v4';
bdclose('all');
load_system(model_name);

out_file = fullfile(pwd, 'ct_topology_v4.txt');
fid = fopen(out_file, 'w');

fprintf(fid, '================================================================================\n');
fprintf(fid, 'CT and Series Resistor Topology Inspection (Model: %s)\n', model_name);
fprintf(fid, 'Date: %s\n', datestr(now));
fprintf(fid, '================================================================================\n\n');

% 1. CT blocks
ct_names = {'CT', 'CT1', 'CT2', 'CT3', 'CT4', 'CT6'};
fprintf(fid, '================================================================================\n');
fprintf(fid, '1. CT BLOCKS (CT, CT1, CT2 on HV; CT3, CT4, CT6 on LV)\n');
fprintf(fid, '================================================================================\n\n');

for i = 1:length(ct_names)
    ct_b = [model_name '/' ct_names{i}];
    fprintf(fid, '--------------------------------------------------------------------------------\n');
    fprintf(fid, 'BLOCK: %s\n', ct_b);
    b_type = get_param(ct_b, 'BlockType');
    fprintf(fid, '  BlockType: %s\n', b_type);
    
    % Port connectivity
    pc = get_param(ct_b, 'PortConnectivity');
    fprintf(fid, '  Port Connectivity (%d ports):\n', length(pc));
    for p = 1:length(pc)
        fprintf(fid, '    Port %s (Type: %s):\n', num2str(p), pc(p).Type);
        for d = 1:length(pc(p).DstBlock)
            dst_h = pc(p).DstBlock(d);
            if ishandle(dst_h)
                fprintf(fid, '      -> Dst: %s (Port %d)\n', get_param(dst_h, 'Name'), pc(p).DstPort(d));
            end
        end
        for s = 1:length(pc(p).SrcBlock)
            src_h = pc(p).SrcBlock(s);
            if ishandle(src_h)
                fprintf(fid, '      <- Src: %s (Port %d)\n', get_param(src_h, 'Name'), pc(p).SrcPort(s));
            end
        end
    end
    
    % Subsystem internal contents
    if strcmp(b_type, 'SubSystem')
        sub_blocks = find_system(ct_b, 'LookUnderMasks', 'all');
        fprintf(fid, '  Internal Subsystem Contents (%d elements):\n', length(sub_blocks));
        for sb = 1:length(sub_blocks)
            sb_path = sub_blocks{sb};
            if strcmp(sb_path, ct_b); continue; end
            sb_name = get_param(sb_path, 'Name');
            sb_type = get_param(sb_path, 'BlockType');
            fprintf(fid, '    - %s (%s)\n', sb_name, sb_type);
            if contains(sb_name, 'Saturable') || contains(sb_type, 'Saturable')
                try
                    fprintf(fid, '        NominalParameters: %s\n', get_param(sb_path, 'NominalParameters'));
                    fprintf(fid, '        Winding1: %s\n', get_param(sb_path, 'Winding1'));
                    fprintf(fid, '        Winding2: %s\n', get_param(sb_path, 'Winding2'));
                    fprintf(fid, '        Saturation: %s\n', get_param(sb_path, 'Saturation'));
                catch me
                    fprintf(fid, '        Could not read params: %s\n', me.message);
                end
            end
            if contains(sb_name, '1ohm') || contains(sb_name, 'Burden') || contains(sb_name, 'burden')
                try
                    fprintf(fid, '        Resistance: %s\n', get_param(sb_path, 'Resistance'));
                catch
                end
            end
        end
    end
    fprintf(fid, '\n');
end

% 2. All Series RLC Branch blocks
fprintf(fid, '================================================================================\n');
fprintf(fid, '2. ALL SERIES RLC BRANCH BLOCKS IN MODEL\n');
fprintf(fid, '================================================================================\n\n');

rlc_blocks = find_system(model_name, 'SearchDepth', 1, 'BlockType', 'PMComponent');
for b = 1:length(rlc_blocks)
    b_path = rlc_blocks{b};
    b_name = get_param(b_path, 'Name');
    if ~contains(b_name, 'Series RLC') && ~contains(b_name, 'Branch')
        continue;
    end
    fprintf(fid, 'BLOCK: %s\n', b_name);
    try
        fprintf(fid, '  BranchType: %s, R: %s, L: %s, C: %s\n', ...
            get_param(b_path, 'BranchType'), ...
            get_param(b_path, 'Resistance'), ...
            get_param(b_path, 'Inductance'), ...
            get_param(b_path, 'Capacitance'));
    catch
    end
    pc = get_param(b_path, 'PortConnectivity');
    for p = 1:length(pc)
        fprintf(fid, '    Port %s (%s):\n', num2str(p), pc(p).Type);
        for d = 1:length(pc(p).DstBlock)
            dst_h = pc(p).DstBlock(d);
            if ishandle(dst_h)
                fprintf(fid, '      -> Dst: %s (Port %d)\n', get_param(dst_h, 'Name'), pc(p).DstPort(d));
            end
        end
        for s = 1:length(pc(p).SrcBlock)
            src_h = pc(p).SrcBlock(s);
            if ishandle(src_h)
                fprintf(fid, '      <- Src: %s (Port %d)\n', get_param(src_h, 'Name'), pc(p).SrcPort(s));
            end
        end
    end
    fprintf(fid, '\n');
end

% 3. Three-phase transformer and terminal measurements
fprintf(fid, '================================================================================\n');
fprintf(fid, '3. THREE-PHASE TRANSFORMER & TERMINAL BUSES\n');
fprintf(fid, '================================================================================\n\n');

key_blocks = {'Step_down_Transformer', 'Primary_side', 'Secondary_side', 'Three-Phase Fault', 'Three-Phase\nFault'};
for k = 1:length(key_blocks)
    k_name = key_blocks{k};
    matches = find_system(model_name, 'SearchDepth', 1, 'Name', k_name);
    if isempty(matches)
        continue;
    end
    k_path = matches{1};
    fprintf(fid, 'BLOCK: %s\n', get_param(k_path, 'Name'));
    pc = get_param(k_path, 'PortConnectivity');
    for p = 1:length(pc)
        fprintf(fid, '    Port %s (%s):\n', num2str(p), pc(p).Type);
        for d = 1:length(pc(p).DstBlock)
            dst_h = pc(p).DstBlock(d);
            if ishandle(dst_h)
                fprintf(fid, '      -> Dst: %s (Port %d)\n', get_param(dst_h, 'Name'), pc(p).DstPort(d));
            end
        end
        for s = 1:length(pc(p).SrcBlock)
            src_h = pc(p).SrcBlock(s);
            if ishandle(src_h)
                fprintf(fid, '      <- Src: %s (Port %d)\n', get_param(src_h, 'Name'), pc(p).SrcPort(s));
            end
        end
    end
    fprintf(fid, '\n');
end

fclose(fid);
bdclose('all');
fprintf('Topology inspection complete. Output written to %s\n', out_file);
