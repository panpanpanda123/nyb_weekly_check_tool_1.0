"""
文件上传相关API
File Upload Related APIs
"""
import os
from flask import request, jsonify
from werkzeug.utils import secure_filename
from viewer.data_importer import DataImporter


def allowed_file(filename: str, allowed_exts: set) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


def register_upload_routes(app, get_db_session):
    """注册文件上传相关路由"""
    
    @app.route('/api/upload/whitelist', methods=['POST'])
    def upload_whitelist():
        """上传白名单Excel文件"""
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': '没有上传文件'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '文件名为空'
                }), 400
            
            if not allowed_file(file.filename, {'xlsx'}):
                return jsonify({
                    'success': False,
                    'error': '只支持.xlsx格式的Excel文件'
                }), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                session = get_db_session()
                importer = DataImporter(session)
                result = importer.import_whitelist(filepath)
                
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
        """上传审核结果CSV文件"""
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': '没有上传文件'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '文件名为空'
                }), 400
            
            if not allowed_file(file.filename, {'csv'}):
                return jsonify({
                    'success': False,
                    'error': '只支持.csv格式的文件'
                }), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                session = get_db_session()
                importer = DataImporter(session)
                result = importer.import_reviews(filepath)
                
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
                if os.path.exists(filepath):
                    os.remove(filepath)
                raise e
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'上传失败: {str(e)}'
            }), 500
