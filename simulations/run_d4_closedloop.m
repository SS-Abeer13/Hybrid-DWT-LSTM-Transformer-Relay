function run_d4_closedloop()
%RUN_D4_CLOSEDLOOP Runs the 50 D4 traces (25 main + 25 OOD) in Simulink with LSTM active.
thisDir = fileparts(mfilename('fullpath'));
cd(thisDir);
projectDir = fileparts(thisDir);
indFile = fullfile(projectDir, 'runs', '20261027_v4_final', 'd4', 'indices.json');
ind = jsondecode(fileread(indFile));

fprintf('=== Running 25 Main Closed-Loop Traces (Tag: d4main) ===\n');
generate_stress_dataset_v4('closedloop', 'Indices', ind.main, 'Tag', 'd4main');

fprintf('\n=== Running 25 OOD Closed-Loop Traces (Tag: d4ood) ===\n');
generate_stress_dataset_v4('closedloop', 'Set', 'OOD', 'Indices', ind.ood, 'Tag', 'd4ood');

fprintf('\nAll 50 D4 closed-loop traces finished successfully.\n');
end
