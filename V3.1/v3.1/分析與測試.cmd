@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m pytest -q
if errorlevel 1 (echo Tests failed.&pause&exit /b 1)
python -m scripts.run_studio --input "examples\DEMO_商圈資料_情境假設_非官方.csv" --shop "手搖飲店" --city "桃園市"
pause
