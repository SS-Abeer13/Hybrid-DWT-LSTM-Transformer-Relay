#!/bin/bash
cd "/f/Transformer Thesis"
P=/c/Users/Abeer/AppData/Local/Programs/Python/Python311/python
F="datasets/StressDataset_v5_20261028_162333.mat datasets/StressDataset_v5Only_20261028_232627.mat datasets/StressDataset_v5Only_20261028_233305.mat datasets/StressDataset_v5Only_20261028_234041.mat datasets/StressDataset_v5Only_20261029_111722.mat"
R=runs/20261029_v5_final
mkdir -p $R
PYTHONPATH="$PWD/.pylibs" PYTHONUNBUFFERED=1 $P lstm_models/train_cv_v5.py final --files $F --ood datasets/StressDataset_v5OOD_20261028_205712.mat --run-dir $R > $R/log.txt 2>&1
echo FINAL_DONE >> $R/log.txt
