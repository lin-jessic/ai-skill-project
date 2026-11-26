@echo off
setlocal
cd /d "%~dp0"
python preflight_v4.py
if errorlevel 1 (pause & exit /b 1)
python verify_web.py
if errorlevel 1 (pause & exit /b 1)
python -m pytest -q
if errorlevel 1 (pause & exit /b 1)
echo V4 CHECK PASSED
pause
endlocal
