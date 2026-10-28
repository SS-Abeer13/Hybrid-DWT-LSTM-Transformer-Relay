@echo off
REM V8 option (a): regenerate all four v5 datasets, one MATLAB at a time, each with automatic restarts.
cd /d "%~dp0"
echo [%date% %time%] plant A main 3040 >> datasets\v5_generation_master_log.txt
call "%~dp0run_stress_v5_generate.bat" 3040 main
echo [%date% %time%] plant A OOD 300 >> datasets\v5_generation_master_log.txt
call "%~dp0run_stress_v5_generate.bat" 300 OOD
echo [%date% %time%] plant B main 1200 >> datasets\v5_generation_master_log.txt
call "%~dp0run_stress_plant_b_v5_generate.bat" 1200 main
echo [%date% %time%] plant B OOD 150 >> datasets\v5_generation_master_log.txt
call "%~dp0run_stress_plant_b_v5_generate.bat" 150 OOD
echo [%date% %time%] ALL_V5_GENERATION_DONE >> datasets\v5_generation_master_log.txt
