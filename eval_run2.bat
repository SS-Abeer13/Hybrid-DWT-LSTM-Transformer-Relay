@echo off
cd /d "%~dp0"
".venv-lstm\Scripts\python.exe" "simulations\evaluate_simulated_cases_v2.py" 1> "simulations\lstm_eval_v2_output.txt" 2>&1
echo EXITCODE=%ERRORLEVEL%>> "simulations\lstm_eval_v2_output.txt"
