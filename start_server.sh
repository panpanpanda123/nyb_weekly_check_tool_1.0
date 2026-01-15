#!/bin/bash
# 启动脚本 - 用于云服务器

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}门店检查项图片审核系统${NC}"
echo -e "${GREEN}================================${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}未找到虚拟环境，正在创建...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}未找到.env文件，使用默认配置${NC}"
    echo -e "${YELLOW}建议复制.env.example为.env并修改配置${NC}"
fi

# 创建必要的目录
mkdir -p logs data uploads

# 检查PostgreSQL连接
echo -e "${YELLOW}检查数据库连接...${NC}"
python3 -c "from database import engine; engine.connect()" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库连接成功${NC}"
else
    echo -e "${RED}✗ 数据库连接失败${NC}"
    echo -e "${RED}请检查PostgreSQL是否运行，以及DATABASE_URL配置是否正确${NC}"
    exit 1
fi

# 初始化数据库
echo -e "${YELLOW}初始化数据库...${NC}"
python3 init_database.py

# 选择启动方式
echo ""
echo "请选择启动方式:"
echo "1) 开发模式 (Flask内置服务器)"
echo "2) 生产模式 (Gunicorn)"
read -p "请输入选项 [1-2]: " choice

case $choice in
    1)
        echo -e "${GREEN}启动开发模式...${NC}"
        export FLASK_ENV=development
        python3 app_cloud.py
        ;;
    2)
        echo -e "${GREEN}启动生产模式...${NC}"
        export FLASK_ENV=production
        gunicorn -c gunicorn_config.py app_cloud:app
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac
