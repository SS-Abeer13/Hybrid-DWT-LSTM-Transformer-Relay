#!/bin/bash
# Background equivalent of run_stress_v3_generate.bat: main set (3040), then OOD set (300). Same run-id files, so either can resume the other.
cd "/f/Transformer Thesis"
MATLAB="/c/Program Files/MATLAB/R2023a/bin/matlab.exe"
gen() {   # $1 = N, $2 = set (main|OOD)
  local N=$1 SET=$2 TAG=$2 FT=""
  [ "$SET" = "OOD" ] && FT="OOD"
  local IDFILE="datasets/stress_v3_${TAG}_runid.txt" LOG="datasets/stress_v3_${TAG}_generate_log.txt"
  [ -f "$IDFILE" ] || date +%Y%m%d_%H%M%S > "$IDFILE"
  local RUN; RUN=$(tr -d '\r\n' < "$IDFILE")
  local FINAL="datasets/StressDataset_v3${FT}_${RUN}.mat" TRIES=0
  echo "[$(date)] $SET run $RUN, N=$N" >> "$LOG"
  while [ ! -f "$FINAL" ] && [ $TRIES -lt 200 ]; do
    TRIES=$((TRIES+1)); echo "[$(date)] launch $TRIES" >> "$LOG"
    "$MATLAB" -batch "cd('F:\Transformer Thesis\simulations'); generate_stress_dataset_v3($N,'Run','$RUN','Chunk',100,'Set','$SET')" >> "$LOG" 2>&1
  done
  echo "[$(date)] $SET finished: $([ -f "$FINAL" ] && echo "$FINAL" || echo MISSING)" >> "$LOG"
}
gen 3040 main
gen 300 OOD
echo ALL_DONE > datasets/stress_v3_generation_done.txt
