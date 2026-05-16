mdl = 'TransformerWithCTSaturation';
relay = [mdl '/Hybrid 87T Relay'];
load_system(mdl);

% Remove old debug taps if they exist
dbgBlocks = {
    'DBG_supervisory_raw_trip'
    'DBG_trip_bool'
    'DBG_trip_latch'
    'DBG_trip_outport_input'
};

for k = 1:numel(dbgBlocks)
    blk = [relay '/' dbgBlocks{k}];
    if ~isempty(find_system(relay, 'SearchDepth', 1, 'Name', dbgBlocks{k}))
        delete_block(blk);
    end
end

% Find S-R latch block safely because its name contains a newline
sr = find_system(relay, 'SearchDepth', 1, 'Regexp', 'on', 'Name', '^S-R\s*Latch$');
sr = sr{1};

% Add taps
addDebugTap(relay, [relay '/Supervisory Override with Hardware Fallback'], 1, ...
    'DBG_supervisory_raw_trip', [1220 190 1370 220]);

addDebugTap(relay, [relay '/Data Type Conversion'], 1, ...
    'DBG_trip_bool', [1320 210 1470 240]);

% Important: S-R latch trip output is port 2
addDebugTap(relay, sr, 2, ...
    'DBG_trip_latch', [1440 230 1590 260]);

% Top-level subsystem output signal is same as Trip_Signal input
addDebugTap(relay, sr, 2, ...
    'DBG_trip_outport_input', [1440 270 1590 300]);

save_system(mdl);

function addDebugTap(parent, srcBlk, srcPort, varName, pos)
    tap = [parent '/' varName];

    add_block('simulink/Sinks/To Workspace', tap, ...
        'Position', pos, ...
        'VariableName', varName, ...
        'SaveFormat', 'Array', ...
        'MaxDataPoints', 'inf');

    srcPH = get_param(srcBlk, 'PortHandles');
    tapPH = get_param(tap, 'PortHandles');

    add_line(parent, srcPH.Outport(srcPort), tapPH.Inport(1), 'autorouting', 'on');
end
