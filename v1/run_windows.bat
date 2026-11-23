@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 (echo Cannot create Python 3.12 environment & pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (echo Dependency install failed & pause & exit /b 1)
echo.
echo Step 1: Download real original government data
".venv\Scripts\python.exe" scripts\download_data.py
if errorlevel 1 (
 echo Download unsuccessful. Please manually save real official A1 JSON in data\raw\a1_official.json
 echo Official source: https://data.gov.tw/dataset/57023
 pause
 exit /b 2
)
echo Step 2: Run all three stages
".venv\Scripts\python.exe" scripts\run_pipeline.py --input data\raw\a1_official.json
if errorlevel 1 (echo Pipeline failed, see errors above & pause & exit /b 3)
echo Step 3: Open local dashboard
".venv\Scripts\python.exe" -m streamlit run app.py
