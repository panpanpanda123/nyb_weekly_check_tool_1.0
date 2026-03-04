@echo off
chcp 65001 >nul
echo ========================================
echo 本地测试 - 设备异常监控
echo ========================================
echo.

echo [步骤1] 导入设备异常数据...
python import_equipment_data.py
if errorlevel 1 (
    echo.
    echo ❌ 数据导入失败
    pause
    exit /b 1
)

echo.
echo [步骤2] 启动Web服务...
echo 🌐 访问地址: http://localhost:8000/equipment
echo.
python viewer/app_viewer.py

pause
