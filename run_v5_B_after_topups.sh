#!/bin/bash
cd "/f/Transformer Thesis"
while ! grep -q A_TOPUPS_DONE datasets/stress_v5_topups_log.txt 2>/dev/null; do sleep 60; done
cmd //c "F:\Transformer Thesis\run_v5_B_resume.bat"
echo B_CHAIN_END
