@echo off
REM Generate the v3 stress dataset, unattended, with automatic restarts.
REM   run_stress_v3_generate.bat [N] [main|OOD] [Only-name]
REM   run_stress_v3_generate.bat 3040            main set  -> datasets\StressDataset_v3_<run>.mat
REM   run_stress_v3_generate.bat 300 OOD         OOD set   -> datasets\StressDataset_v3OOD_<run>.mat
REM   run_stress_v3_generate.bat 80 main Stress_ExtCTSat   top-up -> datasets\StressDataset_v3Only_<run>.mat
REM The run id is stored in datasets\stress_v3_<tag>_runid.txt, so starting this file again CONTINUES the same run.
REM MATLAB is restarted every CHUNK simulations (planned, before the 0xc0000374 heap crash) and after any crash
REM (the generator saves a partial file every 25 samples). One MATLAB at a time (about 2.2 GB RAM).
cd /d "%~dp0"
set N=3040
set SETNAME=main
set ONLY=
set CHUNK=100
if not "%~1"=="" set N=%~1
if not "%~2"=="" set SETNAME=%~2
if not "%~3"=="" set ONLY=%~3
set TAG=%SETNAME%
if not "%ONLY%"=="" set TAG=%SETNAME%_%ONLY%
set FILETAG=
if /i "%SETNAME%"=="OOD" set FILETAG=OOD
if not "%ONLY%"=="" set FILETAG=Only
set IDFILE=datasets\stress_v3_%TAG%_runid.txt
set LOG=datasets\stress_v3_%TAG%_generate_log.txt
if not exist "%IDFILE%" (
  for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do echo %%t> "%IDFILE%"
)
set /p RUN=<"%IDFILE%"
set OPTS='Run','%RUN%','Chunk',%CHUNK%,'Set','%SETNAME%'
if not "%ONLY%"=="" set OPTS=%OPTS%,'Only','%ONLY%'
set FINAL=datasets\StressDataset_v3%FILETAG%_%RUN%.mat
echo Run %RUN% (%TAG%), %N% samples, chunk %CHUNK%. Log: %LOG%
set TRIES=0
:again
if exist "%FINAL%" goto :done
set /a TRIES+=1
if %TRIES% gtr 200 goto :giveup
echo [%date% %time%] launch %TRIES% >> "%LOG%"
matlab -batch "cd('%~dp0simulations'); generate_stress_dataset_v3(%N%,%OPTS%)" >> "%LOG%" 2>&1
goto :again
:done
echo FINISHED: %FINAL%
goto :end
:giveup
echo Gave up after 200 launches. See %LOG%
:end
echo.
echo Press any key to close this window.
pause >nul
