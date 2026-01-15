@echo off
chcp 65001 >nul
echo ========================================
echo 更新服务器代码
echo ========================================
echo.

set SERVER_IP=139.224.200.133
set SERVER_USER=root
set SERVER_PATH=/opt/review-result-viewer

echo 正在连接服务器并更新代码...
echo.

REM 使用 Git 拉取最新代码
ssh %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && git pull origin main && sudo systemctl restart review-viewer"

if %errorlevel% equ 0 (
    echo.
    echo ✓ 代码更新成功！
    echo ✓ 服务已重启！
    echo.
    echo 请访问: http://%SERVER_IP%
) else (
    echo.
    echo ✗ 更新失败！
    echo.
    echo 请手动执行以下命令：
    echo ssh %SERVER_USER%@%SERVER_IP%
    echo cd %SERVER_PATH%
    echo git pull
    echo sudo systemctl restart review-viewer
)

echo.
pause
