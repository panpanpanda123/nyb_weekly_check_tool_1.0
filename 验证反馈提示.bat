@echo off
chcp 65001 >nul
echo ==========================================
echo 验证反馈提示添加
echo ==========================================
echo.

echo 📝 检查HTML文件...
echo.

echo ✅ equipment.html
findstr /C:"有使用问题或BUG" viewer\templates\equipment.html >nul
if %errorlevel%==0 (
    echo    - 找到反馈提示
) else (
    echo    ❌ 未找到反馈提示
)

echo.
echo ✅ viewer.html
findstr /C:"有使用问题或BUG" viewer\templates\viewer.html >nul
if %errorlevel%==0 (
    echo    - 找到反馈提示
) else (
    echo    ❌ 未找到反馈提示
)

echo.
echo ✅ rating.html
findstr /C:"有使用问题或BUG" viewer\templates\rating.html >nul
if %errorlevel%==0 (
    echo    - 找到反馈提示
) else (
    echo    ❌ 未找到反馈提示
)

echo.
echo 🎨 检查CSS样式...
echo.

echo ✅ viewer.css
findstr /C:"feedback-notice" viewer\static\viewer.css >nul
if %errorlevel%==0 (
    echo    - 找到反馈提示样式
) else (
    echo    ❌ 未找到反馈提示样式
)

echo.
echo ✅ rating.css
findstr /C:"feedback-notice" viewer\static\rating.css >nul
if %errorlevel%==0 (
    echo    - 找到反馈提示样式
) else (
    echo    ❌ 未找到反馈提示样式
)

echo.
echo 🔢 检查版本号...
echo.

echo ✅ equipment.html
findstr /C:"v=20260304-4" viewer\templates\equipment.html >nul
if %errorlevel%==0 (
    echo    - 版本号已更新
) else (
    echo    ❌ 版本号未更新
)

echo.
echo ✅ viewer.html
findstr /C:"v=20260304-4" viewer\templates\viewer.html >nul
if %errorlevel%==0 (
    echo    - 版本号已更新
) else (
    echo    ❌ 版本号未更新
)

echo.
echo ✅ rating.html
findstr /C:"v=20260304" viewer\templates\rating.html >nul
if %errorlevel%==0 (
    echo    - 版本号已更新
) else (
    echo    ❌ 版本号未更新
)

echo.
echo ==========================================
echo ✅ 检查完成！
echo ==========================================
echo.
echo 📱 反馈提示位置:
echo   - 设备异常: 标题下方,功能选项卡上方
echo   - 周清审核: 标题下方,功能选项卡上方
echo   - 门店评级: 标题栏下方,评价标准上方
echo.
echo 🎨 样式特点:
echo   - 黄色渐变背景
echo   - 左侧橙色边框
echo   - 居中显示
echo   - 阴影效果
echo.
echo 🚀 部署步骤:
echo   1. git add .
echo   2. git commit -m "添加反馈提示"
echo   3. git push
echo   4. 服务器: git pull ^&^& systemctl restart review-viewer
echo.
pause
