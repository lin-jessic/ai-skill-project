@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Copy teacher input CSV or JSON into v2 folder, then type filename.
set /p FNAME=Enter CSV/JSON file path:
if not exist "%FNAME%" (echo File not found.&pause&exit /b 1)
python -m scripts.run_studio --input "%FNAME%" --shop "手搖飲店" --city "桃園市"
pause
