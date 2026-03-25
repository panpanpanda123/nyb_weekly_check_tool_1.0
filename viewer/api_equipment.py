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
            
            # 只查询营业时间内的门店（排除 is_open_at_data_time=0 的门店）
            store_query = store_query.filter(EquipmentStatus.is_open_at_data_time == 1)
            
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
            
            # 获取处理记录 - 查今天所有的处理记录
            # 每次导入时 import_equipment_data.py 已经清空了当前时段的处理记录
            # 所以数据库里存在的处理记录就是本轮有效的处理记录
            today_start = datetime.combine(date.today(), datetime.min.time())
            
            all_processing_records = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.store_id.in_(all_store_ids))\
                .filter(EquipmentProcessing.processed_at >= today_start)\
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
                .filter(EquipmentProcessing.processed_at >= today_start)\
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
        """导出设备异常处理结果"""
        try:
            session = get_db_session()
            
            from equipment_config import ENABLE_MULTI_DAY_CHRONIC
            
            history_days = int(request.args.get('history_days', 10))
            
            # 只导出营业时间内的门店
            equipment_list = session.query(EquipmentStatus)\
                .filter(EquipmentStatus.is_open_at_data_time == 1)\
                .all()
            
            # 获取当前处理记录（只看今天的，跟网页展示一致）
            today_start = datetime.combine(date.today(), datetime.min.time())
            current_processing_list = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.processed_at >= today_start)\
                .all()
            current_processing_dict = {}
            for p in current_processing_list:
                key = f"{p.store_id}_{p.equipment_type}"
                current_processing_dict[key] = p
            
            # 多日统计相关数据（仅开关打开时查询）
            processing_history_dict = {}
            snapshot_dict = {}
            if ENABLE_MULTI_DAY_CHRONIC:
                history_cutoff = datetime.now() - timedelta(days=history_days)
                all_processing_records = session.query(EquipmentProcessing)\
                    .filter(EquipmentProcessing.processed_at >= history_cutoff)\
                    .order_by(EquipmentProcessing.processed_at.desc())\
                    .all()
                for p in all_processing_records:
                    key = f"{p.store_id}_{p.equipment_type}"
                    if key not in processing_history_dict:
                        processing_history_dict[key] = []
                    processing_history_dict[key].append(p)
                
                cutoff_date = date.today() - timedelta(days=10)
                snapshots = session.query(EquipmentStatusSnapshot)\
                    .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff_date)\
                    .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
                    .order_by(EquipmentStatusSnapshot.snapshot_date.desc())\
                    .all()
                for snapshot in snapshots:
                    key = f"{snapshot.store_id}_{snapshot.equipment_type}"
                    if key not in snapshot_dict:
                        snapshot_dict[key] = []
                    snapshot_dict[key].append(snapshot)
            
            def check_suppressed_status(store_id, equipment_type):
                from equipment_utils import should_suppress
                is_suppressed = should_suppress(session, store_id, equipment_type)
                if is_suppressed:
                    # 查有 suppressed_until 的最新记录（跟 should_suppress 逻辑一致）
                    proc = session.query(EquipmentProcessing)\
                        .filter(EquipmentProcessing.store_id == store_id)\
                        .filter(EquipmentProcessing.equipment_type == equipment_type)\
                        .filter(EquipmentProcessing.suppressed_until.isnot(None))\
                        .order_by(EquipmentProcessing.processed_at.desc())\
                        .first()
                    if proc and proc.expected_recovery_date:
                        return f"是（预计{proc.expected_recovery_date.strftime('%m-%d')}恢复）"
                    return "是"
                return "否"
            
            export_data = []
            for equipment in equipment_list:
                key = f"{equipment.store_id}_{equipment.equipment_type}"
                current_processing = current_processing_dict.get(key)
                suppressed_status = check_suppressed_status(equipment.store_id, equipment.equipment_type)
                
                row = {
                    '门店ID': equipment.store_id,
                    '门店名称': equipment.store_name,
                    '战区': equipment.war_zone,
                    '区域经理': equipment.regional_manager,
                    '设备类型': equipment.equipment_type,
                    '设备编号': equipment.equipment_id,
                    '设备名称': equipment.equipment_name,
                    '当前状态': equipment.status,
                    '数据时间点是否营业': '是' if equipment.is_open_at_data_time else '否',
                }
                
                # 多日统计列（跟随功能开关）
                if ENABLE_MULTI_DAY_CHRONIC:
                    is_chronic = False
                    chronic_reason = ''
                    count_5days = 0
                    count_10days = 0
                    abnormal_times = ''
                    counts = {}
                    
                    if equipment.equipment_type == 'POS':
                        is_chronic, chronic_reason, counts = is_chronic_store(session, equipment.store_id, equipment.equipment_type)
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
                    
                    row['是否经常出问题'] = '是' if is_chronic else '否'
                    row['触发原因'] = chronic_reason or ''
                    row['最近5天异常次数'] = count_5days if equipment.equipment_type == 'POS' else ''
                    row['最近10天异常次数'] = count_10days if equipment.equipment_type == 'POS' else ''
                    row['异常时间点'] = abnormal_times
                    row['未处理日期'] = '、'.join(counts.get('unprocessed_dates', [])) if equipment.equipment_type == 'POS' else ''
                    
                    history_records = processing_history_dict.get(key, [])
                    row[f'近{history_days}天处理次数'] = len(history_records)
                    row[f'近{history_days}天已恢复次数'] = sum(1 for r in history_records if r.action == '已恢复')
                    row[f'近{history_days}天未恢复次数'] = sum(1 for r in history_records if r.action == '未恢复')
                    
                    processing_details = []
                    for record in history_records[:5]:
                        detail = f"{record.processed_at.strftime('%m-%d %H:%M')} {record.action}"
                        if record.reason:
                            detail += f"({record.reason[:10]}...)" if len(record.reason) > 10 else f"({record.reason})"
                        processing_details.append(detail)
                    row['最近处理记录'] = '；'.join(processing_details)
                
                row['处理动作'] = current_processing.action if current_processing else '未处理'
                row['未恢复原因'] = current_processing.reason if current_processing else ''
                row['处理时间'] = current_processing.processed_at.strftime('%Y-%m-%d %H:%M:%S') if current_processing and current_processing.processed_at else ''
                row['预计恢复日期'] = current_processing.expected_recovery_date.strftime('%Y-%m-%d') if current_processing and current_processing.expected_recovery_date else ''
                row['恢复期内免查'] = suppressed_status
                
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='设备异常处理结果')
                
                worksheet = writer.sheets['设备异常处理结果']
                # 自动设置列宽
                for i, col in enumerate(df.columns):
                    max_len = max(len(str(col)), df[col].astype(str).str.len().max() if len(df) > 0 else 0)
                    worksheet.column_dimensions[chr(65 + i) if i < 26 else chr(64 + i // 26) + chr(65 + i % 26)].width = min(max_len + 4, 50)
            
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

    @app.route('/api/equipment/export-warning')
    def export_warning():
        """导出警告单：当前时段最终离线门店，字段精简，用于开具警告单"""
        try:
            session = get_db_session()

            equipment_list = session.query(EquipmentStatus)\
                .filter(EquipmentStatus.is_open_at_data_time == 1)\
                .order_by(EquipmentStatus.war_zone, EquipmentStatus.regional_manager,
                          EquipmentStatus.store_id)\
                .all()

            # 获取最新导入时间（用于"数据时间点"列）
            latest_import = session.query(EquipmentImportLog)\
                .order_by(EquipmentImportLog.import_time.desc())\
                .first()
            data_time_str = latest_import.data_time if latest_import and latest_import.data_time else ''

            def get_suppressed_info(store_id, equipment_type):
                from equipment_utils import should_suppress
                if not should_suppress(session, store_id, equipment_type):
                    return '', '否'
                proc = session.query(EquipmentProcessing)\
                    .filter(EquipmentProcessing.store_id == store_id)\
                    .filter(EquipmentProcessing.equipment_type == equipment_type)\
                    .filter(EquipmentProcessing.suppressed_until.isnot(None))\
                    .order_by(EquipmentProcessing.processed_at.desc())\
                    .first()
                recovery_date = proc.expected_recovery_date.strftime('%Y-%m-%d') if proc and proc.expected_recovery_date else ''
                return recovery_date, '是'

            export_data = []
            for eq in equipment_list:
                recovery_date, suppressed = get_suppressed_info(eq.store_id, eq.equipment_type)
                export_data.append({
                    '门店ID': eq.store_id,
                    '门店名称': eq.store_name,
                    '战区': eq.war_zone or '',
                    '区域经理': eq.regional_manager or '',
                    '设备名称': eq.equipment_name or eq.equipment_id or '',
                    '当前状态': eq.status or '离线',
                    '数据时间点是否营业': '是' if eq.is_open_at_data_time else '否',
                    '预计恢复日期': recovery_date,
                    '恢复期内免查': suppressed,
                })

            df = pd.DataFrame(export_data)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='警告单')
                ws = writer.sheets['警告单']
                col_widths = [10, 20, 12, 12, 20, 10, 16, 14, 12]
                for i, w in enumerate(col_widths):
                    col_letter = chr(65 + i) if i < 26 else chr(64 + i // 26) + chr(65 + i % 26)
                    ws.column_dimensions[col_letter].width = w
            output.seek(0)

            filename = f'设备离线警告单_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'导出失败: {str(e)}'}), 500

    @app.route('/api/equipment/suppressed')
    def get_suppressed_stores():
        """获取所有免查门店列表（恢复期内）"""
        try:
            session = get_db_session()
            
            today = date.today()
            today_dt = datetime.combine(today, datetime.min.time())
            
            # 查询所有 suppressed_until >= 今天 的处理记录
            suppressed_records = session.query(EquipmentProcessing)\
                .filter(EquipmentProcessing.suppressed_until.isnot(None))\
                .filter(EquipmentProcessing.suppressed_until >= today_dt)\
                .order_by(EquipmentProcessing.processed_at.desc())\
                .all()
            
            # 每个 store_id + equipment_type 只取最新的一条
            seen = set()
            result_list = []
            for rec in suppressed_records:
                key = f"{rec.store_id}_{rec.equipment_type}"
                if key in seen:
                    continue
                seen.add(key)
                
                # 查门店信息（从 whitelist 或 equipment_status）
                store_info = session.query(EquipmentStatus)\
                    .filter(EquipmentStatus.store_id == rec.store_id)\
                    .first()
                
                if not store_info:
                    from shared.database_models import StoreWhitelist
                    wl = session.query(StoreWhitelist)\
                        .filter(StoreWhitelist.store_id == rec.store_id)\
                        .first()
                    store_name = wl.store_name if wl else rec.store_id
                    war_zone = wl.war_zone if wl else ''
                    regional_manager = wl.regional_manager if wl else ''
                else:
                    store_name = store_info.store_name
                    war_zone = store_info.war_zone
                    regional_manager = store_info.regional_manager
                
                suppressed_date = rec.suppressed_until.date() if hasattr(rec.suppressed_until, 'date') else rec.suppressed_until
                remaining_days = (suppressed_date - today).days
                
                result_list.append({
                    'store_id': rec.store_id,
                    'store_name': store_name,
                    'war_zone': war_zone,
                    'regional_manager': regional_manager,
                    'equipment_type': rec.equipment_type,
                    'action': rec.action,
                    'reason': rec.reason or '',
                    'processed_at': rec.processed_at.strftime('%Y-%m-%d %H:%M') if rec.processed_at else '',
                    'expected_recovery_date': rec.expected_recovery_date.strftime('%Y-%m-%d') if rec.expected_recovery_date else '',
                    'suppressed_until': rec.suppressed_until.strftime('%Y-%m-%d') if rec.suppressed_until else '',
                    'remaining_days': remaining_days
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': result_list,
                    'total': len(result_list)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取免查门店失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/non-operating')
    def get_non_operating_stores():
        """获取检查时间点未营业的门店列表"""
        try:
            session = get_db_session()
            
            # 查询 is_open_at_data_time=0 的门店（导入时标记为未在营业时间内）
            non_operating = session.query(EquipmentStatus)\
                .filter(EquipmentStatus.is_open_at_data_time == 0)\
                .order_by(EquipmentStatus.war_zone, EquipmentStatus.store_id)\
                .all()
            
            # 按门店分组
            stores_data = {}
            for eq in non_operating:
                if eq.store_id not in stores_data:
                    stores_data[eq.store_id] = {
                        'store_id': eq.store_id,
                        'store_name': eq.store_name,
                        'war_zone': eq.war_zone,
                        'regional_manager': eq.regional_manager,
                        'business_hours': eq.business_hours or '未知',
                        'equipment': []
                    }
                stores_data[eq.store_id]['equipment'].append({
                    'equipment_type': eq.equipment_type,
                    'equipment_id': eq.equipment_id,
                    'equipment_name': eq.equipment_name,
                    'status': eq.status
                })
            
            # 获取数据时间
            latest_log = session.query(EquipmentImportLog)\
                .order_by(EquipmentImportLog.import_time.desc())\
                .first()
            data_time = latest_log.data_time if latest_log else ''
            
            result_list = list(stores_data.values())
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': result_list,
                    'total': len(result_list),
                    'data_time': data_time
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取未营业门店失败: {str(e)}'
            }), 500

    @app.route('/api/equipment/store-history')
    def get_store_history():
        """查询门店近N天离线历史记录"""
        try:
            session = get_db_session()

            keyword = request.args.get('keyword', '').strip()
            days = int(request.args.get('days', 10))

            if not keyword:
                return jsonify({'success': False, 'error': '请输入门店ID或名称'}), 400

            from shared.database_models import StoreWhitelist
            from sqlalchemy import or_, func
            matched = session.query(StoreWhitelist.store_id, StoreWhitelist.store_name,
                                    StoreWhitelist.war_zone, StoreWhitelist.regional_manager)\
                .filter(or_(
                    StoreWhitelist.store_id == keyword,
                    StoreWhitelist.store_name.like(f'%{keyword}%')
                )).all()

            if not matched:
                return jsonify({'success': True, 'data': {'stores': [], 'total': 0}})

            cutoff = datetime.now() - timedelta(days=days)
            result = []

            for store_id, store_name, war_zone, regional_manager in matched:
                # 按 (日期, 时段) 分组，每组取最新的 snapshot_date
                # 每个时段只算一次离线，时间显示该时段最后一次上传的时间
                rows = session.query(
                        func.date(EquipmentStatusSnapshot.snapshot_date).label('snap_date'),
                        EquipmentStatusSnapshot.snapshot_period,
                        func.max(EquipmentStatusSnapshot.snapshot_date).label('latest_time')
                    )\
                    .filter(EquipmentStatusSnapshot.store_id == store_id)\
                    .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff)\
                    .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
                    .group_by(
                        func.date(EquipmentStatusSnapshot.snapshot_date),
                        EquipmentStatusSnapshot.snapshot_period
                    )\
                    .order_by(func.date(EquipmentStatusSnapshot.snapshot_date).desc(),
                              EquipmentStatusSnapshot.snapshot_period.desc())\
                    .all()

                history = []
                for row in rows:
                    history.append({
                        'date': str(row.snap_date),
                        'time': row.latest_time.strftime('%H:%M'),
                        'period': '上午' if row.snapshot_period == 'AM' else '下午',
                    })

                result.append({
                    'store_id': store_id,
                    'store_name': store_name,
                    'war_zone': war_zone or '',
                    'regional_manager': regional_manager or '',
                    'history': history,
                    'total_records': len(history)
                })

            return jsonify({'success': True, 'data': {'stores': result, 'total': len(result)}})

        except Exception as e:
            return jsonify({'success': False, 'error': f'查询失败: {str(e)}'}), 500
