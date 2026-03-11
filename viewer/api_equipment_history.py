"""
设备异常历史记录API（只读）
Equipment History Records API (Read-only)
"""
from flask import request, jsonify
from datetime import datetime, timedelta, date
from shared.database_models import EquipmentProcessing, EquipmentStatusSnapshot


def register_equipment_history_routes(app, get_db_session):
    """注册设备异常历史记录相关路由（只读）"""
    
    @app.route('/api/equipment/history/processing')
    def get_processing_history():
        """获取处理记录历史（只读）"""
        try:
            session = get_db_session()
            
            days = int(request.args.get('days', 7))
            date_filter = request.args.get('date', '').strip()  # 可选：指定日期
            
            # 构建查询
            query = session.query(EquipmentProcessing)
            
            if date_filter:
                # 查询指定日期
                try:
                    target_date = datetime.strptime(date_filter, '%Y-%m-%d')
                    start_time = datetime.combine(target_date.date(), datetime.min.time())
                    end_time = datetime.combine(target_date.date(), datetime.max.time())
                    query = query.filter(EquipmentProcessing.processed_at >= start_time)\
                                 .filter(EquipmentProcessing.processed_at <= end_time)
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '日期格式错误，应为 YYYY-MM-DD'
                    }), 400
            else:
                # 查询最近N天
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.filter(EquipmentProcessing.processed_at >= cutoff_date)
            
            records = query.order_by(EquipmentProcessing.processed_at.desc()).all()
            
            # 按日期分组
            records_by_date = {}
            for record in records:
                date_key = record.processed_at.strftime('%Y-%m-%d')
                if date_key not in records_by_date:
                    records_by_date[date_key] = {
                        'date': date_key,
                        'am_records': [],
                        'pm_records': [],
                        'total': 0,
                        'recovered': 0,
                        'not_recovered': 0
                    }
                
                record_data = {
                    'id': record.id,
                    'store_id': record.store_id,
                    'equipment_type': record.equipment_type,
                    'action': record.action,
                    'reason': record.reason or '',
                    'processed_at': record.processed_at.strftime('%H:%M:%S'),
                    'expected_recovery_date': record.expected_recovery_date.strftime('%Y-%m-%d') if record.expected_recovery_date else None
                }
                
                # 按时段分类
                if record.processed_at.hour < 14:
                    records_by_date[date_key]['am_records'].append(record_data)
                else:
                    records_by_date[date_key]['pm_records'].append(record_data)
                
                records_by_date[date_key]['total'] += 1
                if record.action == '已恢复':
                    records_by_date[date_key]['recovered'] += 1
                else:
                    records_by_date[date_key]['not_recovered'] += 1
            
            # 转换为列表并排序
            history_list = sorted(records_by_date.values(), 
                                key=lambda x: x['date'], 
                                reverse=True)
            
            # 统计信息
            total_records = len(records)
            total_recovered = sum(1 for r in records if r.action == '已恢复')
            total_not_recovered = sum(1 for r in records if r.action == '未恢复')
            
            return jsonify({
                'success': True,
                'data': {
                    'history': history_list,
                    'stats': {
                        'total': total_records,
                        'recovered': total_recovered,
                        'not_recovered': total_not_recovered,
                        'days': days
                    }
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取历史记录失败: {str(e)}'
            }), 500
    
    @app.route('/api/equipment/history/snapshots')
    def get_snapshots_history():
        """获取快照历史（只读）"""
        try:
            session = get_db_session()
            
            days = int(request.args.get('days', 7))
            
            cutoff_date = date.today() - timedelta(days=days)
            
            snapshots = session.query(EquipmentStatusSnapshot)\
                .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff_date)\
                .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
                .order_by(EquipmentStatusSnapshot.snapshot_date.desc())\
                .all()
            
            # 按日期分组
            snapshots_by_date = {}
            for snap in snapshots:
                snap_date = snap.snapshot_date.date() if hasattr(snap.snapshot_date, 'date') else snap.snapshot_date
                date_key = snap_date.strftime('%Y-%m-%d')
                
                if date_key not in snapshots_by_date:
                    snapshots_by_date[date_key] = {
                        'date': date_key,
                        'am_stores': [],
                        'pm_stores': [],
                        'am_count': 0,
                        'pm_count': 0,
                        'repeat_stores': []
                    }
                
                if snap.snapshot_period == 'AM':
                    snapshots_by_date[date_key]['am_stores'].append(snap.store_id)
                    snapshots_by_date[date_key]['am_count'] += 1
                else:
                    snapshots_by_date[date_key]['pm_stores'].append(snap.store_id)
                    snapshots_by_date[date_key]['pm_count'] += 1
            
            # 计算当天反复的门店
            for date_key, data in snapshots_by_date.items():
                am_set = set(data['am_stores'])
                pm_set = set(data['pm_stores'])
                repeat_stores = list(am_set & pm_set)
                data['repeat_stores'] = repeat_stores
                data['repeat_count'] = len(repeat_stores)
            
            # 转换为列表并排序
            history_list = sorted(snapshots_by_date.values(), 
                                key=lambda x: x['date'], 
                                reverse=True)
            
            return jsonify({
                'success': True,
                'data': {
                    'history': history_list,
                    'total_snapshots': len(snapshots),
                    'days': days
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取快照历史失败: {str(e)}'
            }), 500
