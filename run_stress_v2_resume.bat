@echo off
REM Auto-resume wrapper: MATLAB crashed (heap corruption) at sample 55, so restart it
REM again and again from the last saved partial file until the final file exists.
REM Usage: run_stress_v2_resume.bat [run id]     (default = run started 20261020_005715)
cd /d "%~dp0"
set RUN=20261020_005715
if not "%~1"=="" set RUN=%~1
set N=1200
set TRIES=0
:again
if exist "datasets\StressDataset_v2_%RUN%.mat" goto :done
set /a TRIES+=1
if %TRIES% gtr 80 goto :giveup
echo [%date% %time%] attempt %TRIES%: resuming run %RUN%
matlab -batch "cd('%~dp0simulations'); generate_stress_dataset_v2(%N%,'Resume','%RUN%')" >> "datasets\stress_v2_generate_log.txt" 2>&1
goto :again
:done
echo FINISHED: datasets\StressDataset_v2_%RUN%.mat
goto :end
:giveup
echo Gave up after 80 attempts. See datasets\stress_v2_generate_log.txt
:end
echo.
echo Press any key to close this window.
pause >nul
