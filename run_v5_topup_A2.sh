#!/bin/bash
cd "/f/Transformer Thesis"
while ! grep -q B_DONE datasets/v5_generation_master_log.txt 2>/dev/null; do sleep 60; done
"/c/Program Files/MATLAB/R2023a/bin/matlab.exe" -batch "cd('simulations'); generate_stress_dataset_v5(60, 'Set', 'main', 'Only', 'Overexcitation', 'OverexcMin', 1.22, 'Seed', 20261121);" >> datasets/stress_v5_topups_log.txt 2>&1
echo "$(date) A_TOPUP2_DONE" >> datasets/stress_v5_topups_log.txt
