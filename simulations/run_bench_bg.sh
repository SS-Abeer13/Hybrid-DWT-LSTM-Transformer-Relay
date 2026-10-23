#!/bin/bash
cd "/f/Transformer Thesis/simulations"
for a in 1 2 3; do
  "/c/Program Files/MATLAB/R2023a/bin/matlab.exe" -batch "cd('F:\Transformer Thesis\simulations'); bdclose('all'); clear lstm_predict_wrapper; test_hybrid_relay" > benchmark_hvfault_console.txt 2>&1
  grep -q "Heap corruption" benchmark_hvfault_console.txt || break
done
echo BENCH_DONE > benchmark_hvfault_done.txt
