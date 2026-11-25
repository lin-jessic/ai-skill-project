@echo off
setlocal
cd /d "%~dp0"
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
echo OpenShop LIFE PWA - Local Application
echo Project: %CD%
"%PY%" -m pip install -r requirements_pwa.txt
if errorlevel 1 (echo Dependency install failed.& pause & exit /b 1)
echo Open http://127.0.0.1:8502 in your browser.
"%PY%" -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
if errorlevel 1 echo Server failed. Check if port 8502 is in use.
pause
