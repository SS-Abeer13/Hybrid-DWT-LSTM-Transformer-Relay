#!/bin/bash
cd "/f/Transformer Thesis"
L=runs/20261101_v5_benchmark_fair
while pgrep -f "run_nn_cv.py afrasiabi 0" > /dev/null; do sleep 20; done
python -I tools/run_nn_cv.py afrasiabi 1 2 >> $L/afrasiabi_cv_log.txt 2>&1
python -I tools/run_nn_cv.py afrasiabi_nocomp >> $L/afrasiabi_nocomp_cv_log.txt 2>&1
python -I tools/run_nn_cv.py key >> $L/key_cv_log.txt 2>&1
