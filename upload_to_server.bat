@echo off
chcp 65001 >nul
echo ========================================
echo 一键上传文件到服务器
echo ========================================
echo.

REM 服务器配置
set SERVER_IP=139.224.200.133
set SERVER_USER=root
set SERVER_PATH=/opt/review-result-viewer

echo 请选择要上传的文件类型：
echo 1. 白名单文件 (Excel .xlsx)
echo 2. 审核结果文件 (CSV .csv)
echo 3. 整个项目代码
echo.
set /p choice=请输入选项 (1/2/3): 

if "%choice%"=="1" goto upload_whitelist
if "%choice%"=="2" goto upload_reviews
if "%choice%"=="3" goto upload_project
echo 无效选项！
pause
exit

:upload_whitelist
echo.
echo 请将白名单 Excel 文件拖到这里，然后按回车：
set /p file_path=
echo.
echo 正在上传白名单文件到服务器...
scp %file_path% %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/data/whitelist.xlsx
if %errorlevel% equ 0 (
    echo ✓ 上传成功！
    echo.
    echo 现在请访问: http://%SERVER_IP%/admin/upload
    echo 在网页上点击"上传白名单"按钮，选择刚才上传的文件
) else (
    echo ✗ 上传失败！请检查网络连接和服务器配置
)
pause
exit

:upload_reviews
echo.
echo 请将审核结果 CSV 文件拖到这里，然后按回车：
set /p file_path=
echo.
echo 正在上传审核结果文件到服务器...
scp %file_path% %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/data/reviews.csv
if %errorlevel% equ 0 (
    echo ✓ 上传成功！
    echo.
    echo 现在请访问: http://%SERVER_IP%/admin/upload
    echo 在网页上点击"上传审核结果"按钮，选择刚才上传的文件
) else (
    echo ✗ 上传失败！请检查网络连接和服务器配置
)
pause
exit

:upload_project
echo.
echo 正在上传整个项目到服务器...
echo 这可能需要几分钟时间...
echo.

REM 排除不需要的文件和目录
scp -r ^
    --exclude=".git" ^
    --exclude="__pycache__" ^
    --exclude="*.pyc" ^
    --exclude=".pytest_cache" ^
    --exclude="venv" ^
    --exclude="node_modules" ^
    --exclude="*.log" ^
    . %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/

if %errorlevel% equ 0 (
    echo ✓ 上传成功！
    echo.
    echo 正在重启服务...
    ssh %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && sudo systemctl restart review-viewer"
    echo.
    echo ✓ 服务已重启！
    echo 请访问: http://%SERVER_IP%
) else (
    echo ✗ 上传失败！请检查网络连接和服务器配置
)
pause
exit
