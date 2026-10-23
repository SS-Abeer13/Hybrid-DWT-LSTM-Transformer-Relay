#!/bin/bash
cd "/f/Transformer Thesis/simulations"
M="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
run() {  # $1 set  $2 tag  $3 indices
  for a in 1 2 3; do
    "$M" -batch "cd('F:\Transformer Thesis\simulations'); bdclose('all'); generate_stress_dataset_v3('closedloop','Set','$1','Indices',$3,'Tag','$2')" > d4_$2_console.txt 2>&1
    grep -q "Passed [0-9]* /" d4_$2_console.txt && break
  done
}
run main d4main1 "[137 183 198 322 655 728 830 888 1092 1227 1316 1594 1751]"
run main d4main2 "[1783 1872 2056 2113 2137 2188 2232 2354 2421 2463 2869 2989]"
run OOD d4ood1 "[5 23 25 28 29 30 31 32 33 35 58 83 84]"
run OOD d4ood2 "[114 133 139 150 195 197 212 226 228 242 243 294]"
echo D4_DONE > d4_done.txt
