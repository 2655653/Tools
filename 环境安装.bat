@echo off
chcp 65001 >nul
echo ==========================================
echo     这次一定有票 - 大麦抢票脚本环境安装
echo ==========================================
echo.

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] 检测到 Python
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 创建日志目录
if not exist "logs" mkdir logs

:: 升级 pip
echo [1/3] 升级 pip ...
python -m pip install --upgrade pip -q

:: 安装依赖
echo [2/3] 安装 Python 依赖（selenium, webdriver-manager, pillow, apscheduler, pytesseract）...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败，请尝试手动运行：
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

:: 检测 Chrome 版本
echo [3/3] 检测 Chrome 浏览器版本 ...
for /f "tokens=*" %%v in ('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version 2^>nul') do set "CHROME_VER=%%v"
for /f "tokens=3" %%v in ('echo %CHROME_VER%') do set "CHROME_VER=%%v"
echo       你的 Chrome 版本: %CHROME_VER%

echo.
echo ==========================================
echo     安装完成！
echo ==========================================
echo.
echo  接下来请按以下步骤操作：
echo  1. 确认 config.json 已填写正确（演出URL、观演人序号等）
echo  2. 运行: python ticket_script.py
echo  3. 首次运行会弹出浏览器，请扫码登录大麦
echo  4. 登录成功后按 Ctrl+C 停止，cookies.pkl 会自动保存
echo.
echo  chromedriver 由 webdriver-manager 自动匹配，无需手动下载！
echo.
pause
