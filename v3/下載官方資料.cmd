@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo OpenShop AI - Official data downloader
echo Files are saved under data\raw\.
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python -m scripts.download_official
if errorlevel 1 echo Some official servers did not return data. Read README and download manually.
pause
exit /b 0
:fail
echo Dependency installation failed.
pause
exit /b 1
