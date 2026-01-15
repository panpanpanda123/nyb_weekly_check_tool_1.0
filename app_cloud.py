"""
门店检查项图片审核系统 - 云服务器版本
Store Inspection Review System - Cloud Server Version
"""
from flask import Flask, render_template, jsonify, request, Response
import os
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
from data_loader import DataLoader
from review_manager_db import ReviewManager
from csv_exporter import CSVExporter
from database import init_db, load_whitelist_to_db, get_all_operators_from_db

# 导入配置
try:
    from config import (
        HOST, PORT, DEBUG, MAX_CONTENT_LENGTH, JSON_AS_ASCII,
        UPLOAD_FOLDER, EXCEL_FILE, WHITELIST_FILE, ADMIN_USERS,
        LOG_LEVEL, LOG_FILE
    )
except ImportError:
    # 如果没有config.py，使用默认配置
    HOST = '0.0.0.0'
    PORT = 5001
    DEBUG = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    JSON_AS_ASCII = False
    UPLOAD_FOLDER = '.'
    EXCEL_FILE = '检查项记录.xlsx'
    WHITELIST_FILE = 'data/whitelist.xlsx'
    ADMIN_USERS = ['窦']
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'

app = Flask(__name__)

# 配置
app.config['JSON_AS_ASCII'] = JSON_AS_ASCII
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 配置日志
if not DEBUG:
    # 确保日志目录存在
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, LOG_LEVEL))
    app.logger.info('门店检查项图片审核系统启动')

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx'}

# 全局数据存储
inspection_data = []
data_loader = None
review_manager = ReviewManager()
csv_exporter = CSVExporter()


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """返回主页面"""
    return render_template('index.html')


@app.route('/api/items', methods=['GET'])
def get_items():
    """获取所有检查项数据"""
    if not inspection_data:
        return jsonify([])
    
    operator = request.args.get('operator', '全部')
    
    if operator and operator != '全部' and data_loader:
        filtered_data = data_loader.filter_by_operator(operator)
        sorted_data = sorted(filtered_data, key=lambda x: int(x['门店编号']) if x['门店编号'].isdigit() else 0)
    else:
        sorted_data = sorted(inspection_data, key=lambda x: int(x['门店编号']) if x['门店编号'].isdigit() else 0)
    
    return jsonify(sorted_data)


@app.route('/api/operators', methods=['GET'])
def get_operators():
    """获取所有运营人员列表"""
    operators = get_all_operators_from_db()
    
    if not operators and data_loader:
        operators = data_loader.get_all_operators()
    
    return jsonify(operators)


@app.route('/api/review', methods=['POST'])
def submit_review():
    """提交审核结果"""
    try:
        data = request.get_json()
        
        if not data or 'item_id' not in data:
            return jsonify({'success': False, 'error': '缺少item_id'}), 400
        
        item_id = data['item_id']
        item_data = next((item for item in inspection_data if item['id'] == item_id), None)
        
        if not item_data:
            return jsonify({'success': False, 'error': '检查项不存在'}), 404
        
        review_data = {
            '门店名称': item_data['门店名称'],
            '门店编号': item_data['门店编号'],
            '所属区域': item_data['所属区域'],
            '检查项名称': item_data['检查项名称'],
            '标准图': item_data['标准图'],
            '审核结果': data.get('审核结果', ''),
            '问题描述': data.get('问题描述', '')
        }
        
        if review_manager.has_review(item_id):
            success = review_manager.update_review(item_id, review_data)
        else:
            success = review_manager.save_review(item_id, review_data)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500
            
    except Exception as e:
        app.logger.error(f'提交审核失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """获取所有审核结果"""
    reviews = review_manager.get_all_reviews()
    return jsonify(reviews)


@app.route('/api/review/problem', methods=['POST'])
def update_problem():
    """更新问题描述"""
    try:
        data = request.get_json()
        
        if not data or 'item_id' not in data:
            return jsonify({'success': False, 'error': '缺少item_id'}), 400
        
        item_id = data['item_id']
        problem_note = data.get('问题描述', '')
        
        review = review_manager.get_review(item_id)
        
        if review:
            review['问题描述'] = problem_note
            success = review_manager.update_review(item_id, review)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': '更新失败'}), 500
        else:
            return jsonify({'success': False, 'error': '审核记录不存在'}), 404
            
    except Exception as e:
        app.logger.error(f'更新问题描述失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['GET'])
def export_csv():
    """导出CSV文件"""
    try:
        reviews = review_manager.get_all_reviews()
        
        if not reviews:
            return jsonify({'error': '暂无审核结果可导出'}), 400
        
        csv_content = csv_exporter.export_reviews(reviews, inspection_data)
        
        from urllib.parse import quote
        filename = csv_exporter.generate_filename()
        filename_encoded = quote(filename)
        
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{filename_encoded}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response
        
    except Exception as e:
        app.logger.error(f'导出CSV失败: {e}')
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取审核统计信息（按门店统计）"""
    try:
        if not inspection_data:
            return jsonify({
                'total': 0,
                'reviewed': 0,
                'percentage': 0
            })
        
        operator = request.args.get('operator', '全部')
        
        if operator and operator != '全部' and data_loader:
            filtered_items = data_loader.filter_by_operator(operator)
        else:
            filtered_items = inspection_data
        
        stores = {}
        for item in filtered_items:
            store_id = item['门店编号']
            if store_id not in stores:
                stores[store_id] = {'items': []}
            stores[store_id]['items'].append(item)
        
        total_stores = len(stores)
        completed_stores = 0
        
        for store_id, store_data in stores.items():
            all_completed = True
            for item in store_data['items']:
                review = review_manager.get_review(item['id'])
                if not review:
                    all_completed = False
                    break
                
                if review.get('审核结果') == '不合格':
                    if not review.get('问题描述') or review.get('问题描述').strip() == '':
                        all_completed = False
                        break
            
            if all_completed:
                completed_stores += 1
        
        percentage = round((completed_stores / total_stores * 100) if total_stores > 0 else 0, 1)
        
        return jsonify({
            'total': total_stores,
            'reviewed': completed_stores,
            'percentage': percentage
        })
        
    except Exception as e:
        app.logger.error(f'获取统计信息失败: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    """管理员重置审核数据（开始新周期）"""
    try:
        data = request.get_json()
        operator = data.get('operator', '')
        
        if operator not in ADMIN_USERS:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        
        review_manager.clear_all_reviews()
        
        global inspection_data, data_loader
        
        data_loader = DataLoader(EXCEL_FILE, WHITELIST_FILE)
        inspection_data = data_loader.load_and_process()
        
        auto_review_no_result_items()
        
        app.logger.info(f'[管理员操作] {operator} 重置审核数据，重新加载 {len(inspection_data)} 条检查项')
        
        return jsonify({
            'success': True,
            'message': '已开始新周期',
            'total_items': len(inspection_data)
        })
        
    except Exception as e:
        app.logger.error(f'重置数据失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/upload', methods=['POST'])
def admin_upload():
    """管理员上传新的Excel文件（开始新周期）"""
    try:
        operator = request.form.get('operator', '')
        if operator not in ADMIN_USERS:
            return jsonify({'success': False, 'error': '权限不足'}), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '只支持.xlsx文件'}), 400
        
        target_path = os.path.join(app.config['UPLOAD_FOLDER'], EXCEL_FILE)
        file.save(target_path)
        
        app.logger.info(f'[管理员操作] {operator} 上传新文件: {file.filename}')
        
        review_manager.clear_all_reviews()
        
        global inspection_data, data_loader
        
        data_loader = DataLoader(target_path, WHITELIST_FILE)
        inspection_data = data_loader.load_and_process()
        
        auto_review_no_result_items()
        
        app.logger.info(f'[管理员操作] 已加载新数据，共 {len(inspection_data)} 条检查项')
        
        return jsonify({
            'success': True,
            'message': '文件上传成功，已开始新周期',
            'total_items': len(inspection_data)
        })
        
    except Exception as e:
        app.logger.error(f'上传文件失败: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


def get_local_ip():
    """获取本机局域网IP地址"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def auto_review_no_result_items():
    """自动为无现场结果的检查项标记为不合格"""
    count = 0
    for item in inspection_data:
        if item.get('无现场结果', False):
            item_id = item['id']
            if not review_manager.has_review(item_id):
                review_data = {
                    '门店名称': item['门店名称'],
                    '门店编号': item['门店编号'],
                    '所属区域': item['所属区域'],
                    '检查项名称': item['检查项名称'],
                    '标准图': item['标准图'],
                    '审核结果': '不合格',
                    '问题描述': '无现场结果'
                }
                review_manager.save_review(item_id, review_data)
                count += 1
    
    if count > 0:
        app.logger.info(f'[自动审核] 已自动标记 {count} 个无现场结果的检查项为不合格')
    
    return count


if __name__ == '__main__':
    # 初始化数据库
    print("正在初始化数据库...")
    try:
        init_db()
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        print("请确保PostgreSQL数据库正在运行，并且连接信息正确")
        exit(1)
    
    # 加载白名单到数据库
    if os.path.exists(WHITELIST_FILE):
        print("正在加载白名单到数据库...")
        load_whitelist_to_db(WHITELIST_FILE)
    else:
        print(f"提示: 未找到白名单文件 {WHITELIST_FILE}")
    
    # 加载Excel数据
    if os.path.exists(EXCEL_FILE):
        try:
            print("正在加载Excel数据...")
            data_loader = DataLoader(EXCEL_FILE, WHITELIST_FILE)
            inspection_data = data_loader.load_and_process()
            print(f"成功加载 {len(inspection_data)} 条检查项数据")
            
            auto_review_no_result_items()
            
            operators = data_loader.get_all_operators()
            if operators:
                print(f"运营人员列表: {', '.join(operators)}")
            
        except ValueError as e:
            print(f"数据验证错误: {e}")
            print("系统将以空数据启动，请通过管理员上传功能导入数据")
            inspection_data = []
        except Exception as e:
            print(f"加载数据时发生错误: {e}")
            print("系统将以空数据启动，请通过管理员上传功能导入数据")
            inspection_data = []
    else:
        print(f"提示: 未找到 {EXCEL_FILE} 文件")
        print("系统将以空数据启动，请通过管理员上传功能导入数据")
        inspection_data = []
    
    # 获取局域网IP地址
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("门店检查项图片审核系统启动中...")
    print(f"局域网访问地址: http://{local_ip}:{PORT}")
    print(f"本机访问地址: http://127.0.0.1:{PORT}")
    print(f"环境: {'开发' if DEBUG else '生产'}")
    print("=" * 60)
    
    # 启动Flask应用
    app.run(host=HOST, port=PORT, debug=DEBUG)
