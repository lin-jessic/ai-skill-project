@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)
echo [1/4] Installing dependencies...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo [2/4] Processing all official data in data\raw...
"%PY%" scripts\run_all.py
if errorlevel 1 goto :fail
echo [3/4] Running tests...
"%PY%" -m pytest -q
if errorlevel 1 goto :fail
echo [4/4] Opening dashboard...
"%PY%" -m streamlit run app.py
exit /b %errorlevel%
:fail
echo Run failed. Review error output, do not claim analysis success.
pause
exit /b 1
