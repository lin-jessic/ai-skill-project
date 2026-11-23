@echo off
chcp 65001 >nul
cd /d "%~dp0"
python scripts\download_official_2026.py --only all
pause
