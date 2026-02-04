#!/bin/bash

# 门店评级系统服务器端一键部署脚本
# Server-side One-Click Deployment Script

set -e  # 遇到错误立即退出

echo "=========================================="
echo "门店评级系统 - 服务器端部署"
echo "=========================================="

# 配置变量
PROJECT_DIR="/opt/review-result-viewer"
RATING_PORT=8000
SERVICE_NAME="rating"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用root用户运行此脚本"
    exit 1
fi

echo ""
echo "📁 项目目录: $PROJECT_DIR"
echo "🔌 服务端口: $RATING_PORT"
echo ""

# 进入项目目录
cd $PROJECT_DIR

echo "📦 安装Python依赖..."
pip3 install -r requirements.txt -q

echo ""
echo "📊 检查数据文件..."
if [ ! -f "rating_data/stores.json" ]; then
    echo "⚠️  警告: rating_data/stores.json 不存在"
    echo "   请先上传门店数据文件"
fi

# 创建必要的目录
echo ""
echo "📁 创建必要的目录..."
mkdir -p rating_data
mkdir -p logs
mkdir -p viewer/uploads

echo ""
echo "📝 创建systemd服务..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Store Rating System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:$RATING_PORT rating_app:app
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/rating_service.log
StandardError=append:$PROJECT_DIR/logs/rating_service_error.log

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
echo "🚀 启动服务..."
systemctl restart $SERVICE_NAME

echo ""
echo "⏳ 等待服务启动..."
sleep 3

echo ""
echo "📊 检查服务状态..."
systemctl status $SERVICE_NAME --no-pager || true

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "服务信息："
echo "  - 服务名称: $SERVICE_NAME"
echo "  - 监听端口: 127.0.0.1:$RATING_PORT"
echo "  - 项目目录: $PROJECT_DIR"
echo ""
echo "常用命令："
echo "  启动服务: systemctl start $SERVICE_NAME"
echo "  停止服务: systemctl stop $SERVICE_NAME"
echo "  重启服务: systemctl restart $SERVICE_NAME"
echo "  查看状态: systemctl status $SERVICE_NAME"
echo "  查看日志: tail -f $PROJECT_DIR/logs/rating_service.log"
echo ""
echo "下一步："
echo "  1. 配置Nginx（参考下面的配置）"
echo "  2. 重启Nginx: nginx -t && systemctl reload nginx"
echo "  3. 访问: http://blitzepanda.top/rating"
echo ""
echo "=========================================="
echo "Nginx配置示例"
echo "=========================================="
echo ""
cat << 'NGINXCONF'
# 在现有的Nginx配置中添加以下location块

# 门店评级系统
location /rating {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/rating {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# 静态文件（可选，提高性能）
location /static {
    alias /opt/review-result-viewer/viewer/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
NGINXCONF
echo ""
echo "=========================================="
