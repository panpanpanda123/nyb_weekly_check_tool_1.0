"""
设备异常监控相关API
Equipment Monitoring Related APIs
"""
from flask import request, jsonify, send_file
from datetime import datetime, timedelta, date
import pandas as pd
from io import BytesIO
from shared.database_models import EquipmentStatus, EquipmentProcessing, EquipmentImportLog, EquipmentStatusSnapshot
from equipment_utils import calculate_chronic_stats, should_suppress, is_chronic_store, get_abnormal_count
from equipment_config import EXPECTED_RECOVERY_MAX_DAYS


def register_equipment_routes(app, get_db_session):
    """注册设备异常监控相关路由"""
    
    @app.route('/api/equipment/filters')
    def get_equipment_filters():
        """获取设备异常筛选选项"""
        try:
            session = get_db_session()
            
            war_zones = session.query(EquipmentStatus.war_zone)\
                .filter(EquipmentStatus.war_zone.isnot(None))\
                .filter(EquipmentStatus.war_zone != '')\
                .distinct()\
                .order_by(EquipmentStatus.war_zone)\
                .all()
            war_zones = [wz[0] for wz in war_zones]
            
            latest_log = session.query(EquipmentImportLog)\
                .order_by(EquipmentImportLog.import_time.desc())\
                .first()
            
            data_time = latest_log.data_time if latest_log and latest_log.data_time else None
            
            return jsonify({
                'success': True,
                'data': {
                    'war_zones': war_zones,
                    'data_time': data_time
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取筛选选项失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/regional-managers')
    def get_equipment_regional_managers():
        """根据战区获取区域经理列表"""
        try:
            session = get_db_session()
            
            war_zone = request.args.get('war_zone', '').strip()
            
            if not war_zone:
                return jsonify({
                    'success': False,
                    'error': '缺少战区参数'
                }), 400
            
            regional_managers = session.query(EquipmentStatus.regional_manager)\
                .filter(EquipmentStatus.war_zone == war_zone)\
                .filter(EquipmentStatus.regional_manager.isnot(None))\
                .filter(EquipmentStatus.regional_manager != '')\
                .distinct()\
                .order_by(EquipmentStatus.regional_manager)\
                .all()
            regional_managers = [rm[0] for rm in regional_managers]
            
            return jsonify({
                'success': True,
                'data': {
                    'regional_managers': regional_managers
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取区域经理列表失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/all-regional-managers')
    def get_all_equipment_regional_managers():
        """获取所有区域经理列表"""
        try:
            session = get_db_session()
            
            regional_managers = session.query(EquipmentStatus.regional_manager)\
                .filter(EquipmentStatus.regional_manager.isnot(None))\
                .filter(EquipmentStatus.regional_manager != '')\
                .distinct()\
                .order_by(EquipmentStatus.regional_manager)\
                .all()
            regional_managers = [rm[0] for rm in regional_managers]
            
            return jsonify({
                'success': True,
                'data': {
                    'regional_managers': regional_managers
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取区域经理列表失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/search')
    def search_equipment():
        """搜索设备异常"""
        try:
            session = get_db_session()
            
            war_zone = request.args.get('war_zone', '').strip()
            regional_manager = request.args.get('regional_manager', '').strip()
            store_search = request.args.get('store_search', '').strip()
            status_filter = request.args.get('status_filter', '').strip()
            
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            from sqlalchemy import func, distinct
            
            store_query = session.query(distinct(EquipmentStatus.store_id))
            
            if store_search:
                store_query = store_query.filter(
                    (EquipmentStatus.store_id == store_search) |
                    (EquipmentStatus.store_name.like(f'%{store_search}%'))
                )
            
            if war_zone:
                store_query = store_query.filter(EquipmentStatus.war_zone == war_zone)
            if regional_manager:
                store_query = store_query.filter(EquipmentStatus.regional_manager == regional_manager)
            
            total_stores = store_query.count()
            
            all_store_ids = [sid[0] for sid in store_query.all()]
            
            # 过滤暂时不提示的门店
            suppressed_store_ids = set()
            for store_id in all_store_ids:
                if should_suppress(session, store_id, 'POS'):
                    suppressed_store_ids.add(store_id)
            
            all_store_ids = [sid for sid in all_store_ids if sid not in suppressed_store_ids]
            total_stores = len(all_store_ids)
            
            # 获取处理记录 - 只看当前时段的处理记录
            # 上午导入后：没有处理记录（都是未处理）
            # 下午导入后：没有处理记录（下午的被清空了），上午的保留用于判定"当天反复"
            from equipment_config import AM_PM_BOUNDARY_HOUR
            current_hour = datetime.now().hour
            current_period = 'AM' if current_hour < AM_PM_BOUNDARY_HOUR else 'PM'
            
            today_start = datetime.combine(date.today(), datetime.min.time())
            
            if current_period == 'AM':
                # 上午：只看今天上午的处理记录
                processing_filter_start = today_start
            else:
                # 下午：只看今天下午的处理记录（上午的保留但不算"已处理"）
                processing_filter_start = datetime.combine(date.today(), datetime.min.time().replace(hour=AM_PM_BOUNDARY_HOUR))
            
            all_processing_records = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.store_id.in_(all_store_ids))\
                .filter(EquipmentProcessing.processed_at >= processing_filter_start)\
                .all()
            
            processed_store_ids = set()
            recovered_store_ids = set()
            not_recovered_store_ids = set()
            
            store_processing = {}
            for p in all_processing_records:
                if p.store_id not in store_processing:
                    store_processing[p.store_id] = []
                store_processing[p.store_id].append(p)
            
            for store_id, records in store_processing.items():
                processed_store_ids.add(store_id)
                
                has_not_recovered = any(r.action == '未恢复' for r in records)
                
                if has_not_recovered:
                    not_recovered_store_ids.add(store_id)
                else:
                    recovered_store_ids.add(store_id)
            
            total_processed = len(processed_store_ids)
            total_pending = total_stores - total_processed
            total_recovered = len(recovered_store_ids)
            total_not_recovered = len(not_recovered_store_ids)
            
            chronic_stats = calculate_chronic_stats(session, all_store_ids)
            total_chronic = sum(1 for stats in chronic_stats.values() if stats['is_chronic'])
            
            # 根据状态筛选
            filtered_store_ids = all_store_ids
            if status_filter == 'pending':
                filtered_store_ids = [sid for sid in all_store_ids if sid not in processed_store_ids]
            elif status_filter == 'recovered':
                filtered_store_ids = list(recovered_store_ids)
            elif status_filter == 'not_recovered':
                filtered_store_ids = list(not_recovered_store_ids)
            elif status_filter == 'chronic':
                filtered_store_ids = [sid for sid in all_store_ids if chronic_stats.get(sid, {}).get('is_chronic', False)]
            
            filtered_total = len(filtered_store_ids)
            filtered_total_pages = (filtered_total + per_page - 1) // per_page if filtered_total > 0 else 1
            
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            store_ids = filtered_store_ids[start_idx:end_idx]
            
            equipment_list = session.query(EquipmentStatus)\
                .filter(EquipmentStatus.store_id.in_(store_ids))\
                .order_by(EquipmentStatus.store_id, EquipmentStatus.id)\
                .all()
            
            processing_records = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.store_id.in_(store_ids))\
                .filter(EquipmentProcessing.processed_at >= processing_filter_start)\
                .all()
            processing_dict = {}
            for p in processing_records:
                key = f"{p.store_id}_{p.equipment_type}"
                processing_dict[key] = p.to_dict()
            
            stores_data = {}
            for equipment in equipment_list:
                if equipment.store_id not in stores_data:
                    chronic_info = chronic_stats.get(equipment.store_id, {})
                    
                    stores_data[equipment.store_id] = {
                        'store_id': equipment.store_id,
                        'store_name': equipment.store_name,
                        'war_zone': equipment.war_zone,
                        'regional_manager': equipment.regional_manager,
                        'equipment': [],
                        'processing_pos': processing_dict.get(f"{equipment.store_id}_POS"),
                        'processing_stb': processing_dict.get(f"{equipment.store_id}_机顶盒"),
                        'is_chronic': chronic_info.get('is_chronic', False),
                        'chronic_reason': chronic_info.get('chronic_reason'),
                        'abnormal_count_5days': chronic_info.get('abnormal_count_5days', 0),
                        'abnormal_count_10days': chronic_info.get('abnormal_count_10days', 0)
                    }
                stores_data[equipment.store_id]['equipment'].append(equipment.to_dict())
            
            stores_list = list(stores_data.values())
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': stores_list,
                    'total_stores': total_stores,
                    'total_pending': total_pending,
                    'total_processed': total_processed,
                    'total_recovered': total_recovered,
                    'total_not_recovered': total_not_recovered,
                    'total_chronic': total_chronic,
                    'filtered_total': filtered_total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': filtered_total_pages,
                    'has_more': page < filtered_total_pages
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'搜索失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/process', methods=['POST'])
    def process_equipment():
        """处理设备异常"""
        try:
            session = get_db_session()
            
            data = request.get_json()
            store_id = data.get('store_id')
            equipment_type = data.get('equipment_type')
            action = data.get('action')
            reason = data.get('reason', '')
            expected_recovery_date_str = data.get('expected_recovery_date')
            
            if not store_id or not equipment_type or not action:
                return jsonify({
                    'success': False,
                    'error': '缺少必要参数'
                }), 400
            
            expected_recovery_date = None
            suppressed_until = None
            
            if expected_recovery_date_str:
                try:
                    expected_recovery_date = datetime.strptime(expected_recovery_date_str, '%Y-%m-%d')
                    
                    max_date = datetime.now() + timedelta(days=EXPECTED_RECOVERY_MAX_DAYS)
                    if expected_recovery_date > max_date:
                        return jsonify({
                            'success': False,
                            'error': f'预计恢复日期不能超过{EXPECTED_RECOVERY_MAX_DAYS}天'
                        }), 400
                    
                    suppressed_until = expected_recovery_date
                    
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '预计恢复日期格式错误，应为 YYYY-MM-DD'
                    }), 400
            
            existing = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.store_id == store_id)\
                .filter(EquipmentProcessing.equipment_type == equipment_type)\
                .first()
            
            if existing:
                existing.action = action
                existing.reason = reason
                existing.processed_at = datetime.now()
                existing.expected_recovery_date = expected_recovery_date
                existing.suppressed_until = suppressed_until
            else:
                processing = EquipmentProcessing(
                    store_id=store_id,
                    equipment_type=equipment_type,
                    action=action,
                    reason=reason,
                    expected_recovery_date=expected_recovery_date,
                    suppressed_until=suppressed_until
                )
                session.add(processing)
            
            session.commit()
            
            return jsonify({
                'success': True,
                'message': '处理成功'
            })
            
        except Exception as e:
            session.rollback()
            return jsonify({
                'success': False,
                'error': f'处理失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/export')
    def export_equipment():
        """导出设备异常处理结果（包含近期处理记录）"""
        try:
            session = get_db_session()
            
            # 获取查询天数参数（默认10天）
            history_days = int(request.args.get('history_days', 10))
            
            equipment_list = session.query(EquipmentStatus).all()
            
            # 获取最新的处理记录（当前状态）
            current_processing_list = session.query(EquipmentProcessing).all()
            current_processing_dict = {}
            for p in current_processing_list:
                key = f"{p.store_id}_{p.equipment_type}"
                current_processing_dict[key] = p
            
            # 获取近期所有处理记录（用于统计处理次数）
            history_cutoff = datetime.now() - timedelta(days=history_days)
            all_processing_records = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.processed_at >= history_cutoff)\
                .order_by(EquipmentProcessing.processed_at.desc())\
                .all()
            
            # 按门店和设备类型分组处理记录
            processing_history_dict = {}
            for p in all_processing_records:
                key = f"{p.store_id}_{p.equipment_type}"
                if key not in processing_history_dict:
                    processing_history_dict[key] = []
                processing_history_dict[key].append(p)
            
            # 获取快照数据
            cutoff_date = date.today() - timedelta(days=10)
            snapshots = session.query(EquipmentStatusSnapshot)\
                .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff_date)\
                .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
                .order_by(EquipmentStatusSnapshot.snapshot_date.desc())\
                .all()
            
            snapshot_dict = {}
            for snapshot in snapshots:
                key = f"{snapshot.store_id}_{snapshot.equipment_type}"
                if key not in snapshot_dict:
                    snapshot_dict[key] = []
                snapshot_dict[key].append(snapshot)
            
            # 检查是否在预计恢复期内被跳过
            def check_suppressed_status(store_id, equipment_type):
                """检查门店是否在预计恢复期内被跳过"""
                from equipment_utils import should_suppress
                is_suppressed = should_suppress(session, store_id, equipment_type)
                if is_suppressed:
                    # 获取预计恢复日期
                    proc = current_processing_dict.get(f"{store_id}_{equipment_type}")
                    if proc and proc.expected_recovery_date:
                        return f"是（预计{proc.expected_recovery_date.strftime('%m-%d')}恢复）"
                return "否"
            
            export_data = []
            for equipment in equipment_list:
                key = f"{equipment.store_id}_{equipment.equipment_type}"
                current_processing = current_processing_dict.get(key)
                
                is_chronic = False
                chronic_reason = ''
                count_5days = 0
                count_10days = 0
                abnormal_times = ''
                counts = {}
                
                if equipment.equipment_type == 'POS':
                    is_chronic, chronic_reason, counts = is_chronic_store(
                        session, 
                        equipment.store_id, 
                        equipment.equipment_type
                    )
                    count_5days = get_abnormal_count(session, equipment.store_id, equipment.equipment_type, 5, exclude_today=False)
                    count_10days = get_abnormal_count(session, equipment.store_id, equipment.equipment_type, 10, exclude_today=False)
                    
                    store_snapshots = snapshot_dict.get(key, [])
                    if store_snapshots:
                        time_list = []
                        seen_times = set()
                        for snap in store_snapshots:
                            time_str = snap.snapshot_date.strftime('%m-%d')
                            period = snap.snapshot_period
                            time_key = f"{time_str}_{period}"
                            
                            if time_key not in seen_times:
                                seen_times.add(time_key)
                                period_text = '上午' if period == 'AM' else '下午'
                                time_list.append(f"{time_str}{period_text}")
                                
                                if len(time_list) >= 5:
                                    break
                        
                        abnormal_times = '、'.join(time_list)
                
                # 统计近期处理记录
                history_records = processing_history_dict.get(key, [])
                total_processing_count = len(history_records)
                recovered_count = sum(1 for r in history_records if r.action == '已恢复')
                not_recovered_count = sum(1 for r in history_records if r.action == '未恢复')
                
                # 生成处理记录详情（最近5条）
                processing_details = []
                for i, record in enumerate(history_records[:5]):
                    detail = f"{record.processed_at.strftime('%m-%d %H:%M')} {record.action}"
                    if record.reason:
                        detail += f"({record.reason[:10]}...)" if len(record.reason) > 10 else f"({record.reason})"
                    processing_details.append(detail)
                processing_details_str = '；'.join(processing_details) if processing_details else ''
                
                # 检查是否被跳过
                suppressed_status = check_suppressed_status(equipment.store_id, equipment.equipment_type)
                
                export_data.append({
                    '门店ID': equipment.store_id,
                    '门店名称': equipment.store_name,
                    '战区': equipment.war_zone,
                    '区域经理': equipment.regional_manager,
                    '设备类型': equipment.equipment_type,
                    '设备编号': equipment.equipment_id,
                    '设备名称': equipment.equipment_name,
                    '当前状态': equipment.status,
                    '是否经常出问题': '是' if is_chronic else '否',
                    '触发原因': chronic_reason or '',
                    '最近5天异常次数': count_5days if equipment.equipment_type == 'POS' else '',
                    '最近10天异常次数': count_10days if equipment.equipment_type == 'POS' else '',
                    '异常时间点': abnormal_times,
                    '未处理日期': '、'.join(counts.get('unprocessed_dates', [])) if equipment.equipment_type == 'POS' else '',
                    f'近{history_days}天处理次数': total_processing_count,
                    f'近{history_days}天已恢复次数': recovered_count,
                    f'近{history_days}天未恢复次数': not_recovered_count,
                    '最近处理记录': processing_details_str,
                    '当前处理动作': current_processing.action if current_processing else '未处理',
                    '未恢复原因': current_processing.reason if current_processing else '',
                    '当前处理时间': current_processing.processed_at.strftime('%Y-%m-%d %H:%M:%S') if current_processing and current_processing.processed_at else '',
                    '预计恢复日期': current_processing.expected_recovery_date.strftime('%Y-%m-%d') if current_processing and current_processing.expected_recovery_date else '',
                    '预计恢复期内跳过': suppressed_status
                })
            
            df = pd.DataFrame(export_data)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='设备异常处理结果')
                
                worksheet = writer.sheets['设备异常处理结果']
                # 设置列宽
                worksheet.column_dimensions['A'].width = 12   # 门店ID
                worksheet.column_dimensions['B'].width = 25   # 门店名称
                worksheet.column_dimensions['C'].width = 10   # 战区
                worksheet.column_dimensions['D'].width = 12   # 区域经理
                worksheet.column_dimensions['E'].width = 12   # 设备类型
                worksheet.column_dimensions['F'].width = 20   # 设备编号
                worksheet.column_dimensions['G'].width = 20   # 设备名称
                worksheet.column_dimensions['H'].width = 10   # 当前状态
                worksheet.column_dimensions['I'].width = 15   # 是否经常出问题
                worksheet.column_dimensions['J'].width = 20   # 触发原因
                worksheet.column_dimensions['K'].width = 15   # 最近5天异常次数
                worksheet.column_dimensions['L'].width = 15   # 最近10天异常次数
                worksheet.column_dimensions['M'].width = 30   # 异常时间点
                worksheet.column_dimensions['N'].width = 20   # 未处理日期
                worksheet.column_dimensions['O'].width = 15   # 近X天处理次数
                worksheet.column_dimensions['P'].width = 15   # 近X天已恢复次数
                worksheet.column_dimensions['Q'].width = 15   # 近X天未恢复次数
                worksheet.column_dimensions['R'].width = 50   # 最近处理记录
                worksheet.column_dimensions['S'].width = 12   # 当前处理动作
                worksheet.column_dimensions['T'].width = 30   # 未恢复原因
                worksheet.column_dimensions['U'].width = 20   # 当前处理时间
                worksheet.column_dimensions['V'].width = 15   # 预计恢复日期
                worksheet.column_dimensions['W'].width = 20   # 预计恢复期内跳过
            
            output.seek(0)
            
            filename = f'设备异常处理结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'导出失败: {str(e)}'
            }), 500
