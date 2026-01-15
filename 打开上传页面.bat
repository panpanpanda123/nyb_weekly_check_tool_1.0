@echo off
chcp 65001 >nul
echo ========================================
echo 打开服务器上传页面
echo ========================================
echo.
echo 正在打开浏览器...
echo.
echo 上传步骤：
echo 1. 点击"选择文件"按钮
echo 2. 选择你的白名单 Excel 文件或审核结果 CSV 文件
echo 3. 点击"上传"按钮
echo 4. 等待上传完成
echo.

start http://139.224.200.133/admin/upload

echo ✓ 浏览器已打开！
echo.
pause
