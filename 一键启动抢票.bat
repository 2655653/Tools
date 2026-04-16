@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先运行 环境安装.bat
    pause
    exit /b 1
)

:: 检查依赖
python -c "import selenium" >nul 2>&1
if errorlevel 1 (
    echo [警告] selenium 未安装，正在安装 ...
    pip install -r requirements.txt -q
)

echo.
echo 启动抢票脚本 ...
echo 首次运行会弹出浏览器，请扫码登录大麦账号
echo chromedriver 由 webdriver-manager 自动匹配，无需手动下载
echo.
python ticket_script.py
pause
