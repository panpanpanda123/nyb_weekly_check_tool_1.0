@echo off
chcp 65001 >nul
echo ==========================================
echo 测试移动端优化
echo ==========================================
echo.

echo 📱 检查移动端优化...
echo.

echo ✅ 检查viewport配置
findstr /C:"maximum-scale=1.0" viewer\templates\equipment.html >nul
if %errorlevel%==0 (
    echo    - equipment.html: viewport已配置
) else (
    echo    ❌ equipment.html: viewport未配置
)

findstr /C:"maximum-scale=1.0" viewer\templates\viewer.html >nul
if %errorlevel%==0 (
    echo    - viewer.html: viewport已配置
) else (
    echo    ❌ viewer.html: viewport未配置
)

echo.
echo ✅ 检查CSS移动端样式
findstr /C:"@media (max-width: 768px)" viewer\static\viewer.css >nul
if %errorlevel%==0 (
    echo    - 找到移动端媒体查询
) else (
    echo    ❌ 未找到移动端媒体查询
)

findstr /C:"min-height: 48px" viewer\static\viewer.css >nul
if %errorlevel%==0 (
    echo    - 找到触摸目标优化
) else (
    echo    ❌ 未找到触摸目标优化
)

findstr /C:"移动端设备异常优化" viewer\static\viewer.css >nul
if %errorlevel%==0 (
    echo    - 找到设备异常移动端样式
) else (
    echo    ❌ 未找到设备异常移动端样式
)

echo.
echo ✅ 检查版本号
findstr /C:"v=20260304-3" viewer\templates\equipment.html >nul
if %errorlevel%==0 (
    echo    - equipment.html: 版本号已更新
) else (
    echo    ❌ equipment.html: 版本号未更新
)

findstr /C:"v=20260304-3" viewer\templates\viewer.html >nul
if %errorlevel%==0 (
    echo    - viewer.html: 版本号已更新
) else (
    echo    ❌ viewer.html: 版本号未更新
)

echo.
echo ==========================================
echo ✅ 检查完成！
echo ==========================================
echo.
echo 📱 移动端测试方法:
echo.
echo 方法1: Chrome DevTools
echo   1. 打开 Chrome 浏览器
echo   2. 按 F12 打开开发者工具
echo   3. 按 Ctrl+Shift+M 切换设备模式
echo   4. 选择设备型号(如 iPhone 12)
echo   5. 访问 http://localhost:8000/equipment
echo.
echo 方法2: 真机测试
echo   1. 确保手机和电脑在同一WiFi
echo   2. 查看电脑IP: ipconfig
echo   3. 手机浏览器访问: http://[电脑IP]:8000/equipment
echo.
echo 方法3: 部署后测试
echo   1. 部署到服务器
echo   2. 手机访问: https://weeklycheck.blitzepanda.top/equipment
echo.
echo 🔍 测试要点:
echo   - 按钮是否足够大(易于点击)
echo   - 输入框点击后是否缩放
echo   - 布局是否单列显示
echo   - 文字是否清晰可读
echo   - 滚动是否流畅
echo   - 图片是否正常显示
echo.
pause
