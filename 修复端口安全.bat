@echo off
chcp 65001 >nul
echo ========================================
echo 修复端口安全配置
echo ========================================
echo.

set SERVER_IP=139.224.200.133/2112
set SERVER_USER=root

echo 正在连接服务器并修复配置...
echo.

ssh %SERVER_USER%@%SERVER_IP% "sudo sed -i 's/--bind 0.0.0.0:8000/--bind 127.0.0.1:8000/g' /etc/systemd/system/review-viewer.service && sudo systemctl daemon-reload && sudo systemctl restart review-viewer && echo '✓ Gunicorn 已改为只监听 127.0.0.1:8000' && netstat -nltp | grep 8000"

if %errorlevel% equ 0 (
    echo.
    echo ✓ 端口安全配置已修复！
    echo.
    echo 现在 8000 端口只能从服务器内部访问
    echo 外部访问必须通过 Nginx (80端口)
) else (
    echo.
    echo ✗ 修复失败！
    echo.
    echo 请手动执行：
    echo ssh %SERVER_USER%@%SERVER_IP%
    echo sudo nano /etc/systemd/system/review-viewer.service
    echo 将 --bind 0.0.0.0:8000 改为 --bind 127.0.0.1:8000
)

echo.
pause
