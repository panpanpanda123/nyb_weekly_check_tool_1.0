@echo off
chcp 65001 >nul
title 一键上传所有设备数据到服务器
color 0A

echo.
echo ============================================================
echo           一键上传所有设备数据到服务器
echo ============================================================
echo.
echo 使用说明：
echo 1. 将最新的Excel文件放到 equipment_status 文件夹
echo 2. 双击运行本脚本
echo 3. 输入服务器密码
echo 4. 等待完成
echo.
echo ============================================================
echo.

REM 检查是否安装了plink和pscp
if not exist "plink.exe" (
    echo ❌ 缺少 plink.exe 工具
    echo.
    echo 请按以下步骤操作：
    echo 1. 访问 https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    echo 2. 下载 putty.zip
    echo 3. 解压后将 plink.exe 和 pscp.exe 复制到本文件夹
    echo.
    pause
    exit /b 1
)

if not exist "pscp.exe" (
    echo ❌ 缺少 pscp.exe 工具
    echo.
    echo 请按以下步骤操作：
    echo 1. 访问 https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    echo 2. 下载 putty.zip
    echo 3. 解压后将 plink.exe 和 pscp.exe 复制到本文件夹
    echo.
    pause
    exit /b 1
)

REM 服务器信息
set SERVER=139.224.200.133
set USER=root
set PROJECT_DIR=/var/www/nyb_weekly_check_tool_1.0

echo 📁 检查本地数据文件...
echo.

REM 检查在营门店文件
set FOUND_OPERATING=0
for %%f in (equipment_status\*在营门店*.xlsx) do (
    set FOUND_OPERATING=1
    set OPERATING_FILE=%%f
)

if %FOUND_OPERATING%==0 (
    echo ❌ 未找到在营门店文件
    echo    请确保文件名包含"在营门店"
    echo.
    pause
    exit /b 1
)

echo ✅ 找到在营门店文件: %OPERATING_FILE%

REM 检查收银设备文件
set FOUND_POS=0
for %%f in (equipment_status\牛约堡集团_点餐设备表*.xlsx) do (
    set FOUND_POS=1
    set POS_FILE=%%f
)

if %FOUND_POS%==0 (
    echo ❌ 未找到收银设备文件
    echo    请确保文件名包含"牛约堡集团_点餐设备表"
    echo.
    pause
    exit /b 1
)

echo ✅ 找到收银设备文件: %POS_FILE%

REM 检查机顶盒文件
set FOUND_STB=0
for %%f in (equipment_status\202*.xlsx) do (
    set FOUND_STB=1
    set STB_FILE=%%f
)

if %FOUND_STB%==0 (
    echo ❌ 未找到机顶盒文件
    echo    请确保文件名以"202"开头
    echo.
    pause
    exit /b 1
)

echo ✅ 找到机顶盒文件: %STB_FILE%
echo.

REM 输入密码
echo 请输入服务器密码：
set /p PASSWORD=

if "%PASSWORD%"=="" (
    echo ❌ 密码不能为空
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 开始上传和导入...
echo ============================================================
echo.

REM 上传在营门店文件
echo [1/4] 上传在营门店文件...
pscp -pw %PASSWORD% "%OPERATING_FILE%" %USER%@%SERVER%:%PROJECT_DIR%/equipment_status/
if errorlevel 1 (
    echo ❌ 上传失败，请检查密码是否正确
    pause
    exit /b 1
)
echo ✅ 上传成功
echo.

REM 上传收银设备文件
echo [2/4] 上传收银设备文件...
pscp -pw %PASSWORD% "%POS_FILE%" %USER%@%SERVER%:%PROJECT_DIR%/equipment_status/
if errorlevel 1 (
    echo ❌ 上传失败
    pause
    exit /b 1
)
echo ✅ 上传成功
echo.

REM 上传机顶盒文件
echo [3/4] 上传机顶盒文件...
pscp -pw %PASSWORD% "%STB_FILE%" %USER%@%SERVER%:%PROJECT_DIR%/equipment_status/
if errorlevel 1 (
    echo ❌ 上传失败
    pause
    exit /b 1
)
echo ✅ 上传成功
echo.

REM 执行导入命令
echo [4/4] 导入所有设备数据到数据库...
plink -pw %PASSWORD% %USER%@%SERVER% "cd %PROJECT_DIR% && python3 import_equipment_data.py"
if errorlevel 1 (
    echo ❌ 导入失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ 全部完成！
echo ============================================================
echo.
echo 访问地址查看最新数据：
echo https://weeklycheck.blitzepanda.top/equipment
echo.
echo 按任意键退出...
pause >nul
