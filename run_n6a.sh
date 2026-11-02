#!/bin/bash
cd "/f/Transformer Thesis"
O=runs/20261101_v5_benchmark_fair/b1_equal_budget
mkdir -p $O
for s in 20261021 20261022 20261023; do
  python -I lstm_models/benchmark_literature_models.py --output-dir $O/seed_$s --seed $s --cv-dir runs/20261029_v5_cv5_seeds/seed_$s --epochs 25 --patience 5 --cache-file runs/20261029_v5_cv5_seeds/traces_cache.npz >> $O/log_$s.txt 2>&1
done
