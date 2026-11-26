@echo off
setlocal
cd /d "%~dp0"
echo [1/2] Running v4 preflight...
python preflight_v4.py
if errorlevel 1 (pause & exit /b 1)
echo [2/2] OpenShop LIFE v4 at http://127.0.0.1:8502/
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
if errorlevel 1 (echo Server failed - run CHECK_V4.cmd first & pause & exit /b 1)
endlocal
