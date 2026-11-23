@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==================================================
echo SafeRoad - 2024 + 2025 Official Accident Downloader
echo ==================================================
python --version
if errorlevel 1 (
 echo Python not found. Please install Python and add to PATH.
 pause
 exit /b 1
)
python scripts\download_official_2024_2025.py
set "STATUS=%ERRORLEVEL%"
echo.
if not "%STATUS%"=="0" echo Download error. See messages above and try manual download.
if "%STATUS%"=="0" echo Download finished. Run: python scriptsun_all.py
pause
exit /b %STATUS%
