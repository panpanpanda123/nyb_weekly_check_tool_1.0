@echo off
chcp 65001 >nul
echo ==========================================
echo 本地测试设备异常功能修改
echo ==========================================
echo.

echo 📝 修改内容:
echo 1. 处理选项更新:
echo    - '已处理' → '已恢复'
echo    - '不配合' → 已删除
echo    - '特殊情况' → '未恢复(需填写原因)'
echo 2. 每次导入数据自动清空处理记录
echo.

echo 🔍 检查修改的文件:
echo.

echo ✅ viewer/static/equipment.js
findstr /C:"已恢复" viewer\static\equipment.js >nul
if %errorlevel%==0 (
    echo    - 找到 '已恢复'
) else (
    echo    ❌ 未找到 '已恢复'
)

findstr /C:"未恢复" viewer\static\equipment.js >nul
if %errorlevel%==0 (
    echo    - 找到 '未恢复'
) else (
    echo    ❌ 未找到 '未恢复'
)

echo.
echo ✅ import_equipment_data.py
findstr /C:"EquipmentProcessing" import_equipment_data.py >nul
if %errorlevel%==0 (
    echo    - 找到 EquipmentProcessing 清空代码
) else (
    echo    ❌ 未找到 EquipmentProcessing 清空代码
)

echo.
echo ✅ viewer/templates/equipment.html
findstr /C:"v=20260304-2" viewer\templates\equipment.html >nul
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
echo 下一步:
echo 1. 提交代码: git add . ^&^& git commit -m "修改设备异常处理选项"
echo 2. 推送到服务器: git push
echo 3. SSH登录服务器执行: cd /var/www/nyb_weekly_check_tool_1.0 ^&^& git pull ^&^& systemctl restart review-viewer
echo.
pause
