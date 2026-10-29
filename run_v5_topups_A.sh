#!/bin/bash
# plant A v5 top-ups (own seed ranges), after the main generation chain has finished; one MATLAB at a time
cd "/f/Transformer Thesis"
while ! grep -q ALL_V5_GENERATION_DONE datasets/v5_generation_master_log.txt; do sleep 60; done
L=datasets/stress_v5_topups_log.txt
M="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
echo "$(date) top-up Inrush_Loaded 80" >> $L
"$M" -batch "cd('simulations'); generate_stress_dataset_v5(80, 'Set', 'main', 'Only', 'Inrush_Loaded');" >> $L 2>&1
echo "$(date) top-up Overexcitation 100 (OverexcMin 1.22)" >> $L
"$M" -batch "cd('simulations'); generate_stress_dataset_v5(100, 'Set', 'main', 'Only', 'Overexcitation', 'OverexcMin', 1.22);" >> $L 2>&1
echo "$(date) top-up Stress_ExtCTSat multi-phase 60" >> $L
"$M" -batch "cd('simulations'); generate_stress_dataset_v5(60, 'Set', 'main', 'Only', {'Stress_ExtCTSat_AB','Stress_ExtCTSat_BC','Stress_ExtCTSat_AC','Stress_ExtCTSat_ABC','Stress_ExtCTSat_ABG','Stress_ExtCTSat_BCG','Stress_ExtCTSat_ACG','Stress_ExtCTSat_ABCG'});" >> $L 2>&1
echo "$(date) A_TOPUPS_DONE" >> $L
