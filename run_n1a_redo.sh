#!/bin/bash
cd "/f/Transformer Thesis"
M="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
D="F:/Transformer Thesis/datasets"
echo "[$(date '+%F %T')] N1a redo plant B OOD trace 57 start" >> datasets/n1a_log.txt
"$M" -batch "cd('simulations'); generate_stress_dataset_plant_b_hr_v5(150,'Run','REDO57','Set','OOD','Reference','${D}/StressDataset_PlantBv5OOD_20261029_010052.mat','Redo',57);" >> datasets/n1a_matlab.txt 2>&1
echo "[$(date '+%F %T')] N1a redo end" >> datasets/n1a_log.txt
