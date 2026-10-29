@echo off
cd /d "%~dp0"
call "%~dp0run_stress_plant_b_v5_generate.bat" 1200 main
call "%~dp0run_stress_plant_b_v5_generate.bat" 150 OOD
echo [%date% %time%] B_DONE >> datasets\v5_generation_master_log.txt
