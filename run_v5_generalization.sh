#!/bin/bash
cd "/f/Transformer Thesis"
P=/c/Users/Abeer/AppData/Local/Programs/Python/Python311/python
A="datasets/StressDataset_v5_20261028_162333.mat datasets/StressDataset_v5Only_20261028_232627.mat datasets/StressDataset_v5Only_20261028_233305.mat datasets/StressDataset_v5Only_20261028_234041.mat datasets/StressDataset_v5Only_20261029_111722.mat"
B="datasets/StressDataset_PlantBv5_20261028_212041.mat datasets/StressDataset_PlantBv5Only_20261029_111005.mat datasets/StressDataset_PlantBv5Only_20261029_111251.mat"
PYTHONPATH="$PWD/.pylibs" PYTHONUNBUFFERED=1 $P tools/run_plant_b_generalization_v5.py --mode all --plant-a-run runs/20261029_v5_final --plant-a-files $A --plant-b-files $B --out-tag 20261029_v5 > runs/generalization_v5_console.txt 2>&1
echo GEN_DONE >> runs/generalization_v5_console.txt
