@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
python .agents/skills/store-opening-advisor/scripts/download_official.py --check
exit /b %errorlevel%
