@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements_pwa.txt
if errorlevel 1 (pause & exit /b 1)
python verify_web.py
if errorlevel 1 (pause & exit /b 1)
python -m pytest -q
if errorlevel 1 (pause & exit /b 1)
echo ALL TESTS PASSED
pause
endlocal
