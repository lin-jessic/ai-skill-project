@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python -m pytest -q
if errorlevel 1 goto fail
python -m scripts.run_pipeline
pause
exit /b 0
:fail
echo Execution failed. Review error above.
pause
exit /b 1
