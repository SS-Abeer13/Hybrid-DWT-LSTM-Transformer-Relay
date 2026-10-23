@echo off
REM Quick self-test of the v2 stress generator: 5 cases, checks printed, NOTHING saved, .slx untouched.
cd /d "%~dp0"
echo Running generator self-test (a few minutes)...
matlab -batch "cd('%~dp0simulations'); generate_stress_dataset_v2('selftest')" > "simulations\stress_v2_selftest.txt" 2>&1
type "simulations\stress_v2_selftest.txt"
echo.
echo Output saved to simulations\stress_v2_selftest.txt
echo.
echo Press any key to close this window.
pause >nul
