"""One-off: derive generate_stress_dataset_v3.m from v2 (step A1 of IMPLEMENTATION_PLAN_V3.md). v2 is not modified."""
from pathlib import Path

here = Path(__file__).resolve().parent
s = (here / "generate_stress_dataset_v2.m").read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert old in s, "pattern not found: " + old[:70]
    s = s.replace(old, new, 1)


# --- names / messages
s = s.replace("GenV2:", "GenV3:").replace("generate_stress_dataset_v2", "generate_stress_dataset_v3").replace("GENERATE_STRESS_DATASET_V2", "GENERATE_STRESS_DATASET_V3")
s = s.replace("'v2-2026-10-19'", "'v3-2026-10-21'")

# --- header
rep("""%   generate_stress_dataset_v3('selftest')        % 5 quick cases, prints the checks, saves nothing
%   outFile = generate_stress_dataset_v3(1200)    % full run -> ONE file datasets\\StressDataset_v2_<run>.mat
%   generate_stress_dataset_v3(1200, 'Resume', '20261019_201500')   % continue an interrupted run
""", """%   generate_stress_dataset_v3('selftest')        % quick cases, prints the checks, saves nothing
%   outFile = generate_stress_dataset_v3(3040)    % main set -> ONE file datasets\\StressDataset_v3_<run>.mat
%   generate_stress_dataset_v3(300, 'Set', 'OOD') % out-of-distribution set -> StressDataset_v3OOD_<run>.mat
%   generate_stress_dataset_v3(80, 'Only', 'Stress_ExtCTSat')   % top-up of named scenarios / kinds / zones
%                                                  %   -> StressDataset_v3Only_<run>.mat (own seed range: no duplicates of the main run)
%
% OPTIONS (name, value pairs)
%   'Run'     run id. If datasets\\StressDataset_v3*_<run>_PARTIAL.mat exists the run RESUMES from it (same seed and N required),
%             otherwise it starts fresh under that id. Default: timestamp (fresh run).
%   'Resume'  alias of 'Run' (v2 name).
%   'Chunk'   stop cleanly after this many simulations in THIS MATLAB process (partial file saved) and return ''. The wrapper
%             run_stress_v3_generate.bat restarts MATLAB until the final file exists. MATLAB's heap-corruption crash
%             (0xc0000374) appears after ~50-150 simulations, so a restart BEFORE it avoids losing work. 0 = never (default).
%   'Set'     'main' (default) | 'OOD' (out-of-distribution ranges; default seed 20261022).
%   'Only'    char or cellstr of scenario names, kinds or zones to generate (default: all).
%   'Seed'    base seed (default 20261021; sample k uses rng(seed + k)).
%   'StopTime' simulation length in seconds (default 1.10).
%
% v3 = v2 plus the changes of IMPLEMENTATION_PLAN_V3.md (A1: the options above; A2-A8 add load calibration, CT stress, HiZ bins,
% HV-side faults, over-excitation / recovery inrush, stratified sampling and the extended self-test).
%
% ---- v2 notes (still valid) ----
""")

# --- options
rep("""opts = struct('Resume', '', 'Seed', 20261019, 'StopTime', 1.10);
for k = 1:2:numel(varargin), opts.(varargin{k}) = varargin{k + 1}; end
""", """opts = struct('Resume', '', 'Run', '', 'Seed', 20261021, 'StopTime', 1.10, 'Chunk', 0, 'Set', 'main', 'Only', {{}});
for k = 1:2:numel(varargin)
    assert(isfield(opts, varargin{k}), 'GenV3:Option', 'Unknown option "%s".', varargin{k});
    opts.(varargin{k}) = varargin{k + 1};
end
seedGiven = any(strcmp(varargin(1:2:end), 'Seed'));
if ~isempty(opts.Resume) && isempty(opts.Run), opts.Run = opts.Resume; end
opts.Set = char(opts.Set);
assert(any(strcmp(opts.Set, {'main', 'OOD'})), 'GenV3:Option', 'Set must be main or OOD.');
if ischar(opts.Only) || isstring(opts.Only), opts.Only = cellstr(opts.Only); end
if ~seedGiven
    if strcmp(opts.Set, 'OOD'), opts.Seed = 20261022; end
    if ~isempty(opts.Only), opts.Seed = opts.Seed + 500000 + sum(double([opts.Only{:}])); end   % own seed range: no duplicates of the main run
end
fileTag = ''; if strcmp(opts.Set, 'OOD'), fileTag = 'OOD'; elseif ~isempty(opts.Only), fileTag = 'Only'; end
""")
rep("cfg.stopTime  = opts.StopTime;\n", "cfg.stopTime  = opts.StopTime;\ncfg.set       = opts.Set;\ncfg.only      = strjoin(opts.Only, ',');\n")
rep("nSamplesNum = 1200; else, nSamplesNum = nSamples; end", "nSamplesNum = 3040; else, nSamplesNum = nSamples; end")

# --- plan with Only filter
rep("""weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
""", """if ~isempty(opts.Only)
    keep = ismember({ST.name}, opts.Only) | ismember({ST.kind}, opts.Only) | ismember({ST.zone}, opts.Only);
    assert(any(keep), 'GenV3:Only', 'Only = {%s} matches no scenario name, kind or zone.', strjoin(opts.Only, ', '));
    ST = ST(keep);
end
weights = [ST.weight];
counts = max(1, round(nSamplesNum * weights / sum(weights)));
""")

# --- run id / resume
rep("""if isempty(opts.Resume)
    runId = datestr(now, 'yyyymmdd_HHMMSS'); %#ok<TNOW1,DATST>
    dataset = preallocate(N);
    startAt = 1;
else
    runId = opts.Resume;
    P = load(partialFile(datasetsDir, runId));
""", """if isempty(opts.Run)
    runId = datestr(now, 'yyyymmdd_HHMMSS'); %#ok<TNOW1,DATST>
else
    runId = opts.Run;
end
finalFile = fullfile(datasetsDir, sprintf('StressDataset_v3%s_%s.mat', fileTag, runId));
if isfile(finalFile)
    fprintf('Run %s is already finished: %s\\n', runId, finalFile);
    outFile = finalFile;
    return;
end
if ~isfile(partialFile(datasetsDir, fileTag, runId))
    dataset = preallocate(N);
    startAt = 1;
else
    P = load(partialFile(datasetsDir, fileTag, runId));
""")
rep("fprintf('=== Stress dataset v2 | run %s | %d samples | %d scenarios ===\\n', runId, N, numel(ST));",
    "fprintf('=== Stress dataset v3 | set %s | run %s | %d samples | %d scenarios | start at %d | chunk %d ===\\n', opts.Set, runId, N, numel(ST), startAt, opts.Chunk);")

# --- loop: partial name + planned chunk stop
rep("""        save(partialFile(datasetsDir, runId), 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
    end
end
""", """        save(partialFile(datasetsDir, fileTag, runId), 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
    end
    if opts.Chunk > 0 && done >= opts.Chunk && idx < N      % planned restart before MATLAB's heap-corruption crash
        generationConfig = cfg; scenarioTableOut = ST; %#ok<NASGU>
        save(partialFile(datasetsDir, fileTag, runId), 'dataset', 'generationConfig', 'scenarioTableOut', '-v7.3');
        fprintf('CHUNK_DONE at sample %d of %d (run %s). Restart MATLAB with the same Run id to continue.\\n', idx, N, runId);
        outFile = '';
        return;
    end
end
""")
rep("outFile = fullfile(datasetsDir, sprintf('StressDataset_v2_%s.mat', runId));\nsave(outFile", "outFile = finalFile;\nsave(outFile")
rep("if isfile(partialFile(datasetsDir, runId)), delete(partialFile(datasetsDir, runId)); end",
    "if isfile(partialFile(datasetsDir, fileTag, runId)), delete(partialFile(datasetsDir, fileTag, runId)); end")
rep("""function f = partialFile(dir, runId)
f = fullfile(dir, sprintf('StressDataset_v2_%s_PARTIAL.mat', runId));""", """function f = partialFile(dir, fileTag, runId)
f = fullfile(dir, sprintf('StressDataset_v3%s_%s_PARTIAL.mat', fileTag, runId));""")
rep("SELF-TEST PASSED. Run: generate_stress_dataset_v3(1200)", "SELF-TEST PASSED. Run: run_stress_v3_generate.bat 3040")

(here / "generate_stress_dataset_v3.m").write_text(s, encoding="utf-8")
print(len(s.splitlines()), "lines written")
