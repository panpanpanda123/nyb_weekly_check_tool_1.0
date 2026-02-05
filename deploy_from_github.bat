@echo off
chcp 65001 >nul
echo ========================================
echo 从GitHub部署到服务器
echo ========================================
echo.

echo [1/5] 连接服务器...
ssh root@blitzepanda.top "echo '✅ 连接成功'"
if errorlevel 1 (
    echo ❌ 无法连接到服务器
    pause
    exit /b 1
)

echo.
echo [2/5] 备份当前评分数据...
ssh root@blitzepanda.top "cd /opt/review-result-viewer && cp rating_data/ratings.json rating_data/ratings.backup.$(date +%%Y%%m%%d_%%H%%M%%S).json 2>/dev/null || echo '无需备份（文件不存在）'"

echo.
echo [3/5] 从GitHub拉取最新代码...
ssh root@blitzepanda.top "cd /opt/review-result-viewer && git pull origin main"
if errorlevel 1 (
    echo ❌ Git拉取失败
    echo 提示：可能需要先在服务器上执行 git stash
    pause
    exit /b 1
)

echo.
echo [4/5] 重启评级服务...
ssh root@blitzepanda.top "systemctl restart rating"
if errorlevel 1 (
    echo ❌ 服务重启失败
    pause
    exit /b 1
)

echo.
echo [5/5] 验证部署...
timeout /t 3 /nobreak >nul
ssh root@blitzepanda.top "systemctl status rating | head -5"

echo.
echo ========================================
echo ✅ 部署完成！
echo ========================================
echo.
echo 请测试以下功能：
echo 1. 访问页面：http://blitzepanda.top/rating
echo 2. 测试导出功能（点击右上角导出按钮）
echo 3. 确认已有评分数据都还在
echo.
echo 如需查看日志：
echo ssh root@blitzepanda.top "tail -50 /opt/review-result-viewer/logs/rating_app.log"
echo.
pause
