"""
门店评级系统 - 独立应用
Store Rating System - Standalone Application
"""
from flask import Flask, render_template, jsonify, request, Response, send_from_directory
import json
import os
from datetime import datetime
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, 
            template_folder='viewer/templates',
            static_folder='viewer/static')

# 配置
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# 数据文件路径
DATA_DIR = Path('rating_data')
DATA_DIR.mkdir(exist_ok=True)

STORES_FILE = DATA_DIR / 'stores.json'
RATINGS_FILE = DATA_DIR / 'ratings.json'

# 配置日志
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

file_handler = RotatingFileHandler(
    LOG_DIR / 'rating_app.log',
    maxBytes=10240000,
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)


def load_stores():
    """加载门店数据"""
    if STORES_FILE.exists():
        with open(STORES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_stores(stores):
    """保存门店数据"""
    with open(STORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(stores, f, ensure_ascii=False, indent=2)


def load_ratings():
    """加载评级数据"""
    if RATINGS_FILE.exists():
        with open(RATINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_ratings(ratings):
    """保存评级数据"""
    with open(RATINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)


@app.route('/')
@app.route('/rating')
def rating():
    """门店评级页面"""
    return render_template('rating.html')


@app.route('/api/rating/war-zones')
def get_rating_war_zones():
    """获取战区列表"""
    try:
        stores = load_stores()
        war_zones = sorted(list(set(
            store.get('war_zone', '') 
            for store in stores 
            if store.get('war_zone')
        )))
        
        return jsonify({
            'success': True,
            'data': {'war_zones': war_zones}
        })
    except Exception as e:
        app.logger.error(f'获取战区列表失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rating/regional-managers')
def get_regional_managers():
    """获取区域经理列表"""
    try:
        stores = load_stores()
        war_zone = request.args.get('war_zone', '')
        
        # 筛选门店
        filtered_stores = stores
        if war_zone:
            filtered_stores = [s for s in stores if s.get('war_zone') == war_zone]
        
        # 获取区域经理列表
        managers = sorted(list(set(
            store.get('regional_manager', '') 
            for store in filtered_stores 
            if store.get('regional_manager')
        )))
        
        return jsonify({
            'success': True,
            'data': {'regional_managers': managers}
        })
    except Exception as e:
        app.logger.error(f'获取区域经理列表失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rating/stores')
def get_rating_stores():
    """获取门店列表（支持筛选和分页）"""
    try:
        stores = load_stores()
        ratings = load_ratings()
        
        # 获取筛选参数
        war_zone = request.args.get('war_zone', '')
        regional_manager = request.args.get('regional_manager', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))
        
        # 筛选门店
        filtered_stores = stores
        if war_zone:
            filtered_stores = [s for s in filtered_stores if s.get('war_zone') == war_zone]
        if regional_manager:
            filtered_stores = [s for s in filtered_stores if s.get('regional_manager') == regional_manager]
        
        # 分页
        total = len(filtered_stores)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        
        page_stores = filtered_stores[start:end]
        
        # 添加当前评级
        for store in page_stores:
            store_id = store.get('store_id')
            rating_data = ratings.get(store_id, {})
            # 如果rating_data是字典，取出rating字段；否则直接使用
            if isinstance(rating_data, dict):
                store['current_rating'] = rating_data.get('rating', '')
            else:
                store['current_rating'] = rating_data if rating_data else ''
        
        return jsonify({
            'success': True,
            'data': {
                'stores': page_stores,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            }
        })
    except Exception as e:
        app.logger.error(f'获取门店列表失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rating/submit', methods=['POST'])
def submit_rating():
    """提交评级"""
    try:
        data = request.get_json()
        store_id = data.get('store_id')
        rating = data.get('rating')
        
        if not store_id or not rating:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        if rating not in ['A', 'B', 'C']:
            return jsonify({
                'success': False,
                'error': '无效的评级'
            }), 400
        
        # 加载评级数据
        ratings = load_ratings()
        
        # 保存评级
        ratings[store_id] = {
            'rating': rating,
            'updated_at': datetime.now().isoformat()
        }
        
        save_ratings(ratings)
        
        app.logger.info(f'门店 {store_id} 评级为 {rating}')
        
        return jsonify({
            'success': True,
            'data': {'rating': rating}
        })
    except Exception as e:
        app.logger.error(f'提交评级失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rating/completion-stats')
def get_completion_stats():
    """获取完成率统计"""
    try:
        stores = load_stores()
        ratings = load_ratings()
        
        # 获取筛选参数
        war_zone = request.args.get('war_zone', '')
        regional_manager = request.args.get('regional_manager', '')
        
        # 筛选门店
        filtered_stores = stores
        if war_zone:
            filtered_stores = [s for s in filtered_stores if s.get('war_zone') == war_zone]
        if regional_manager:
            filtered_stores = [s for s in filtered_stores if s.get('regional_manager') == regional_manager]
        
        # 按战区统计
        war_zones = sorted(list(set(s.get('war_zone', '') for s in filtered_stores if s.get('war_zone'))))
        
        stats = []
        for wz in war_zones:
            zone_stores = [s for s in filtered_stores if s.get('war_zone') == wz]
            total = len(zone_stores)
            rated = sum(1 for s in zone_stores if s.get('store_id') in ratings)
            completion_rate = round((rated / total * 100) if total > 0 else 0, 1)
            
            stats.append({
                'war_zone': wz,
                'total_stores': total,
                'rated_stores': rated,
                'completion_rate': completion_rate
            })
        
        return jsonify({
            'success': True,
            'data': {'stats': stats}
        })
    except Exception as e:
        app.logger.error(f'获取完成率统计失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rating/export')
def export_ratings():
    """导出评级结果为CSV"""
    try:
        stores = load_stores()
        ratings = load_ratings()
        
        # 生成CSV内容
        csv_lines = ['门店ID,门店名称,城市,战区,区域经理,堂食营业额,评级,更新时间']
        
        for store in stores:
            store_id = store.get('store_id', '')
            rating_data = ratings.get(store_id, {})
            
            if rating_data:
                # 确保所有值都转换为字符串，处理None值
                line = ','.join([
                    str(store.get('store_id') or ''),
                    str(store.get('store_name') or ''),
                    str(store.get('city') or ''),
                    str(store.get('war_zone') or ''),
                    str(store.get('regional_manager') or ''),
                    str(store.get('dine_in_revenue') or ''),
                    str(rating_data.get('rating') or ''),
                    str(rating_data.get('updated_at') or '')
                ])
                csv_lines.append(line)
        
        csv_content = '\n'.join(csv_lines)
        
        # 生成文件名
        filename = f'门店评级_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        from urllib.parse import quote
        filename_encoded = quote(filename)
        
        response = Response(
            csv_content.encode('utf-8-sig'),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{filename_encoded}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response
    except Exception as e:
        app.logger.error(f'导出CSV失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("门店评级系统启动中...")
    print("本地访问地址: http://127.0.0.1:8001")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8001, debug=False)
