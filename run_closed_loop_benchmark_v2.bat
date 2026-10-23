@echo off
REM Closed-loop benchmark for the ONE deployed model (leak-free run, 2026-10-18).
REM Change DEPLOYED_RUN here only; every step below uses it.
cd /d "%~dp0"
set DEPLOYED_RUN=runs\20261018_trace_split
set PY=".venv-lstm\Scripts\python.exe"

REM Safety: back up the Simulink model and network once before anything is changed.
if not exist "simulations\TransformerWithCTSaturation_BACKUP_20261018.slx" copy "simulations\TransformerWithCTSaturation.slx" "simulations\TransformerWithCTSaturation_BACKUP_20261018.slx" >nul
if not exist "simulations\live_relay_ai_BACKUP_20261018.mat" copy "simulations\live_relay_ai.mat" "simulations\live_relay_ai_BACKUP_20261018.mat" >nul

echo ============================================================
echo   1/5 Export ONNX from %DEPLOYED_RUN% (12 features, W=32)
echo ============================================================
%PY% lstm_models\export_onnx.py --checkpoint %DEPLOYED_RUN%\transformer_protection_lstm_best.pth --output lstm_models\wt_lstm_relay.onnx --sequence-length 32 || goto :fail

echo ============================================================
echo   2/5 Build live_relay_ai.mat
echo ============================================================
matlab -batch "cd('%~dp0lstm_models'); ONNXBUILDER" || goto :fail

echo ============================================================
echo   3/5 Feed the LSTM the training I_diff and set the tuned threshold
echo ============================================================
matlab -batch "cd('%~dp0simulations'); fix_lstm_input_raw_idiff(true); set_ai_threshold(str2double(fileread('%~dp0%DEPLOYED_RUN%\decision_threshold.txt')), true)" || goto :fail

echo ============================================================
echo   4/5 Feature parity check (must print PASS twice)
echo ============================================================
matlab -batch "cd('%~dp0simulations'); verify_lstm_feature_parity" > "simulations\feature_parity_results.txt" 2>&1
type "simulations\feature_parity_results.txt"

echo ============================================================
echo   5/5 Closed-loop Simulink benchmark
echo ============================================================
matlab -batch "cd('%~dp0simulations'); bdclose('all'); clear lstm_predict_wrapper; test_hybrid_relay"
type "%~dp0simulations\test_hybrid_relay_results.txt"
goto :eof

:fail
echo FAILED at the step above. See the message printed before this line.
exit /b 1
