@echo off
REM Deploy + benchmark the PLANT-COMPENSATED model (runs\20261020_v2_plant) in Simulink.
REM Close MATLAB / the Simulink model first: do not run two MATLABs on the model at once.
REM Python: system Python 3.11 + .pylibs (numpy 1.26, PyWavelets) because .venv-lstm lost its base interpreter.
cd /d "%~dp0"
set DEPLOYED_RUN=runs\20261020_v2_plant
set PY="C:\Users\Abeer\AppData\Local\Programs\Python\Python311\python.exe"
set PYTHONPATH=%~dp0.pylibs

REM Safety: back up the Simulink model, network and wrapper config once before anything is changed.
if not exist "simulations\TransformerWithCTSaturation_BACKUP_20261020_pre_plant.slx" copy "simulations\TransformerWithCTSaturation.slx" "simulations\TransformerWithCTSaturation_BACKUP_20261020_pre_plant.slx" >nul
if not exist "simulations\live_relay_ai_BACKUP_20261020_pre_plant.mat" copy "simulations\live_relay_ai.mat" "simulations\live_relay_ai_BACKUP_20261020_pre_plant.mat" >nul
if not exist "lstm_models\wt_lstm_relay_BACKUP_20261020_pre_plant.onnx" copy "lstm_models\wt_lstm_relay.onnx" "lstm_models\wt_lstm_relay_BACKUP_20261020_pre_plant.onnx" >nul

echo ============================================================
echo   1/5 Export ONNX from %DEPLOYED_RUN% (12 features, W=32)
echo ============================================================
%PY% lstm_models\export_onnx.py --checkpoint %DEPLOYED_RUN%\transformer_protection_lstm_best.pth --output lstm_models\wt_lstm_relay.onnx --sequence-length 32 || goto :fail

echo ============================================================
echo   2/5 Build live_relay_ai.mat
echo ============================================================
matlab -batch "cd('%~dp0lstm_models'); ONNXBUILDER" || goto :fail

echo ============================================================
echo   3/5 Plant-compensated LSTM input + tuned threshold + dwell check
echo ============================================================
for /f %%d in (%DEPLOYED_RUN%\decision_dwell.txt) do set DW=%%d
echo Deployed dwell = %DW% (relay_config.m must say the same)
findstr /c:"AI_DWELL   = %DW%;" simulations\relay_config.m >nul || (echo relay_config.m AI_DWELL does not match decision_dwell.txt = %DW% & goto :fail)
matlab -batch "cd('%~dp0simulations'); bdclose('all'); fix_lstm_input_plant_idiff(true); set_ai_threshold(str2double(fileread('%~dp0%DEPLOYED_RUN%\decision_threshold.txt')), true)" || goto :fail

echo ============================================================
echo   4/5 Feature parity check (must print PASS twice)
echo ============================================================
matlab -batch "cd('%~dp0simulations'); verify_lstm_feature_parity_plant" > "simulations\feature_parity_plant_results.txt" 2>&1
type "simulations\feature_parity_plant_results.txt"

echo ============================================================
echo   5/5 Closed-loop Simulink benchmark
echo ============================================================
matlab -batch "cd('%~dp0simulations'); bdclose('all'); clear lstm_predict_wrapper; test_hybrid_relay"
type "%~dp0simulations\test_hybrid_relay_results.txt"
goto :eof

:fail
echo FAILED at the step above. See the message printed before this line.
exit /b 1
