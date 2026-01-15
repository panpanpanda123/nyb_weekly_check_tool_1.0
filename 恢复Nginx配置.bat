@echo off
chcp 65001 >nul
echo ========================================
echo 恢复 Nginx 配置到默认状态
echo ========================================
echo.

set SERVER_IP=139.224.200.133
set SERVER_USER=root
set SERVER_PATH=/opt/review-result-viewer

echo 正在上传配置文件到服务器...
echo.

REM 上传配置文件
scp deploy/nginx-default.conf %SERVER_USER%@%SERVER_IP%:/tmp/review-viewer.conf

if %errorlevel% neq 0 (
    echo ✗ 上传失败！
    pause
    exit
)

echo.
echo 正在应用配置...
echo.

REM 应用配置并重启
ssh %SERVER_USER%@%SERVER_IP% "sudo mv /tmp/review-viewer.conf /etc/nginx/sites-enabled/review-viewer && sudo nginx -t && sudo systemctl restart nginx"

if %errorlevel% equ 0 (
    echo.
    echo ✓ Nginx 配置已恢复！
    echo ✓ 服务已重启！
    echo.
    echo 现在可以访问: http://%SERVER_IP%/
) else (
    echo.
    echo ✗ 应用配置失败！
    echo.
    echo 请手动执行：
    echo ssh %SERVER_USER%@%SERVER_IP%
    echo sudo nano /etc/nginx/sites-enabled/review-viewer
)

echo.
pause

