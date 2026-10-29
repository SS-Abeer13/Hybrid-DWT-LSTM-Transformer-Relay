#!/bin/bash
# resume after the 21:45 interruption: plant B main (resumes from PARTIAL), plant B OOD, then plant A top-ups
cd "/f/Transformer Thesis"
cmd //c "F:\Transformer Thesis\run_stress_plant_b_v5_generate.bat 1200 main"
cmd //c "F:\Transformer Thesis\run_stress_plant_b_v5_generate.bat 150 OOD"
echo "[$(date)] ALL_V5_GENERATION_DONE (resumed chain)" >> datasets/v5_generation_master_log.txt
bash run_v5_topups_A.sh
