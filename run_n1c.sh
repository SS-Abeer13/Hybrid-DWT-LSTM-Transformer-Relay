#!/bin/bash
cd "/f/Transformer Thesis"
M="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
for f in 60 50; do
  echo "[$(date '+%F %T')] N1c powergui $f Hz start" >> datasets/n1c_log.txt
  "$M" -batch "cd('simulations'); generate_stress_dataset_hr_v5(12,'Run','N1C_F${f}','Only',{'Normal','External_ABC','Inrush_Loaded'},'GuiFreq',${f});" >> datasets/n1c_matlab.txt 2>&1
  echo "[$(date '+%F %T')] N1c powergui $f Hz end" >> datasets/n1c_log.txt
done
