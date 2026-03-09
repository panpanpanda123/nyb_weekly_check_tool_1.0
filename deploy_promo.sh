#!/bin/bash
# 活动参与度监控系统部署脚本

echo "======================================"
echo "活动参与度监控系统部署"
echo "======================================"

# 检查是否在项目根目录
if [ ! -f "import_promo_data.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 1. 创建数据文件夹
echo ""
echo "1. 创建数据文件夹..."
mkdir -p promo_data
mkdir -p logs
echo "✓ 数据文件夹创建完成"

# 2. 初始化数据库表
echo ""
echo "2. 初始化数据库表..."
python3 << EOF
from shared.database_models import create_db_engine, init_viewer_db
import os

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

engine = create_db_engine(DATABASE_URL, echo=False)
init_viewer_db(engine)
print("✓ 数据库表初始化完成")
EOF

# 3. 检查数据文件
echo ""
echo "3. 检查数据文件..."
if [ -f "promo_data/3月活动门店表.xlsx" ]; then
    echo "✓ 找到活动门店表"
else
    echo "⚠️  未找到活动门店表，请上传到 promo_data/ 文件夹"
fi

if ls promo_data/活动参与度*.xlsx 1> /dev/null 2>&1; then
    echo "✓ 找到活动参与度文件"
else
    echo "⚠️  未找到活动参与度文件，请上传到 promo_data/ 文件夹"
fi

# 4. 导入数据（如果文件存在）
echo ""
echo "4. 导入数据..."
if ls promo_data/活动参与度*.xlsx 1> /dev/null 2>&1; then
    python3 import_promo_data.py
else
    echo "⚠️  跳过数据导入（文件不存在）"
fi

# 5. 重启服务
echo ""
echo "5. 重启服务..."
sudo systemctl restart review-viewer
sleep 2

# 6. 检查服务状态
echo ""
echo "6. 检查服务状态..."
if sudo systemctl is-active --quiet review-viewer; then
    echo "✓ 服务运行正常"
else
    echo "❌ 服务启动失败，请检查日志"
    sudo systemctl status review-viewer
    exit 1
fi

# 7. 完成
echo ""
echo "======================================"
echo "✓ 部署完成！"
echo "======================================"
echo ""
echo "访问地址："
echo "  https://weeklycheck.blitzepanda.top/promoratio"
echo ""
echo "数据导入："
echo "  python3 import_promo_data.py"
echo ""
echo "查看日志："
echo "  tail -f logs/rating_app.log"
echo ""
