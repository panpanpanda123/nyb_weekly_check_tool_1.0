@echo off
chcp 65001 >nul
echo ========================================
echo 门店评级系统 - 快速修复上传
echo ========================================
echo.

echo [1/4] 上传修复后的代码...
scp rating_app.py root@blitzepanda.top:/opt/review-result-viewer/
if errorlevel 1 (
    echo ❌ 上传失败！请检查网络连接
    pause
    exit /b 1
)
echo ✅ 代码上传成功

echo.
echo [2/4] 检查数据文件...
scp rating_data/stores.json root@blitzepanda.top:/opt/review-result-viewer/rating_data/
if errorlevel 1 (
    echo ⚠️  数据文件上传失败（可能已存在）
) else (
    echo ✅ 数据文件上传成功
)

echo.
echo [3/4] 修复Nginx配置并重启服务...
ssh root@blitzepanda.top "sed -i 's|proxy_pass http://127.0.0.1:8000|proxy_pass http://127.0.0.1:8001|g' /etc/nginx/sites-available/default && nginx -t && systemctl reload nginx && systemctl restart rating"
if errorlevel 1 (
    echo ❌ 服务重启失败！
    pause
    exit /b 1
)
echo ✅ 服务重启成功

echo.
echo [4/4] 验证部署...
timeout /t 3 /nobreak >nul
ssh root@blitzepanda.top "curl -s http://127.0.0.1:8001/api/rating/war-zones | head -5"

echo.
echo ========================================
echo ✅ 修复完成！
echo ========================================
echo.
echo 修复内容：
echo - 修复评级显示问题
echo - 修复CSV导出None值错误
echo - 统一端口配置为8001
echo.
echo 请访问: http://blitzepanda.top/rating
echo.
echo 如果仍有问题，请运行以下命令查看日志：
echo ssh root@blitzepanda.top "tail -50 /opt/review-result-viewer/logs/rating_app.log"
echo.
pause
