"""
门店检查项图片审核系统
Store Inspection Review System
"""
from flask import Flask, render_template, jsonify, request, send_file, Response
import os
from io import BytesIO
from werkzeug.utils import secure_filename
from data_loader import DataLoader
from review_manager_db import ReviewManager
from csv_exporter import CSVExporter
from database import init_db, load_whitelist_to_db, get_all_operators_from_db, get_operator_by_store_id

app = Flask(__name__)

# 配置
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON响应
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大50MB
app.config['UPLOAD_FOLDER'] = '.'  # 上传到当前目录

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
    # 如果没有数据，返回空列表
    if not inspection_data:
        return jsonify([])
    
    # 获取筛选参数
    operator = request.args.get('operator', '全部')
    
    # 按门店编号排序
    if operator and operator != '全部' and data_loader:
        # 筛选指定运营人员的数据
        filtered_data = data_loader.filter_by_operator(operator)
        sorted_data = sorted(filtered_data, key=lambda x: int(x['门店编号']) if x['门店编号'].isdigit() else 0)
    else:
        # 返回所有数据
        sorted_data = sorted(inspection_data, key=lambda x: int(x['门店编号']) if x['门店编号'].isdigit() else 0)
    
    return jsonify(sorted_data)


@app.route('/api/operators', methods=['GET'])
def get_operators():
    """获取所有运营人员列表"""
    # 优先从数据库获取，如果数据库为空则从data_loader获取
    operators = get_all_operators_from_db()
    
    if not operators and data_loader:
        operators = data_loader.get_all_operators()
    
    return jsonify(operators)


@app.route('/api/review', methods=['POST'])
def submit_review():
    """提交审核结果"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data or 'item_id' not in data:
            return jsonify({'success': False, 'error': '缺少item_id'}), 400
        
        item_id = data['item_id']
        
        # 查找对应的检查项数据
        item_data = next((item for item in inspection_data if item['id'] == item_id), None)
        
        if not item_data:
            return jsonify({'success': False, 'error': '检查项不存在'}), 404
        
        # 构建审核数据
        review_data = {
            '门店名称': item_data['门店名称'],
            '门店编号': item_data['门店编号'],
            '所属区域': item_data['所属区域'],
            '检查项名称': item_data['检查项名称'],
            '标准图': item_data['标准图'],
            '审核结果': data.get('审核结果', ''),
            '问题描述': data.get('问题描述', '')
        }
        
        # 保存或更新审核结果
        if review_manager.has_review(item_id):
            success = review_manager.update_review(item_id, review_data)
        else:
            success = review_manager.save_review(item_id, review_data)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500
            
    except Exception as e:
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
        
        # 获取现有审核记录
        review = review_manager.get_review(item_id)
        
        if review:
            # 更新问题描述
            review['问题描述'] = problem_note
            # 使用update_review方法更新到数据库
            success = review_manager.update_review(item_id, review)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': '更新失败'}), 500
        else:
            return jsonify({'success': False, 'error': '审核记录不存在'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export', methods=['GET'])
def export_csv():
    """导出CSV文件"""
    try:
        # 获取所有审核结果
        reviews = review_manager.get_all_reviews()
        
        if not reviews:
            return jsonify({'error': '暂无审核结果可导出'}), 400
        
        # 生成CSV内容
        csv_content = csv_exporter.export_reviews(reviews, inspection_data)
        
        # 生成文件名（使用URL编码）
        from urllib.parse import quote
        filename = csv_exporter.generate_filename()
        filename_encoded = quote(filename)
        
        # 创建响应
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
        print(f"导出CSV失败: {e}")
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取审核统计信息（按门店统计）"""
    try:
        # 如果没有数据，返回0
        if not inspection_data:
            return jsonify({
                'total': 0,
                'reviewed': 0,
                'percentage': 0
            })
        
        # 获取筛选参数
        operator = request.args.get('operator', '全部')
        
        # 获取对应运营人员的检查项
        if operator and operator != '全部' and data_loader:
            filtered_items = data_loader.filter_by_operator(operator)
        else:
            filtered_items = inspection_data
        
        # 按门店分组统计
        stores = {}
        for item in filtered_items:
            store_id = item['门店编号']
            if store_id not in stores:
                stores[store_id] = {
                    'items': []
                }
            stores[store_id]['items'].append(item)
        
        # 统计完成的门店数
        total_stores = len(stores)
        completed_stores = 0
        
        for store_id, store_data in stores.items():
            # 检查门店是否完成：所有检查项都已审核，且不合格的都有问题描述
            all_completed = True
            for item in store_data['items']:
                review = review_manager.get_review(item['id'])
                if not review:
                    all_completed = False
                    break
                
                # 如果是不合格，必须有问题描述
                if review.get('审核结果') == '不合格':
                    if not review.get('问题描述') or review.get('问题描述').strip() == '':
                        all_completed = False
                        break
            
            if all_completed:
                completed_stores += 1
        
        # 计算百分比
        percentage = round((completed_stores / total_stores * 100) if total_stores > 0 else 0, 1)
        
        return jsonify({
            'total': total_stores,
            'reviewed': completed_stores,
            'percentage': percentage
        })
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    """管理员重置审核数据（开始新周期）"""
    try:
        # 验证权限（简单验证）
        data = request.get_json()
        operator = data.get('operator', '')
        
        if operator != '窦':
            return jsonify({'success': False, 'error': '权限不足'}), 403
        
        # 清空数据库中的审核记录
        review_manager.clear_all_reviews()
        
        # 重新加载数据
        global inspection_data, data_loader
        excel_file = '检查项记录.xlsx'
        whitelist_file = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'
        
        data_loader = DataLoader(excel_file, whitelist_file)
        inspection_data = data_loader.load_and_process()
        
        # 自动标记无现场结果的检查项
        auto_review_no_result_items()
        
        print(f"[管理员操作] 已重置审核数据，重新加载 {len(inspection_data)} 条检查项")
        
        return jsonify({
            'success': True,
            'message': '已开始新周期',
            'total_items': len(inspection_data)
        })
        
    except Exception as e:
        print(f"重置数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/upload', methods=['POST'])
def admin_upload():
    """管理员上传新的Excel文件（开始新周期）"""
    try:
        # 验证权限
        operator = request.form.get('operator', '')
        if operator != '窦':
            return jsonify({'success': False, 'error': '权限不足'}), 403
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '只支持.xlsx文件'}), 400
        
        # 保存文件（覆盖旧文件）
        target_path = os.path.join(app.config['UPLOAD_FOLDER'], '检查项记录.xlsx')
        file.save(target_path)
        
        print(f"[管理员操作] 上传新文件: {file.filename}")
        
        # 清空数据库中的审核记录
        review_manager.clear_all_reviews()
        
        # 重新加载数据
        global inspection_data, data_loader
        whitelist_file = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'
        
        data_loader = DataLoader(target_path, whitelist_file)
        inspection_data = data_loader.load_and_process()
        
        # 自动标记无现场结果的检查项
        auto_review_no_result_items()
        
        print(f"[管理员操作] 已加载新数据，共 {len(inspection_data)} 条检查项")
        
        return jsonify({
            'success': True,
            'message': '文件上传成功，已开始新周期',
            'total_items': len(inspection_data)
        })
        
    except Exception as e:
        print(f"上传文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_local_ip():
    """获取本机局域网IP地址"""
    import socket
    try:
        # 创建一个UDP连接来获取本机IP
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
            # 检查是否已经有审核记录
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
        print(f"[自动审核] 已自动标记 {count} 个无现场结果的检查项为不合格")
    
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
    whitelist_file = 'D:/pythonproject/Newyobo_operat_database/daily_data/whitelist/whitelist.xlsx'
    if os.path.exists(whitelist_file):
        print("正在加载白名单到数据库...")
        load_whitelist_to_db(whitelist_file)
    else:
        print(f"提示: 未找到白名单文件 {whitelist_file}")
    
    # 加载Excel数据 - 使用固定文件名（如果存在）
    excel_file = '检查项记录.xlsx'
    
    # 检查Excel文件是否存在
    if os.path.exists(excel_file):
        try:
            print("正在加载Excel数据...")
            data_loader = DataLoader(excel_file, whitelist_file)
            inspection_data = data_loader.load_and_process()
            print(f"成功加载 {len(inspection_data)} 条检查项数据")
            
            # 自动标记无现场结果的检查项
            auto_review_no_result_items()
            
            # 显示运营人员统计
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
        print(f"提示: 未找到 {excel_file} 文件")
        print("系统将以空数据启动，请通过管理员上传功能导入数据")
        inspection_data = []
    
    # 获取局域网IP地址
    local_ip = get_local_ip()
    
    # 端口配置（如果5000被占用，可以改成其他端口）
    # 推荐端口: 5001, 5002, 8000, 8080, 8888, 9000
    port = 5001  # 修改这里的端口号
    
    print("=" * 60)
    print("门店检查项图片审核系统启动中...")
    print(f"局域网访问地址: http://{local_ip}:{port}")
    print(f"本机访问地址: http://127.0.0.1:{port}")
    print("=" * 60)
    
    # 启动Flask应用，允许局域网访问
    app.run(host='0.0.0.0', port=port, debug=True)
