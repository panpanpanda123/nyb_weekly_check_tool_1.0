"""
审核结果展示系统 Flask 应用 (重构版)
Review Result Viewer Flask Application (Refactored)
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, render_template
from sqlalchemy.orm import Session
from shared.database_models import (
    create_db_engine, 
    create_session_factory, 
    init_viewer_db
)

# 导入API模块
from viewer.api_review import register_review_routes
from viewer.api_rating import register_rating_routes
from viewer.api_equipment import register_equipment_routes
from viewer.api_promo import register_promo_routes
from viewer.api_upload import register_upload_routes

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['JSON_AS_ASCII'] = False  # 支持中文
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'viewer-secret-key-change-in-production')

# 上传文件夹配置
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

# 创建数据库引擎和会话工厂
engine = create_db_engine(DATABASE_URL, echo=False)
SessionFactory = create_session_factory(engine)

# 初始化数据库表
init_viewer_db(engine)


def get_db_session() -> Session:
    """获取数据库会话"""
    return SessionFactory()


@app.after_request
def add_no_cache_headers(response):
    """为所有响应添加禁用缓存的响应头"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers.pop('ETag', None)
    return response


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """展示系统首页"""
    return render_template('viewer.html')


@app.route('/rating')
def rating():
    """门店评级页面"""
    return render_template('rating.html')


@app.route('/equipment')
def equipment():
    """设备异常监控页面"""
    return render_template('equipment.html')


@app.route('/promoratio')
def promo_ratio():
    """活动参与度页面"""
    return render_template('promoratio.html')


@app.route('/admin/upload')
def admin_upload():
    """数据管理页面"""
    return render_template('admin.html')


# ==================== 注册API路由 ====================

# 注册周清审核API
register_review_routes(app, get_db_session)

# 注册门店评级API
register_rating_routes(app, get_db_session)

# 注册设备异常监控API
register_equipment_routes(app, get_db_session)

# 注册活动参与度API
register_promo_routes(app, get_db_session)

# 注册文件上传API
register_upload_routes(app, get_db_session)


@app.teardown_appcontext
def shutdown_session(exception=None):
    """请求结束时清理会话"""
    SessionFactory.remove()


if __name__ == '__main__':
    # 开发环境运行
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
