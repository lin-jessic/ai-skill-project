@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (set "PY=py -3") else (set "PY=python")
%PY% -m pip install -r requirements.txt
if errorlevel 1 (echo Package installation failed.&pause&exit /b 1)
%PY% -m streamlit run app.py
pause
