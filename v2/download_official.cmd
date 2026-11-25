@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title OpenShop - Fully Automatic Official Data Download

echo ==============================================
echo  OpenShop AI - AUTO Download Government Data
echo ==============================================
echo Folder: %CD%
echo NO browser. NO manual file picker.
echo.
if not exist "scripts\download_official.py" (
 echo ERROR: Put this file in v2 folder and Python file in v2\scripts
 pause
 exit /b 1
)
where py >nul 2>nul
if not errorlevel 1 (
 py -3 -m scripts.download_official --all-months
) else (
 python -m scripts.download_official --all-months
)
set "STATUS=%ERRORLEVEL%"
echo.
echo Download finished, exit code: %STATUS%
echo Check data\raw and data\official_download_manifest.json
echo.
pause
exit /b %STATUS%
