@echo off
chcp 65001 >nul
echo ========================================
echo 更新设备异常数据到服务器
echo ========================================
echo.
echo ⚠️  注意：需要配置SSH密钥或输入密码
echo    如果连接失败，请使用手动上传方式
echo    参考：手动更新设备数据指南.md
echo.

REM 设置服务器信息
set SERVER=root@139.224.200.133
set PROJECT_DIR=/var/www/nyb_weekly_check_tool_1.0

echo 📁 检查本地数据文件...
if not exist "equipment_status\牛约堡集团_点餐设备表*.xlsx" (
    echo ❌ 未找到收银设备文件
    pause
    exit /b 1
)

if not exist "equipment_status\202*.xlsx" (
    echo ❌ 未找到机顶盒文件
    pause
    exit /b 1
)

if not exist "equipment_status\牛约堡集团_门店档案*.xlsx" (
    echo ❌ 未找到门店档案文件
    pause
    exit /b 1
)

echo ✅ 本地文件检查完成
echo.

echo 📤 上传文件到服务器...
echo.

REM 上传收银设备文件
for %%f in (equipment_status\牛约堡集团_点餐设备表*.xlsx) do (
    echo 上传: %%f
    scp "%%f" %SERVER%:%PROJECT_DIR%/equipment_status/
)

REM 上传机顶盒文件
for %%f in (equipment_status\202*.xlsx) do (
    echo 上传: %%f
    scp "%%f" %SERVER%:%PROJECT_DIR%/equipment_status/
)

REM 上传门店档案文件
for %%f in (equipment_status\牛约堡集团_门店档案*.xlsx) do (
    echo 上传: %%f
    scp "%%f" %SERVER%:%PROJECT_DIR%/equipment_status/
)

echo.
echo ✅ 文件上传完成
echo.

echo 🔄 在服务器上导入数据...
ssh %SERVER% "cd %PROJECT_DIR% && python3 import_equipment_data.py"

if errorlevel 1 (
    echo.
    echo ❌ 数据导入失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 数据更新完成！
echo ========================================
echo.
echo 访问地址查看最新数据：
echo https://weeklycheck.blitzepanda.top/equipment
echo.
pause
