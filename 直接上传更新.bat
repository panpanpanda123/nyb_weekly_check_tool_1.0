@echo off
chcp 65001 >nul
echo ========================================
echo 直接上传文件到服务器（不用 Git）
echo ========================================
echo.

set SERVER_IP=139.224.200.133
set SERVER_USER=root
set SERVER_PATH=/opt/review-result-viewer

echo 正在上传修改的文件...
echo.

REM 上传 viewer 目录的文件
scp -r viewer/static/viewer.js %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/viewer/static/
scp -r viewer/static/viewer.css %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/viewer/static/
scp -r viewer/templates/viewer.html %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/viewer/templates/

if %errorlevel% neq 0 (
    echo ✗ 上传失败！
    pause
    exit
)

echo.
echo ✓ 文件上传成功！
echo.
echo 正在重启服务...
ssh %SERVER_USER%@%SERVER_IP% "sudo systemctl restart review-viewer"

if %errorlevel% equ 0 (
    echo.
    echo ✓ 服务已重启！
    echo.
    echo 现在可以访问: http://%SERVER_IP%/
) else (
    echo.
    echo ✗ 重启失败！
    echo 请手动执行: ssh %SERVER_USER%@%SERVER_IP%
    echo sudo systemctl restart review-viewer
)

echo.
pause
