@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo OpenShop AI v2 - 官方資料收集工具
 echo ============================================
where python >nul 2>nul
if errorlevel 1 (
 echo [ERROR] 找不到 Python，請先安裝 Python 並加入 PATH。
 pause
 exit /b 1
)
python -m scripts.download_official
if errorlevel 1 echo [提醒] 請查看上方錯誤。
echo.
echo 查看已存檔案：
python -m scripts.download_official --check
pause
