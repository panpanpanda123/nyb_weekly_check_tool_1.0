#!/bin/bash

echo "=========================================="
echo "部署移动端优化"
echo "=========================================="
echo

# 检查是否在项目目录
if [ ! -f "viewer/app_viewer.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull

if [ $? -ne 0 ]; then
    echo "❌ Git拉取失败"
    exit 1
fi

echo "✅ 代码更新成功"
echo

# 重启服务
echo "🔄 重启服务..."
systemctl restart review-viewer

if [ $? -ne 0 ]; then
    echo "❌ 服务重启失败"
    exit 1
fi

echo "✅ 服务重启成功"
echo

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查服务状态
echo "🔍 检查服务状态..."
if systemctl is-active --quiet review-viewer; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务未运行"
    echo "查看日志: journalctl -u review-viewer -n 50"
    exit 1
fi

echo

# 测试API
echo "🧪 测试API..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/equipment)

if [ "$response" = "200" ]; then
    echo "✅ API响应正常 (HTTP $response)"
else
    echo "⚠️  API响应异常 (HTTP $response)"
fi

echo
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo
echo "📱 访问地址:"
echo "- 周清审核: https://weeklycheck.blitzepanda.top/"
echo "- 门店评级: https://weeklycheck.blitzepanda.top/rating"
echo "- 设备异常: https://weeklycheck.blitzepanda.top/equipment"
echo
echo "🔍 验证步骤:"
echo "1. 手机浏览器访问上述地址"
echo "2. 检查布局是否单列显示"
echo "3. 测试按钮是否易于点击"
echo "4. 测试输入框是否会缩放"
echo "5. 测试所有功能是否正常"
echo
echo "📊 查看日志:"
echo "journalctl -u review-viewer -n 50 -f"
echo
echo "🔧 如遇问题:"
echo "1. 检查服务状态: systemctl status review-viewer"
echo "2. 查看错误日志: journalctl -u review-viewer -n 100"
echo "3. 重启服务: systemctl restart review-viewer"
echo
