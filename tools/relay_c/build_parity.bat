@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "%~dp0"
cl.exe /O2 /arch:AVX2 /Fe:parity_test.exe parity_test.c relay_pipeline.c
