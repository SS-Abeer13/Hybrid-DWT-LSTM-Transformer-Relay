function run_d5_closedloop()
%RUN_D5_CLOSEDLOOP Runs the 50 D5 traces (25 main + 25 OOD) in Simulink with LSTM active.
thisDir = fileparts(mfilename('fullpath'));
cd(thisDir);
projectDir = fileparts(thisDir);
indFile = fullfile(projectDir, 'runs', '20261029_v5_final', 'd4', 'indices.json');
ind = jsondecode(fileread(indFile));

fprintf('=== Running 25 Main Closed-Loop Traces (Tag: d5main) ===\n');
generate_stress_dataset_v5('closedloop', 'Indices', ind.main, 'Tag', 'd5main');

fprintf('\n=== Running 25 OOD Closed-Loop Traces (Tag: d5ood) ===\n');
generate_stress_dataset_v5('closedloop', 'Set', 'OOD', 'Indices', ind.ood, 'Tag', 'd5ood');

fprintf('\nAll 50 D4 closed-loop traces finished successfully.\n');
end
