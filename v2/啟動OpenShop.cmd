@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python -m streamlit run app.py
exit /b %errorlevel%
:fail
echo Python dependency installation failed.
pause
exit /b 1
