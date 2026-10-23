@echo off
cd /d "%~dp0"
echo ============================================================
echo   1/3 Exporting ONNX Network (W=32)
echo ============================================================
python lstm_models\export_onnx.py --checkpoint runs\20260723_lstm_training\transformer_protection_lstm_best.pth --output lstm_models\wt_lstm_relay.onnx --sequence-length 32

echo ============================================================
echo   2/3 Building MATLAB Network Container live_relay_ai.mat
echo ============================================================
matlab -batch "cd('%~dp0lstm_models'); ONNXBUILDER"

echo ============================================================
echo   3/3 Executing Closed-Loop Simulink Benchmark Suite
echo ============================================================
matlab -batch "cd('%~dp0simulations'); bdclose('all'); clear lstm_predict_wrapper; test_hybrid_relay"

echo ============================================================
echo   VERIFICATION BENCHMARK COMPLETE
echo ============================================================
type "%~dp0simulations\test_hybrid_relay_results.txt"
