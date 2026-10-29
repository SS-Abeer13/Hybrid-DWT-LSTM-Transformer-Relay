#!/bin/bash
cd "/f/Transformer Thesis"
while ! grep -q B_OOD_DONE datasets/v5_generation_master_log.txt 2>/dev/null; do sleep 60; done
L=datasets/stress_v5_topups_log.txt
M="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
echo "$(date) B top-up Inrush_Loaded 30" >> $L
"$M" -batch "cd('simulations'); generate_stress_dataset_plant_b_v5(30, 'Set', 'main', 'Only', 'Inrush_Loaded');" >> $L 2>&1
echo "$(date) B top-up Overexcitation 60" >> $L
"$M" -batch "cd('simulations'); generate_stress_dataset_plant_b_v5(60, 'Set', 'main', 'Only', 'Overexcitation', 'OverexcMin', 1.22);" >> $L 2>&1
echo "$(date) A top-up Overexcitation 60" >> $L
"$M" -batch "cd('simulations'); generate_stress_dataset_v5(60, 'Set', 'main', 'Only', 'Overexcitation', 'OverexcMin', 1.22, 'Seed', 20261121);" >> $L 2>&1
echo "$(date) ALL_TOPUPS2_DONE" >> $L
