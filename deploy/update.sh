#!/bin/bash

# 审核结果展示系统 - 更新脚本
# 用于从 GitHub 拉取最新代码并重启服务

set -e  # 遇到错误立即退出

echo "=========================================="
echo "审核结果展示系统 - 更新"
echo "=========================================="

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 root 权限运行此脚本"
    echo "使用: sudo bash update.sh"
    exit 1
fi

# 配置变量
PROJECT_DIR="/opt/review-result-viewer"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="review-viewer"

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误: 项目目录不存在: $PROJECT_DIR"
    echo "请先运行 install.sh 进行首次安装"
    exit 1
fi

cd "$PROJECT_DIR"

echo ""
echo "步骤 1/5: 停止服务..."
systemctl stop $SERVICE_NAME
echo "服务已停止"

echo ""
echo "步骤 2/5: 备份当前版本..."
BACKUP_DIR="/opt/review-viewer-backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

tar -czf "$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='viewer/uploads/*' \
    "$PROJECT_DIR"

echo "备份已创建: $BACKUP_FILE"

echo ""
echo "步骤 3/5: 拉取最新代码..."
git fetch origin
git reset --hard origin/main  # 或者使用 origin/master，根据你的分支名

echo ""
echo "步骤 4/5: 更新依赖..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# 检查是否需要数据库迁移
if [ -f "$PROJECT_DIR/migrations/migrate.py" ]; then
    echo ""
    echo "执行数据库迁移..."
    python3 "$PROJECT_DIR/migrations/migrate.py"
fi

echo ""
echo "步骤 5/5: 重启服务..."
systemctl start $SERVICE_NAME

# 等待服务启动
sleep 3

# 检查服务状态
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "服务启动成功"
    systemctl status $SERVICE_NAME --no-pager
else
    echo "错误: 服务启动失败"
    echo "查看日志: journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

echo ""
echo "=========================================="
echo "更新完成！"
echo "=========================================="
echo ""
echo "备份文件: $BACKUP_FILE"
echo "服务状态: systemctl status $SERVICE_NAME"
echo "实时日志: journalctl -u $SERVICE_NAME -f"
echo ""
echo "如果更新出现问题，可以使用以下命令恢复:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo tar -xzf $BACKUP_FILE -C /"
echo "  sudo systemctl start $SERVICE_NAME"
echo "=========================================="
