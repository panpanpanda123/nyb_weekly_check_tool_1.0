"""
配置文件 - 云服务器部署配置
Configuration for Cloud Server Deployment
"""
import os
from pathlib import Path

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent

# 环境配置
ENV = os.getenv('FLASK_ENV', 'production')  # development, production
DEBUG = ENV == 'development'

# 服务器配置
HOST = os.getenv('HOST', '0.0.0.0')  # 监听所有网络接口
PORT = int(os.getenv('PORT', 5001))

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/configurable_ops'
)

# 文件路径配置
# 云服务器上使用相对路径或环境变量
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR))
EXCEL_FILE = os.getenv('EXCEL_FILE', '检查项记录.xlsx')
WHITELIST_FILE = os.getenv(
    'WHITELIST_FILE',
    str(BASE_DIR / 'data' / 'whitelist.xlsx')  # 使用项目内的data目录
)

# Flask配置
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
JSON_AS_ASCII = False  # 支持中文

# 安全配置
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'logs' / 'app.log'))

# CORS配置（如果需要跨域访问）
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# 管理员配置
ADMIN_USERS = os.getenv('ADMIN_USERS', '窦').split(',')

# 性能配置
SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', 10))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 20))

# 创建必要的目录
def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        BASE_DIR / 'logs',
        BASE_DIR / 'data',
        BASE_DIR / 'uploads',
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

ensure_directories()
