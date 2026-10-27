@echo off
REM Run top-ups for v4 dataset to achieve 100% PASS across all coverage criteria.
REM Single MATLAB instance at a time.
cd /d "%~dp0"
set LOG=datasets\stress_v4_topups_log.txt
echo [%date% %time%] === STARTING V4 TOP-UPS === > "%LOG%"
echo [%date% %time%] === STARTING V4 TOP-UPS ===

echo [%date% %time%] Top-up 1/3: Inrush_Loaded (80 traces)... >> "%LOG%"
echo [%date% %time%] Top-up 1/3: Inrush_Loaded (80 traces)...
matlab -batch "cd('simulations'); generate_stress_dataset_v4(80, 'Set', 'main', 'Only', 'Inrush_Loaded');" >> "%LOG%" 2>&1
if errorlevel 1 (echo ERROR in Inrush_Loaded topup & exit /b 1)

echo [%date% %time%] Top-up 2/3: Overexcitation (40 traces, OverexcMin 1.22)... >> "%LOG%"
echo [%date% %time%] Top-up 2/3: Overexcitation (40 traces, OverexcMin 1.22)...
matlab -batch "cd('simulations'); generate_stress_dataset_v4(40, 'Set', 'main', 'Only', 'Overexcitation', 'OverexcMin', 1.22);" >> "%LOG%" 2>&1
if errorlevel 1 (echo ERROR in Overexcitation topup & exit /b 1)

echo [%date% %time%] Top-up 3/3: InternalHV_CG (15 traces)... >> "%LOG%"
echo [%date% %time%] Top-up 3/3: InternalHV_CG (15 traces)...
matlab -batch "cd('simulations'); generate_stress_dataset_v4(15, 'Set', 'main', 'Only', 'InternalHV_CG');" >> "%LOG%" 2>&1
if errorlevel 1 (echo ERROR in InternalHV_CG topup & exit /b 1)

echo [%date% %time%] === ALL TOP-UPS COMPLETED SUCCESSFULLY === >> "%LOG%"
echo [%date% %time%] === ALL TOP-UPS COMPLETED SUCCESSFULLY ===
