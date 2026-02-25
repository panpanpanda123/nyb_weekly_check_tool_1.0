@echo off
chcp 65001 >nul
title 本地测试 - 周清审核系统

echo ========================================
echo 本地测试 - 周清审核系统
echo ========================================
echo.

REM 1. 导入数据
echo [步骤1] 导入测试数据...
python 本地测试导入.py
if errorlevel 1 (
    echo.
    echo ❌ 数据导入失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [步骤2] 启动本地测试服务器...
echo ========================================
echo.

REM 2. 设置环境变量使用本地SQLite数据库
set DATABASE_URL=sqlite:///local_test.db
set PORT=8002

REM 3. 启动服务器并在3秒后打开浏览器
echo 正在启动服务器（端口8002）...
echo 3秒后自动打开浏览器...
echo.
echo 提示：按 Ctrl+C 停止服务器
echo.

REM 启动服务器（后台）
start /B python viewer/app_viewer.py

REM 等待3秒让服务器启动
timeout /t 3 /nobreak >nul

REM 打开浏览器
start http://127.0.0.1:8002

REM 等待用户按键
echo.
echo ========================================
echo 服务器已启动
echo 浏览器地址: http://127.0.0.1:8002
echo ========================================
echo.
pause
