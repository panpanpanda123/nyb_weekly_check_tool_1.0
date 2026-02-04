"""
审核结果展示系统 Flask 应用
Review Result Viewer Flask Application
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径（解决模块导入问题）
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, render_template, request, jsonify
from sqlalchemy.orm import Session
from shared.database_models import (
    create_db_engine, 
    create_session_factory, 
    init_viewer_db,
    StoreWhitelist,
    ViewerReviewResult,
    StoreRating,
    StoreOperationData
)
from viewer.data_importer import DataImporter
from werkzeug.utils import secure_filename

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

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

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


def allowed_file(filename: str, allowed_exts: set) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


def get_db_session() -> Session:
    """获取数据库会话"""
    return SessionFactory()


@app.route('/')
def index():
    """展示系统首页"""
    return render_template('viewer.html')


@app.route('/rating')
def rating():
    """门店评级页面"""
    return render_template('rating.html')


@app.route('/admin/upload')
def admin_upload():
    """数据管理页面"""
    return render_template('admin.html')


@app.route('/api/filters')
def get_filters():
    """
    获取所有筛选选项
    返回战区、省份、城市、门店标签、是否合格的选项列表
    Requirements: 1.1
    """
    try:
        session = get_db_session()
        
        # 获取战区列表（从白名单）
        war_zones = session.query(StoreWhitelist.war_zone)\
            .filter(StoreWhitelist.war_zone.isnot(None))\
            .filter(StoreWhitelist.war_zone != '')\
            .distinct()\
            .order_by(StoreWhitelist.war_zone)\
            .all()
        war_zones = [wz[0] for wz in war_zones]
        
        # 获取省份列表（从白名单）
        provinces = session.query(StoreWhitelist.province)\
            .filter(StoreWhitelist.province.isnot(None))\
            .filter(StoreWhitelist.province != '')\
            .distinct()\
            .order_by(StoreWhitelist.province)\
            .all()
        provinces = [p[0] for p in provinces]
        
        # 获取城市列表（从白名单）
        cities = session.query(StoreWhitelist.city)\
            .filter(StoreWhitelist.city.isnot(None))\
            .filter(StoreWhitelist.city != '')\
            .distinct()\
            .order_by(StoreWhitelist.city)\
            .all()
        cities = [c[0] for c in cities]
        
        # 获取运营列表（优先临时运营，其次省市运营）
        from sqlalchemy import func
        operators_query = session.query(
            func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator).label('operator')
        ).filter(
            func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator).isnot(None)
        ).filter(
            func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator) != ''
        ).distinct().order_by('operator')
        
        operators = [op[0] for op in operators_query.all()]
        
        # 审核结果选项（固定值）
        review_results = ['合格', '不合格']
        
        return jsonify({
            'success': True,
            'data': {
                'war_zones': war_zones,
                'provinces': provinces,
                'cities': cities,
                'operators': operators,
                'review_results': review_results
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取筛选选项失败: {str(e)}'
        }), 500


@app.route('/api/filters/provinces')
def get_provinces_by_war_zone():
    """
    根据战区获取省份列表
    Requirements: 1.2
    """
    try:
        war_zone = request.args.get('war_zone', '')
        
        if not war_zone:
            return jsonify({
                'success': False,
                'error': '缺少战区参数'
            }), 400
        
        session = get_db_session()
        
        # 根据战区查询省份
        provinces = session.query(StoreWhitelist.province)\
            .filter(StoreWhitelist.war_zone == war_zone)\
            .filter(StoreWhitelist.province.isnot(None))\
            .filter(StoreWhitelist.province != '')\
            .distinct()\
            .order_by(StoreWhitelist.province)\
            .all()
        provinces = [p[0] for p in provinces]
        
        return jsonify({
            'success': True,
            'data': {
                'provinces': provinces
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取省份列表失败: {str(e)}'
        }), 500


@app.route('/api/filters/cities')
def get_cities_by_province():
    """
    根据省份获取城市列表
    Requirements: 1.3
    """
    try:
        province = request.args.get('province', '')
        
        if not province:
            return jsonify({
                'success': False,
                'error': '缺少省份参数'
            }), 400
        
        session = get_db_session()
        
        # 根据省份查询城市
        cities = session.query(StoreWhitelist.city)\
            .filter(StoreWhitelist.province == province)\
            .filter(StoreWhitelist.city.isnot(None))\
            .filter(StoreWhitelist.city != '')\
            .distinct()\
            .order_by(StoreWhitelist.city)\
            .all()
        cities = [c[0] for c in cities]
        
        return jsonify({
            'success': True,
            'data': {
                'cities': cities
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取城市列表失败: {str(e)}'
        }), 500


@app.route('/api/search')
def search_reviews():
    """
    根据筛选条件搜索审核结果
    支持多条件组合查询
    支持门店编号精确搜索和门店名称模糊搜索
    支持分页加载（每次最多返回100条，按门店分组）
    Requirements: 1.4, 1.5
    """
    try:
        session = get_db_session()
        
        # 获取筛选参数
        war_zone = request.args.get('war_zone', '').strip()
        province = request.args.get('province', '').strip()
        city = request.args.get('city', '').strip()
        operator = request.args.get('operator', '').strip()
        review_result = request.args.get('review_result', '').strip()
        
        # 获取门店搜索参数
        store_search = request.args.get('store_search', '').strip()
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 9))  # 每页9条记录
        
        # 构建查询
        query = session.query(ViewerReviewResult)
        
        # 门店搜索：精确匹配门店编号或模糊匹配门店名称
        if store_search:
            query = query.filter(
                (ViewerReviewResult.store_id == store_search) |
                (ViewerReviewResult.store_name.like(f'%{store_search}%'))
            )
        
        # 应用筛选条件
        if war_zone:
            query = query.filter(ViewerReviewResult.war_zone == war_zone)
        
        if province:
            query = query.filter(ViewerReviewResult.province == province)
        
        if city:
            query = query.filter(ViewerReviewResult.city == city)
        
        if review_result:
            query = query.filter(ViewerReviewResult.review_result == review_result)
        
        # 如果有运营筛选，需要关联白名单表（优先临时运营，其次省市运营）
        if operator:
            from sqlalchemy import func
            query = query.join(
                StoreWhitelist,
                ViewerReviewResult.store_id == StoreWhitelist.store_id
            ).filter(
                func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator) == operator
            )
        
        # 获取总数
        total_count = query.count()
        
        # 执行查询并排序，应用分页
        results = query.order_by(
            ViewerReviewResult.store_id,  # 先按门店分组
            ViewerReviewResult.review_time.desc().nullslast(),
            ViewerReviewResult.id.desc()
        ).limit(per_page).offset((page - 1) * per_page).all()
        
        # 转换为字典列表
        results_data = [result.to_dict() for result in results]
        
        # 计算总页数
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'data': {
                'results': results_data,
                'count': len(results_data),
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_more': page < total_pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'搜索失败: {str(e)}'
        }), 500


@app.route('/api/upload/whitelist', methods=['POST'])
def upload_whitelist():
    """
    上传白名单Excel文件
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            }), 400
        
        # 检查文件扩展名
        if not allowed_file(file.filename, {'xlsx'}):
            return jsonify({
                'success': False,
                'error': '只支持.xlsx格式的Excel文件'
            }), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 导入数据
            session = get_db_session()
            importer = DataImporter(session)
            result = importer.import_whitelist(filepath)
            
            # 删除临时文件
            os.remove(filepath)
            
            if result.success:
                return jsonify({
                    'success': True,
                    'message': f'白名单导入成功，共导入 {result.records_count} 条记录',
                    'records_count': result.records_count
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.error_message
                }), 400
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}'
        }), 500


@app.route('/api/upload/reviews', methods=['POST'])
def upload_reviews():
    """
    上传审核结果CSV文件
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            }), 400
        
        # 检查文件扩展名
        if not allowed_file(file.filename, {'csv'}):
            return jsonify({
                'success': False,
                'error': '只支持.csv格式的文件'
            }), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 导入数据
            session = get_db_session()
            importer = DataImporter(session)
            result = importer.import_reviews(filepath)
            
            # 删除临时文件
            os.remove(filepath)
            
            if result.success:
                message = f'审核结果导入成功，共导入 {result.records_count} 条记录'
                if result.unmatched_stores_count > 0:
                    message += f'，其中 {result.unmatched_stores_count} 个门店在白名单中未找到（已标记为"[未匹配]"）'
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'records_count': result.records_count,
                    'unmatched_stores_count': result.unmatched_stores_count
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.error_message
                }), 400
                
        except Exception as e:
            # 清理临时文件
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}'
        }), 500


@app.route('/api/unmatched-stores')
def get_unmatched_stores():
    """
    获取所有未匹配的门店列表
    返回战区/省份/城市标记为"[未匹配]"的审核结果
    """
    try:
        session = get_db_session()
        
        # 查询所有包含"[未匹配]"标记的审核结果
        unmatched_results = session.query(ViewerReviewResult)\
            .filter(
                (ViewerReviewResult.war_zone == "[未匹配]") |
                (ViewerReviewResult.province == "[未匹配]") |
                (ViewerReviewResult.city == "[未匹配]")
            )\
            .order_by(ViewerReviewResult.store_id, ViewerReviewResult.id)\
            .all()
        
        # 按门店ID分组统计
        stores_dict = {}
        for result in unmatched_results:
            if result.store_id not in stores_dict:
                stores_dict[result.store_id] = {
                    'store_id': result.store_id,
                    'store_name': result.store_name,
                    'war_zone': result.war_zone,
                    'province': result.province,
                    'city': result.city,
                    'items_count': 0,
                    'items': []
                }
            
            stores_dict[result.store_id]['items_count'] += 1
            stores_dict[result.store_id]['items'].append({
                'item_name': result.item_name,
                'review_result': result.review_result,
                'review_time': result.review_time.strftime('%Y-%m-%d %H:%M:%S') if result.review_time else ''
            })
        
        stores_list = list(stores_dict.values())
        
        return jsonify({
            'success': True,
            'data': {
                'stores': stores_list,
                'total_stores': len(stores_list),
                'total_items': len(unmatched_results)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取未匹配门店失败: {str(e)}'
        }), 500


# ==================== 门店评级 API ====================

@app.route('/api/rating/war-zones')
def get_rating_war_zones():
    """
    获取战区列表（用于评级功能）
    """
    try:
        session = get_db_session()
        
        # 从白名单获取战区列表
        war_zones = session.query(StoreWhitelist.war_zone)\
            .filter(StoreWhitelist.war_zone.isnot(None))\
            .filter(StoreWhitelist.war_zone != '')\
            .distinct()\
            .order_by(StoreWhitelist.war_zone)\
            .all()
        war_zones = [wz[0] for wz in war_zones]
        
        return jsonify({
            'success': True,
            'data': {
                'war_zones': war_zones
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取战区列表失败: {str(e)}'
        }), 500


@app.route('/api/rating/regional-managers')
def get_regional_managers():
    """
    获取区域经理列表（用于评级功能）
    可选参数：war_zone - 根据战区筛选
    """
    try:
        session = get_db_session()
        war_zone = request.args.get('war_zone', '').strip()
        
        # 从白名单的"区域经理"字段获取
        query = session.query(StoreWhitelist.regional_manager)\
            .filter(StoreWhitelist.regional_manager.isnot(None))\
            .filter(StoreWhitelist.regional_manager != '')
        
        # 如果指定了战区，添加战区筛选
        if war_zone:
            query = query.filter(StoreWhitelist.war_zone == war_zone)
        
        managers = query.distinct().order_by(StoreWhitelist.regional_manager).all()
        managers = [m[0] for m in managers]
        
        return jsonify({
            'success': True,
            'data': {
                'regional_managers': managers
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取区域经理列表失败: {str(e)}'
        }), 500


@app.route('/api/rating/stores')
def get_rating_stores():
    """
    获取门店列表（用于评级功能）
    支持筛选和分页
    参数：
    - war_zone: 战区
    - regional_manager: 区域经理
    - page: 页码（默认1）
    - per_page: 每页数量（默认5）
    """
    try:
        session = get_db_session()
        
        # 获取筛选参数
        war_zone = request.args.get('war_zone', '').strip()
        regional_manager = request.args.get('regional_manager', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))
        
        # 构建查询
        query = session.query(StoreWhitelist)
        
        # 应用筛选条件
        if war_zone:
            query = query.filter(StoreWhitelist.war_zone == war_zone)
        
        if regional_manager:
            query = query.filter(StoreWhitelist.regional_manager == regional_manager)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        stores = query.order_by(StoreWhitelist.store_id)\
            .limit(per_page)\
            .offset((page - 1) * per_page)\
            .all()
        
        # 获取每个门店的运营数据和当前评级
        stores_data = []
        for store in stores:
            # 获取运营数据
            operation_data = session.query(StoreOperationData)\
                .filter(StoreOperationData.store_id == store.store_id)\
                .first()
            
            # 获取最新评级
            latest_rating = session.query(StoreRating)\
                .filter(StoreRating.store_id == store.store_id)\
                .order_by(StoreRating.rated_at.desc())\
                .first()
            
            store_dict = {
                'store_id': store.store_id,
                'store_name': store.store_name,
                'city': store.city,
                'war_zone': store.war_zone,
                'regional_manager': store.regional_manager,
                'dine_in_revenue': operation_data.dine_in_revenue if operation_data else None,
                'comprehensive_score': operation_data.comprehensive_score if operation_data else None,
                'operation_score': operation_data.operation_score if operation_data else None,
                'current_rating': latest_rating.rating if latest_rating else None
            }
            stores_data.append(store_dict)
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'data': {
                'stores': stores_data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取门店列表失败: {str(e)}'
        }), 500


@app.route('/api/rating/submit', methods=['POST'])
def submit_rating():
    """
    提交门店评级
    请求体：
    {
        "store_id": "门店ID",
        "rating": "A/B/C"
    }
    """
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data or 'store_id' not in data or 'rating' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需字段：store_id 或 rating'
            }), 400
        
        store_id = data['store_id']
        rating = data['rating']
        
        # 验证评级值
        if rating not in ['A', 'B', 'C']:
            return jsonify({
                'success': False,
                'error': '无效的评级值，只允许 A、B、C'
            }), 400
        
        # 验证门店是否存在
        session = get_db_session()
        store = session.query(StoreWhitelist)\
            .filter(StoreWhitelist.store_id == store_id)\
            .first()
        
        if not store:
            return jsonify({
                'success': False,
                'error': '门店不存在'
            }), 404
        
        # 保存评级（插入新记录，保留历史）
        from datetime import datetime
        new_rating = StoreRating(
            store_id=store_id,
            rating=rating,
            rated_at=datetime.now(),
            rated_by=None  # TODO: 如果需要登录功能，可以记录评级人
        )
        session.add(new_rating)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': '评级已保存'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': f'保存评级失败: {str(e)}'
        }), 500


@app.route('/api/rating/completion-stats')
def get_completion_stats():
    """
    获取评级完成率统计
    参数：
    - war_zone: 战区（可选）
    - regional_manager: 区域经理（可选）
    """
    try:
        session = get_db_session()
        
        # 获取筛选参数
        war_zone = request.args.get('war_zone', '').strip()
        regional_manager = request.args.get('regional_manager', '').strip()
        
        # 构建门店查询
        store_query = session.query(StoreWhitelist)
        
        if war_zone:
            store_query = store_query.filter(StoreWhitelist.war_zone == war_zone)
        
        if regional_manager:
            store_query = store_query.filter(StoreWhitelist.regional_manager == regional_manager)
        
        # 按战区分组统计
        from sqlalchemy import func
        
        # 获取所有门店（按战区分组）
        stores_by_zone = {}
        for store in store_query.all():
            zone = store.war_zone or '未知战区'
            if zone not in stores_by_zone:
                stores_by_zone[zone] = []
            stores_by_zone[zone].append(store.store_id)
        
        # 统计每个战区的完成情况
        stats = []
        for zone, store_ids in stores_by_zone.items():
            total_stores = len(store_ids)
            
            # 统计已评级的门店数
            rated_stores = session.query(func.count(func.distinct(StoreRating.store_id)))\
                .filter(StoreRating.store_id.in_(store_ids))\
                .scalar()
            
            completion_rate = (rated_stores / total_stores * 100) if total_stores > 0 else 0
            
            stats.append({
                'war_zone': zone,
                'total_stores': total_stores,
                'rated_stores': rated_stores,
                'completion_rate': round(completion_rate, 1)
            })
        
        # 按战区名称排序
        stats.sort(key=lambda x: x['war_zone'])
        
        return jsonify({
            'success': True,
            'data': {
                'stats': stats
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取统计信息失败: {str(e)}'
        }), 500


@app.route('/api/rating/export')
def export_ratings():
    """
    导出评级结果为CSV文件
    """
    try:
        session = get_db_session()
        
        # 查询所有已评级的门店（获取最新评级）
        from sqlalchemy import func
        
        # 子查询：获取每个门店的最新评级时间
        subquery = session.query(
            StoreRating.store_id,
            func.max(StoreRating.rated_at).label('max_rated_at')
        ).group_by(StoreRating.store_id).subquery()
        
        # 主查询：获取最新评级记录
        ratings = session.query(StoreRating)\
            .join(
                subquery,
                (StoreRating.store_id == subquery.c.store_id) &
                (StoreRating.rated_at == subquery.c.max_rated_at)
            )\
            .order_by(StoreRating.store_id)\
            .all()
        
        if not ratings:
            return jsonify({
                'success': False,
                'error': '暂无评级数据可导出'
            }), 400
        
        # 生成CSV内容
        import io
        import csv
        from urllib.parse import quote
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['门店ID', '门店名称', '城市', '战区', '区域经理', '评级', '评级时间'])
        
        # 写入数据行
        for rating in ratings:
            # 获取门店信息
            store = session.query(StoreWhitelist)\
                .filter(StoreWhitelist.store_id == rating.store_id)\
                .first()
            
            if store:
                writer.writerow([
                    rating.store_id,
                    store.store_name or '',
                    store.city or '',
                    store.war_zone or '',
                    store.regional_manager or '',
                    rating.rating,
                    rating.rated_at.strftime('%Y-%m-%d %H:%M:%S') if rating.rated_at else ''
                ])
        
        # 生成文件名
        from datetime import datetime
        filename = f'门店评级结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filename_encoded = quote(filename)
        
        # 创建响应
        from flask import Response
        response = Response(
            '\ufeff' + output.getvalue(),  # UTF-8-BOM
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{filename_encoded}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'导出失败: {str(e)}'
        }), 500


@app.teardown_appcontext
def shutdown_session(exception=None):
    """请求结束时清理会话"""
    SessionFactory.remove()


if __name__ == '__main__':
    # 开发环境运行
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
