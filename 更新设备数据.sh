#!/bin/bash
# 更新设备异常数据到服务器

echo "=========================================="
echo "更新设备异常数据到服务器"
echo "=========================================="
echo ""
echo "⚠️  注意：需要配置SSH密钥或输入密码"
echo "   如果连接失败，请使用手动上传方式"
echo "   参考：手动更新设备数据指南.md"
echo ""

# 设置服务器信息
SERVER="root@139.224.200.133"
PROJECT_DIR="/var/www/nyb_weekly_check_tool_1.0"

# 检查本地数据文件
echo "📁 检查本地数据文件..."

POS_FILE=$(ls equipment_status/牛约堡集团_点餐设备表*.xlsx 2>/dev/null | head -1)
STB_FILE=$(ls equipment_status/202*.xlsx 2>/dev/null | head -1)
STORE_FILE=$(ls equipment_status/牛约堡集团_门店档案*.xlsx 2>/dev/null | head -1)

if [ -z "$POS_FILE" ]; then
    echo "❌ 未找到收银设备文件"
    exit 1
fi

if [ -z "$STB_FILE" ]; then
    echo "❌ 未找到机顶盒文件"
    exit 1
fi

if [ -z "$STORE_FILE" ]; then
    echo "❌ 未找到门店档案文件"
    exit 1
fi

echo "✅ 本地文件检查完成"
echo "   - 收银设备: $POS_FILE"
echo "   - 机顶盒: $STB_FILE"
echo "   - 门店档案: $STORE_FILE"
echo ""

# 上传文件到服务器
echo "📤 上传文件到服务器..."

scp "$POS_FILE" "$SERVER:$PROJECT_DIR/equipment_status/"
scp "$STB_FILE" "$SERVER:$PROJECT_DIR/equipment_status/"
scp "$STORE_FILE" "$SERVER:$PROJECT_DIR/equipment_status/"

if [ $? -ne 0 ]; then
    echo "❌ 文件上传失败"
    exit 1
fi

echo "✅ 文件上传完成"
echo ""

# 在服务器上导入数据
echo "🔄 在服务器上导入数据..."
ssh "$SERVER" "cd $PROJECT_DIR && python3 import_equipment_data.py"

if [ $? -ne 0 ]; then
    echo "❌ 数据导入失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 数据更新完成！"
echo "=========================================="
echo ""
echo "访问地址查看最新数据："
echo "https://weeklycheck.blitzepanda.top/equipment"
echo ""
