#!/bin/bash
cd "/f/Transformer Thesis"
P=/c/Users/Abeer/AppData/Local/Programs/Python/Python311/python
F="datasets/StressDataset_v3_20261021_021053.mat datasets/StressDataset_v3Only_topup_inrush_loaded.mat datasets/StressDataset_v3Only_topup_overexc.mat"
for S in 20261022 20261023; do
  mkdir -p runs/20261021_v3_cv5_seed$S
  PYTHONPATH="$PWD/.pylibs" PYTHONUNBUFFERED=1 $P lstm_models/train_cv_v3.py cv --files $F --run-dir runs/20261021_v3_cv5_seed$S --seed $S --cache runs/20261021_v3data_baseline/traces_cache_main.npz > runs/20261021_v3_cv5_seed$S/log.txt 2>&1
done
echo CV_SEEDS_DONE > runs/cv_seeds_done.txt
