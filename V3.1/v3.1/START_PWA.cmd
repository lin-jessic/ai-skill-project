@echo off
setlocal
cd /d "%~dp0"
echo [1/2] Verify web assets...
python verify_web.py
if errorlevel 1 (echo FAILED: web assets & pause & exit /b 1)
echo [2/2] OpenShop LIFE at http://127.0.0.1:8502/
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
if errorlevel 1 (echo Server failed - install requirements_pwa.txt & pause & exit /b 1)
endlocal
