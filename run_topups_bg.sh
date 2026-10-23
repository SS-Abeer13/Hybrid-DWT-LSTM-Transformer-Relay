#!/bin/bash
cd "/f/Transformer Thesis"
MATLAB="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
top() {  # $1 N, $2 only-name, $3 run id, $4 extra options
  local FINAL="datasets/StressDataset_v3Only_$3.mat" TRIES=0
  while [ ! -f "$FINAL" ] && [ $TRIES -lt 30 ]; do
    TRIES=$((TRIES+1))
    "$MATLAB" -batch "cd('F:\Transformer Thesis\simulations'); generate_stress_dataset_v3($1,'Only','$2','Run','$3','Chunk',100$4)" >> "datasets/stress_v3_topup_log.txt" 2>&1
  done
}
top 120 Inrush_Loaded topup_inrush_loaded ""
top 60 Overexcitation topup_overexc ",'OverexcMin',1.22"
echo TOPUPS_DONE > datasets/stress_v3_topups_done.txt
