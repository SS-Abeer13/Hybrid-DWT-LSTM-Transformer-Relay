#!/bin/bash
# D2: 20 kHz re-simulation of every v5 trace (plant A main + top-ups + OOD, plant B main + top-ups + OOD); one MATLAB at a time, auto-resume.
cd "/f/Transformer Thesis"
M="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
LOG=datasets/hr_resim_log.txt
D="F:/Transformer Thesis/datasets"
run_job () {   # fn  N  runid  filetag  prefix  reference-file  extra-args
  fn=$1; N=$2; run=$3; tag=$4; prefix=$5; ref=$6; extra=$7
  final="datasets/${prefix}${tag}_${run}.mat"
  tries=0
  while [ ! -f "$final" ] && [ $tries -lt 400 ]; do
    tries=$((tries+1))
    echo "[$(date '+%F %T')] $fn $run launch $tries" >> $LOG
    "$M" -batch "cd('simulations'); ${fn}(${N},'Run','${run}','Chunk',100,'Reference','${D}/${ref}'${extra});" >> datasets/hr_resim_matlab.txt 2>&1
  done
  echo "[$(date '+%F %T')] DONE $final" >> $LOG
}
run_job generate_stress_dataset_hr_v5 3040 20261028_162333 "" StressDataset_v5HR StressDataset_v5_20261028_162333.mat ",'Set','main'"
run_job generate_stress_dataset_hr_v5 80  20261028_232627 Only StressDataset_v5HR StressDataset_v5Only_20261028_232627.mat ",'Set','main','Only','Inrush_Loaded'"
run_job generate_stress_dataset_hr_v5 100 20261028_233305 Only StressDataset_v5HR StressDataset_v5Only_20261028_233305.mat ",'Set','main','Only','Overexcitation','OverexcMin',1.22"
run_job generate_stress_dataset_hr_v5 60  20261028_234041 Only StressDataset_v5HR StressDataset_v5Only_20261028_234041.mat ",'Set','main','Only',{'Stress_ExtCTSat_AB','Stress_ExtCTSat_BC','Stress_ExtCTSat_AC','Stress_ExtCTSat_ABC','Stress_ExtCTSat_ABG','Stress_ExtCTSat_BCG','Stress_ExtCTSat_ACG','Stress_ExtCTSat_ABCG'}"
run_job generate_stress_dataset_hr_v5 60  20261029_111722 Only StressDataset_v5HR StressDataset_v5Only_20261029_111722.mat ",'Set','main','Only','Overexcitation','OverexcMin',1.22,'Seed',20261121"
run_job generate_stress_dataset_hr_v5 300 20261028_205712 OOD StressDataset_v5HR StressDataset_v5OOD_20261028_205712.mat ",'Set','OOD'"
run_job generate_stress_dataset_plant_b_hr_v5 1200 20261028_212041 "" StressDataset_PlantBv5HR StressDataset_PlantBv5_20261028_212041.mat ",'Set','main'"
run_job generate_stress_dataset_plant_b_hr_v5 30  20261029_111005 Only StressDataset_PlantBv5HR StressDataset_PlantBv5Only_20261029_111005.mat ",'Set','main','Only','Inrush_Loaded'"
run_job generate_stress_dataset_plant_b_hr_v5 60  20261029_111251 Only StressDataset_PlantBv5HR StressDataset_PlantBv5Only_20261029_111251.mat ",'Set','main','Only','Overexcitation','OverexcMin',1.22"
run_job generate_stress_dataset_plant_b_hr_v5 150 20261029_010052 OOD StressDataset_PlantBv5HR StressDataset_PlantBv5OOD_20261029_010052.mat ",'Set','OOD'"
echo "[$(date '+%F %T')] ALL_HR_DONE" >> $LOG
