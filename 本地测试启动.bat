@echo off
chcp 65001 >nul
echo ========================================
echo 审核结果展示系统 - 本地测试启动
echo ========================================
echo.

REM 设置环境变量
set DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops
set FLASK_ENV=development
set PORT=8000
set SECRET_KEY=local-test-secret-key

echo [1/3] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo.

echo [2/3] 检查依赖包...
python -c "import flask, sqlalchemy, psycopg2" 2>nul
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install flask sqlalchemy psycopg2-binary python-dotenv pandas openpyxl werkzeug
    echo.
)

echo [3/3] 启动展示系统...
echo.
echo ========================================
echo 系统启动中...
echo 访问地址: http://localhost:8000
echo 管理页面: http://localhost:8000/admin/upload
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%
python viewer\app_viewer.py

pause
