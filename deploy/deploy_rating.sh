#!/bin/bash

# 门店评级系统部署脚本
# Store Rating System Deployment Script

echo "=========================================="
echo "门店评级系统部署脚本"
echo "=========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用root用户运行此脚本"
    exit 1
fi

# 设置变量
APP_DIR="/root/rating"
SERVICE_NAME="rating"
PORT=8000

echo ""
echo "📁 创建应用目录..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/viewer/templates
mkdir -p $APP_DIR/viewer/static
mkdir -p $APP_DIR/rating_data
mkdir -p $APP_DIR/logs

echo ""
echo "📦 检查Python依赖..."
pip3 install flask gunicorn -q

echo ""
echo "📝 创建systemd服务..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Store Rating System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:$PORT rating_app:app
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/service.log
StandardError=append:$APP_DIR/logs/service_error.log

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🔄 重新加载systemd..."
systemctl daemon-reload

echo ""
echo "✅ 启用服务..."
systemctl enable $SERVICE_NAME

echo ""
echo "=========================================="
echo "✅ 部署配置完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 上传以下文件到 $APP_DIR:"
echo "   - rating_app.py"
echo "   - rating_data/stores.json"
echo "   - viewer/templates/rating.html"
echo "   - viewer/static/rating.js"
echo "   - viewer/static/rating.css"
echo ""
echo "2. 启动服务:"
echo "   systemctl start $SERVICE_NAME"
echo ""
echo "3. 查看状态:"
echo "   systemctl status $SERVICE_NAME"
echo ""
echo "4. 配置Nginx（参考 rating_deploy_guide.md）"
echo ""
