@echo off
REM Generate the Plant B stress dataset, unattended, with automatic restarts.
REM   run_stress_plant_b_generate.bat [N] [main|OOD] [Only-name]
REM   run_stress_plant_b_generate.bat 1200            main set  -> datasets\StressDataset_PlantB_<run>.mat
REM   run_stress_plant_b_generate.bat 150 OOD         OOD set   -> datasets\StressDataset_PlantBOOD_<run>.mat
REM   run_stress_plant_b_generate.bat 50 main Stress_ExtCTSat   top-up -> datasets\StressDataset_PlantBOnly_<run>.mat
cd /d "%~dp0"
set N=1200
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
set IDFILE=datasets\stress_plant_b_%TAG%_runid.txt
set LOG=datasets\stress_plant_b_%TAG%_generate_log.txt
if not exist "%IDFILE%" (
  for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do echo %%t> "%IDFILE%"
)
set /p RUN=<"%IDFILE%"
set OPTS='Run','%RUN%','Chunk',%CHUNK%,'Set','%SETNAME%'
if not "%ONLY%"=="" set OPTS=%OPTS%,'Only','%ONLY%'
set FINAL=datasets\StressDataset_PlantB%FILETAG%_%RUN%.mat
echo Run %RUN% (%TAG%), %N% samples, chunk %CHUNK%. Log: %LOG%
set TRIES=0
:again
if exist "%FINAL%" goto :done
set /a TRIES+=1
if %TRIES% gtr 200 goto :giveup
echo [%date% %time%] launch %TRIES% >> "%LOG%"
matlab -batch "cd('%~dp0simulations'); generate_stress_dataset_plant_b(%N%,%OPTS%); exit;" >> "%LOG%" 2>&1
goto :again
:done
echo FINISHED: %FINAL%
goto :end
:giveup
echo Gave up after 200 launches. See %LOG%
:end
