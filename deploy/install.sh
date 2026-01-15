#!/bin/bash

# 审核结果展示系统 - 首次安装脚本
# 适用于 Ubuntu 22.04 LTS

set -e  # 遇到错误立即退出

echo "=========================================="
echo "审核结果展示系统 - 首次安装"
echo "=========================================="

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 root 权限运行此脚本"
    echo "使用: sudo bash install.sh"
    exit 1
fi

# 配置变量
PROJECT_DIR="/opt/review-result-viewer"
VENV_DIR="$PROJECT_DIR/venv"
DB_NAME="review_viewer_db"
DB_USER="review_viewer"
DB_PASSWORD=$(openssl rand -base64 32)
NGINX_CONF="/etc/nginx/sites-available/review-viewer"
SYSTEMD_SERVICE="/etc/systemd/system/review-viewer.service"
APP_USER="www-data"

echo ""
echo "步骤 1/10: 更新系统包..."
apt-get update
apt-get upgrade -y

echo ""
echo "步骤 2/10: 安装系统依赖..."
apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    openssl

echo ""
echo "步骤 3/10: 配置 PostgreSQL 数据库..."
# 启动 PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# 创建数据库用户和数据库
sudo -u postgres psql <<EOF
-- 删除已存在的数据库和用户（如果存在）
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- 创建新用户和数据库
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "数据库创建成功: $DB_NAME"
echo "数据库用户: $DB_USER"
echo "数据库密码: $DB_PASSWORD"

# 保存数据库凭据
echo "DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME" > /root/.review_viewer_db_credentials
chmod 600 /root/.review_viewer_db_credentials
echo "数据库凭据已保存到: /root/.review_viewer_db_credentials"

echo ""
echo "步骤 4/10: 克隆代码仓库..."
if [ -d "$PROJECT_DIR" ]; then
    echo "项目目录已存在，跳过克隆"
else
    echo "请输入 GitHub 仓库 URL:"
    read REPO_URL
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

echo ""
echo "步骤 5/10: 创建虚拟环境..."
python3.10 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo ""
echo "步骤 6/10: 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo ""
echo "步骤 7/10: 配置环境变量..."
cat > "$PROJECT_DIR/.env" <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
UPLOAD_FOLDER=$PROJECT_DIR/viewer/uploads
MAX_CONTENT_LENGTH=52428800
EOF

chmod 600 "$PROJECT_DIR/.env"
chown $APP_USER:$APP_USER "$PROJECT_DIR/.env"

echo ""
echo "步骤 8/10: 初始化数据库表..."
source "$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
python3 -c "
from shared.database_models import create_db_engine, init_viewer_db
import os
engine = create_db_engine(os.getenv('DATABASE_URL'))
init_viewer_db(engine)
print('数据库表创建成功')
"

echo ""
echo "步骤 9/10: 配置 Nginx..."
cp "$PROJECT_DIR/deploy/nginx.conf" "$NGINX_CONF"

# 替换配置文件中的占位符
sed -i "s|/path/to/project|$PROJECT_DIR|g" "$NGINX_CONF"

# 启用站点
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/review-viewer

# 测试 Nginx 配置
nginx -t

# 重启 Nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo "步骤 10/10: 配置 Systemd 服务..."
cp "$PROJECT_DIR/deploy/review-viewer.service" "$SYSTEMD_SERVICE"

# 替换配置文件中的占位符
sed -i "s|/path/to/project|$PROJECT_DIR|g" "$SYSTEMD_SERVICE"
sed -i "s|/path/to/venv|$VENV_DIR|g" "$SYSTEMD_SERVICE"

# 重新加载 systemd
systemctl daemon-reload

# 启动服务
systemctl start review-viewer
systemctl enable review-viewer

# 检查服务状态
sleep 2
systemctl status review-viewer --no-pager

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "数据库信息:"
echo "  数据库名: $DB_NAME"
echo "  用户名: $DB_USER"
echo "  密码: $DB_PASSWORD"
echo "  凭据文件: /root/.review_viewer_db_credentials"
echo ""
echo "服务信息:"
echo "  项目目录: $PROJECT_DIR"
echo "  虚拟环境: $VENV_DIR"
echo "  服务状态: systemctl status review-viewer"
echo "  服务日志: journalctl -u review-viewer -f"
echo ""
echo "访问地址:"
echo "  http://your-server-ip"
echo ""
echo "管理命令:"
echo "  启动服务: systemctl start review-viewer"
echo "  停止服务: systemctl stop review-viewer"
echo "  重启服务: systemctl restart review-viewer"
echo "  查看日志: journalctl -u review-viewer -f"
echo ""
echo "下次更新请使用: bash $PROJECT_DIR/deploy/update.sh"
echo "=========================================="
