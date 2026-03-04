#!/bin/bash
# 设备异常功能一键部署脚本

echo "=========================================="
echo "设备异常功能部署脚本"
echo "=========================================="
echo ""

# 检查是否在服务器上
if [ ! -d "/var/www/nyb_weekly_check_tool_1.0" ]; then
    echo "❌ 错误：未找到项目目录"
    echo "   请确保在服务器上执行此脚本"
    exit 1
fi

# 进入项目目录
cd /var/www/nyb_weekly_check_tool_1.0

echo "📁 当前目录: $(pwd)"
echo ""

# 1. 拉取最新代码
echo "📥 [1/5] 拉取最新代码..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Git拉取失败"
    exit 1
fi
echo "✅ 代码更新完成"
echo ""

# 2. 检查设备数据文件夹
echo "📂 [2/5] 检查设备数据文件夹..."
if [ ! -d "equipment_status" ]; then
    echo "   创建equipment_status文件夹..."
    mkdir -p equipment_status
fi

# 检查是否有数据文件
POS_FILE=$(ls equipment_status/牛约堡集团_点餐设备表*.xlsx 2>/dev/null | head -1)
STB_FILE=$(ls equipment_status/202*.xlsx 2>/dev/null | head -1)
STORE_FILE=$(ls equipment_status/牛约堡集团_门店档案*.xlsx 2>/dev/null | head -1)

if [ -z "$POS_FILE" ] || [ -z "$STB_FILE" ] || [ -z "$STORE_FILE" ]; then
    echo "⚠️  警告：设备数据文件不完整"
    echo "   需要的文件："
    echo "   - 牛约堡集团_点餐设备表*.xlsx"
    echo "   - 202*.xlsx"
    echo "   - 牛约堡集团_门店档案*.xlsx"
    echo ""
    echo "   请手动上传文件到 equipment_status/ 文件夹"
    echo "   然后重新运行此脚本"
    exit 1
fi

echo "✅ 数据文件检查完成"
echo "   - POS设备: $POS_FILE"
echo "   - 机顶盒: $STB_FILE"
echo "   - 门店档案: $STORE_FILE"
echo ""

# 3. 导入设备数据
echo "📥 [3/5] 导入设备数据..."
python3 import_equipment_data.py
if [ $? -ne 0 ]; then
    echo "❌ 数据导入失败"
    exit 1
fi
echo "✅ 数据导入完成"
echo ""

# 4. 重启服务
echo "🔄 [4/5] 重启服务..."
systemctl restart review-viewer
if [ $? -ne 0 ]; then
    echo "❌ 服务重启失败"
    exit 1
fi

# 等待服务启动
sleep 3

# 检查服务状态
if systemctl is-active --quiet review-viewer; then
    echo "✅ 服务重启成功"
else
    echo "❌ 服务未正常运行"
    echo "   查看日志: journalctl -u review-viewer -n 50"
    exit 1
fi
echo ""

# 5. 测试功能
echo "🧪 [5/5] 测试功能..."

# 测试页面
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/equipment)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 页面访问正常 (HTTP $HTTP_CODE)"
else
    echo "❌ 页面访问失败 (HTTP $HTTP_CODE)"
fi

# 测试API
API_RESPONSE=$(curl -s http://localhost:8000/api/equipment/filters)
if echo "$API_RESPONSE" | grep -q "success"; then
    echo "✅ API接口正常"
else
    echo "❌ API接口异常"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  https://weeklycheck.blitzepanda.top/equipment"
echo ""
echo "如需查看日志："
echo "  journalctl -u review-viewer -n 100 -f"
echo ""
