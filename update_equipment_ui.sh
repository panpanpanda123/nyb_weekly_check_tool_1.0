#!/bin/bash

echo "=========================================="
echo "更新设备异常功能UI"
echo "=========================================="
echo

# 重启服务
echo "🔄 重启服务..."
systemctl restart review-viewer

# 检查服务状态
echo "🔍 检查服务状态..."
if systemctl is-active --quiet review-viewer; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务启动失败"
    systemctl status review-viewer
    exit 1
fi

echo
echo "=========================================="
echo "✅ 更新完成！"
echo "=========================================="
echo
echo "访问地址:"
echo "- 周清审核: https://weeklycheck.blitzepanda.top/"
echo "- 门店评级: https://weeklycheck.blitzepanda.top/rating"
echo "- 设备异常: https://weeklycheck.blitzepanda.top/equipment"
echo
echo "修改内容:"
echo "1. 处理选项更新:"
echo "   - '已处理' → '已恢复'"
echo "   - '不配合' → 已删除"
echo "   - '特殊情况' → '未恢复(需填写原因)'"
echo "2. 每次导入数据自动清空处理记录"
echo "3. 更新缓存版本号强制刷新"
echo
