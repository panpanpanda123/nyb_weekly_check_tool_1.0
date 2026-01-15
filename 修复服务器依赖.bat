@echo off
chcp 65001 >nul
echo ========================================
echo 修复服务器依赖
echo ========================================
echo.

set SERVER_IP=139.224.200.133
set SERVER_USER=root
set SERVER_PATH=/opt/review-result-viewer

echo 正在连接服务器并安装缺失的依赖...
echo.

ssh %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && source venv/bin/activate && pip install openpyxl && sudo systemctl restart review-viewer"

if %errorlevel% equ 0 (
    echo.
    echo ✓ 依赖安装成功！
    echo ✓ 服务已重启！
    echo.
    echo 请访问: http://%SERVER_IP%
) else (
    echo.
    echo ✗ 安装失败！
    echo.
    echo 请手动执行以下命令：
    echo ssh %SERVER_USER%@%SERVER_IP%
    echo cd %SERVER_PATH%
    echo source venv/bin/activate
    echo pip install openpyxl
    echo sudo systemctl restart review-viewer
)

echo.
pause
