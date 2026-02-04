@echo off
chcp 65001 >nul
echo ============================================================
echo 上传门店评级系统到云服务器
echo ============================================================
echo.

REM 设置服务器信息
set SERVER=root@blitzepanda.top
set REMOTE_DIR=/root/rating

echo 📦 准备上传文件...
echo.

REM 上传主应用文件
echo [1/6] 上传 rating_app.py...
scp rating_app.py %SERVER%:%REMOTE_DIR%/

REM 上传门店数据
echo [2/6] 上传 stores.json...
scp rating_data/stores.json %SERVER%:%REMOTE_DIR%/rating_data/

REM 上传模板文件
echo [3/6] 上传 rating.html...
scp viewer/templates/rating.html %SERVER%:%REMOTE_DIR%/viewer/templates/

REM 上传JS文件
echo [4/6] 上传 rating.js...
scp viewer/static/rating.js %SERVER%:%REMOTE_DIR%/viewer/static/

REM 上传CSS文件
echo [5/6] 上传 rating.css...
scp viewer/static/rating.css %SERVER%:%REMOTE_DIR%/viewer/static/

REM 上传部署脚本
echo [6/6] 上传部署脚本...
scp deploy/deploy_rating.sh %SERVER%:%REMOTE_DIR%/

echo.
echo ============================================================
echo ✅ 文件上传完成！
echo ============================================================
echo.
echo 下一步操作：
echo 1. SSH连接到服务器: ssh %SERVER%
echo 2. 进入目录: cd %REMOTE_DIR%
echo 3. 运行部署脚本: bash deploy_rating.sh
echo 4. 启动服务: systemctl start rating
echo 5. 查看状态: systemctl status rating
echo 6. 访问: http://blitzepanda.top/rating
echo.
pause
