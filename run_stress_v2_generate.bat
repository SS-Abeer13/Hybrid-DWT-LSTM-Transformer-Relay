@echo off
REM Full v2 stress dataset (default 1200 samples) -> ONE file datasets\StressDataset_v2_<run>.mat
REM Progress (one line per sample, with ETA) goes to datasets\stress_v2_generate_log.txt
REM If interrupted: generate_stress_dataset_v2(1200, 'Resume', '<run id printed at the start>')
cd /d "%~dp0"
set N=1200
if not "%~1"=="" set N=%~1
echo Generating %N% samples. Follow progress in datasets\stress_v2_generate_log.txt
matlab -batch "cd('%~dp0simulations'); generate_stress_dataset_v2(%N%)" > "datasets\stress_v2_generate_log.txt" 2>&1
echo Done. Last lines of the log:
powershell -NoProfile -Command "Get-Content 'datasets\stress_v2_generate_log.txt' -Tail 8"
echo.
echo Press any key to close this window.
pause >nul
