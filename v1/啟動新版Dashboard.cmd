@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo SafeRoad Studio v3 - Starting...
python -m streamlit run app_v3.py
if errorlevel 1 (
 echo.
 echo 啟動失敗，請先執行 python -m pip install -r requirements.txt
 pause
)
