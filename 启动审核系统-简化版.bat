@echo off
chcp 65001 >nul
title 门店检查项审核系统
color 0A

echo ========================================
echo    门店检查项审核系统
echo ========================================
echo.

:: 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b
)

:: 检查数据文件是否存在
if not exist "检查项记录.xlsx" (
    echo [警告] 未找到"检查项记录.xlsx"
    echo.
    echo 请手动将本周的Excel文件重命名为"检查项记录.xlsx"
    echo 并放在当前目录下，然后重新运行此脚本
    echo.
    pause
    exit /b
)

echo [✓] 找到数据文件: 检查项记录.xlsx
echo.
echo 正在启动系统...
echo.

:: 启动Python应用
python app.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请查看上方错误信息
    pause
)
