#!/bin/bash
cd "/f/Transformer Thesis/simulations"
for t in AB BC AC ABC AG; do
  for a in 1 2 3; do
    "/c/Program Files/MATLAB/R2023a/bin/matlab.exe" -batch "cd('F:\Transformer Thesis\simulations'); hiz_sensitivity_sweep('$t');" > hiz_sweep_${t}_console.txt 2>&1
    [ -f hiz_sweep_$t.mat ] && break
  done
done
echo ALL_DONE > hiz_sweep_done.txt
