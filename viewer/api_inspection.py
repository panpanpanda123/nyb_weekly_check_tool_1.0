"""
周清审核 API
Inspection Review API (按战区筛选)
"""
import pandas as pd
from flask import request, jsonify
from sqlalchemy import func, distinct
from datetime import datetime
from shared.database_models import InspectionReview, StoreWhitelist

# 管理员密码
ADMIN_PASSWORD = 'yuanmingjie'


def register_inspection_routes(app, get_db_session):
    """注册周清审核相关路由"""

    @app.route('/api/inspection/war-zones', methods=['GET'])
    def get_inspection_war_zones():
        """获取战区列表（从白名单获取）"""
        session = get_db_session()
        try:
            # 从白名单获取所有战区
            war_zones = session.query(StoreWhitelist.war_zone)\
                .filter(StoreWhitelist.war_zone.isnot(None))\
                .filter(StoreWhitelist.war_zone != '')\
                .distinct()\
                .order_by(StoreWhitelist.war_zone)\
                .all()
            return jsonify([wz[0] for wz in war_zones])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/verify-password', methods=['POST'])
    def verify_inspection_password():
        """验证管理员密码"""
        try:
            data = request.get_json()
            password = data.get('password', '')
            if password == ADMIN_PASSWORD:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': '密码错误'}), 401
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/inspection/items', methods=['GET'])
    def get_inspection_items():
        """获取检查项数据（按战区筛选，分页）"""
        session = get_db_session()
        try:
            war_zone = request.args.get('war_zone', '全部')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))  # 每页门店数

            # 预加载白名单，建立门店ID到战区的映射
            whitelist_map = {}
            for store in session.query(StoreWhitelist).all():
                whitelist_map[store.store_id] = store.war_zone or '未分配'

            query = session.query(InspectionReview)

            # 如果指定了战区，需要先获取该战区的门店ID列表
            if war_zone and war_zone != '全部':
                store_ids_in_zone = [sid for sid, wz in whitelist_map.items() if wz == war_zone]
                query = query.filter(InspectionReview.store_id.in_(store_ids_in_zone))

            # 排除无现场结果的（已自动标记不合格）
            # 排除已审核完成的门店
            # 先获取所有未完成的门店ID
            all_items = query.order_by(InspectionReview.store_id).all()

            # 按门店分组
            store_groups = {}
            for item in all_items:
                if item.store_id not in store_groups:
                    store_groups[item.store_id] = []
                store_groups[item.store_id].append(item)

            # 分为待审核和已完成
            pending_store_ids = []
            completed_store_ids = []

            for store_id, items in store_groups.items():
                all_done = True
                for item in items:
                    if item.no_result:
                        continue  # 无现场结果的跳过
                    if not item.review_result:
                        all_done = False
                        break
                    if item.review_result == '不合格' and not (item.problem_note and item.problem_note.strip()):
                        all_done = False
                        break
                if all_done:
                    completed_store_ids.append(store_id)
                else:
                    pending_store_ids.append(store_id)

            # 分页：只对待审核门店分页
            total_pending = len(pending_store_ids)
            total_completed = len(completed_store_ids)
            total_pages = max(1, (total_pending + per_page - 1) // per_page)
            page_store_ids = pending_store_ids[(page - 1) * per_page: page * per_page]

            # 获取当前页门店的检查项（排除无现场结果的）
            pending_items = []
            for sid in page_store_ids:
                for item in store_groups[sid]:
                    if not item.no_result:
                        pending_items.append(item.to_item_dict())

            return jsonify({
                'items': pending_items,
                'total_pending_stores': total_pending,
                'total_completed_stores': total_completed,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/reviews', methods=['GET'])
    def get_inspection_reviews():
        """获取所有审核结果"""
        session = get_db_session()
        try:
            war_zone = request.args.get('war_zone', '')

            # 预加载白名单
            whitelist_map = {}
            for store in session.query(StoreWhitelist).all():
                whitelist_map[store.store_id] = store.war_zone or '未分配'

            query = session.query(InspectionReview)\
                .filter(InspectionReview.review_result.isnot(None))\
                .filter(InspectionReview.review_result != '')

            if war_zone and war_zone != '全部':
                store_ids_in_zone = [sid for sid, wz in whitelist_map.items() if wz == war_zone]
                query = query.filter(InspectionReview.store_id.in_(store_ids_in_zone))

            reviews = query.all()
            result = {}
            for r in reviews:
                result[r.item_id] = r.to_dict()
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/review', methods=['POST'])
    def submit_inspection_review():
        """提交审核结果"""
        session = get_db_session()
        try:
            data = request.get_json()
            if not data or 'item_id' not in data:
                return jsonify({'success': False, 'error': '缺少item_id'}), 400

            item = session.query(InspectionReview).filter_by(item_id=data['item_id']).first()

            if not item:
                return jsonify({'success': False, 'error': '检查项不存在'}), 404

            item.review_result = data.get('审核结果', item.review_result)
            if '问题描述' in data:
                item.problem_note = data['问题描述']
            item.review_time = datetime.now()

            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/review/problem', methods=['POST'])
    def update_inspection_problem():
        """更新问题描述"""
        session = get_db_session()
        try:
            data = request.get_json()
            if not data or 'item_id' not in data:
                return jsonify({'success': False, 'error': '缺少item_id'}), 400

            item = session.query(InspectionReview).filter_by(item_id=data['item_id']).first()

            if not item:
                return jsonify({'success': False, 'error': '记录不存在'}), 404

            item.problem_note = data.get('问题描述', '')
            item.review_time = datetime.now()
            session.commit()
            return jsonify({'success': True})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/stats', methods=['GET'])
    def get_inspection_stats():
        """获取审核统计"""
        session = get_db_session()
        try:
            war_zone = request.args.get('war_zone', '全部')

            # 预加载白名单
            whitelist_map = {}
            for store in session.query(StoreWhitelist).all():
                whitelist_map[store.store_id] = store.war_zone or '未分配'

            query = session.query(InspectionReview)
            if war_zone and war_zone != '全部':
                store_ids_in_zone = [sid for sid, wz in whitelist_map.items() if wz == war_zone]
                query = query.filter(InspectionReview.store_id.in_(store_ids_in_zone))

            all_items = query.all()

            # 按门店分组统计
            store_groups = {}
            for item in all_items:
                if item.store_id not in store_groups:
                    store_groups[item.store_id] = []
                store_groups[item.store_id].append(item)

            total_stores = len(store_groups)
            completed_stores = 0

            for store_id, items in store_groups.items():
                all_done = True
                for item in items:
                    if item.no_result:
                        continue
                    if not item.review_result:
                        all_done = False
                        break
                    if item.review_result == '不合格' and not (item.problem_note and item.problem_note.strip()):
                        all_done = False
                        break
                if all_done:
                    completed_stores += 1

            pct = round((completed_stores / total_stores * 100) if total_stores > 0 else 0, 1)

            return jsonify({
                'total': total_stores,
                'reviewed': completed_stores,
                'percentage': pct
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/completed', methods=['GET'])
    def get_completed_stores():
        """获取已完成门店列表"""
        session = get_db_session()
        try:
            war_zone_filter = request.args.get('war_zone', '全部')

            # 预加载白名单
            whitelist_map = {}
            for store in session.query(StoreWhitelist).all():
                whitelist_map[store.store_id] = {
                    'war_zone': store.war_zone or '未分配',
                    'regional_manager': store.regional_manager or ''
                }

            query = session.query(InspectionReview)
            if war_zone_filter and war_zone_filter != '全部':
                store_ids_in_zone = [sid for sid, info in whitelist_map.items() if info['war_zone'] == war_zone_filter]
                query = query.filter(InspectionReview.store_id.in_(store_ids_in_zone))

            all_items = query.all()

            store_groups = {}
            for item in all_items:
                if item.store_id not in store_groups:
                    wl_info = whitelist_map.get(item.store_id, {'war_zone': '未分配', 'regional_manager': ''})
                    store_groups[item.store_id] = {
                        'store_id': item.store_id,
                        'store_name': item.store_name,
                        'war_zone': wl_info['war_zone'],
                        'items': []
                    }
                store_groups[item.store_id]['items'].append(item)

            completed = []
            for store_id, store in store_groups.items():
                all_done = True
                latest_time = None
                pass_count = 0
                fail_count = 0
                visible_count = 0

                for item in store['items']:
                    if item.no_result:
                        fail_count += 1
                        continue
                    visible_count += 1
                    if not item.review_result:
                        all_done = False
                        break
                    if item.review_result == '不合格':
                        if not (item.problem_note and item.problem_note.strip()):
                            all_done = False
                            break
                        fail_count += 1
                    else:
                        pass_count += 1
                    if item.review_time and (latest_time is None or item.review_time > latest_time):
                        latest_time = item.review_time

                if all_done:
                    completed.append({
                        'store_id': store_id,
                        'store_name': store['store_name'],
                        'war_zone': store['war_zone'],
                        'pass_count': pass_count,
                        'fail_count': fail_count,
                        'total_count': pass_count + fail_count,
                        'completed_time': latest_time.strftime('%Y-%m-%d %H:%M') if latest_time else ''
                    })

            completed.sort(key=lambda x: x['completed_time'], reverse=True)
            return jsonify(completed)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/upload', methods=['POST'])
    def upload_inspection_data():
        """上传检查项Excel文件（开始新周期）- 需要密码验证"""
        try:
            # 验证密码
            password = request.form.get('password', '')
            if password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': '密码错误，无权操作'}), 401

            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '未选择文件'}), 400

            file = request.files['file']
            if file.filename == '' or not file.filename.endswith('.xlsx'):
                return jsonify({'success': False, 'error': '只支持.xlsx文件'}), 400

            import os
            filepath = os.path.join(app.config.get('UPLOAD_FOLDER', '/tmp'), 'inspection_data.xlsx')
            file.save(filepath)

            try:
                df = pd.read_excel(filepath)
                print(f"[DEBUG] Excel列名: {list(df.columns)}")
                print(f"[DEBUG] 数据行数: {len(df)}")

                # 验证必需字段
                required = ['检查项名称', '门店名称', '门店编号', '所属区域']
                missing = [f for f in required if f not in df.columns]
                if missing:
                    return jsonify({'success': False, 'error': f'缺少字段: {", ".join(missing)}'}), 400

                session = get_db_session()

                # 清空现有审核数据
                session.query(InspectionReview).delete()
                print("[DEBUG] 已清空现有数据")

                # 预加载白名单（获取战区信息）
                whitelist = {}
                for store in session.query(StoreWhitelist).all():
                    whitelist[store.store_id] = {
                        'war_zone': store.war_zone or '未分配',
                        'operator': store.temp_operator or store.city_operator or '未分配'
                    }
                print(f"[DEBUG] 白名单加载完成，共{len(whitelist)}条")

                count = 0
                auto_count = 0
                error_rows = []
                import json
                import re

                for idx, row in df.iterrows():
                    try:
                        # 安全处理门店编号
                        try:
                            if pd.notna(row['门店编号']):
                                store_id_raw = row['门店编号']
                                if isinstance(store_id_raw, float):
                                    store_id = str(int(store_id_raw))
                                else:
                                    store_id = str(store_id_raw).strip()
                            else:
                                store_id = 'unknown'
                        except:
                            store_id = str(row['门店编号']).strip() if pd.notna(row['门店编号']) else 'unknown'
                        
                        item_name = str(row['检查项名称']).strip() if pd.notna(row['检查项名称']) else 'unknown'
                        item_id = f"{store_id}_{item_name}"

                        # 解析图片URL
                        image_url = ''
                        has_result = False
                        if '现场结果' in df.columns and pd.notna(row['现场结果']):
                            result_data = str(row['现场结果']).strip()
                            try:
                                if result_data.startswith('[') and '],' in result_data:
                                    result_data = result_data[:result_data.index('],') + 1]
                                urls = json.loads(result_data)
                                if isinstance(urls, list) and len(urls) > 0:
                                    first = urls[0]
                                    if isinstance(first, str):
                                        if first.strip().startswith('<img'):
                                            m = re.search(r'src="([^"]+)"', first)
                                            if m:
                                                image_url = m.group(1)
                                                has_result = True
                                        else:
                                            image_url = first
                                            has_result = True
                            except (json.JSONDecodeError, ValueError):
                                if result_data and result_data != 'nan':
                                    if result_data.startswith('<img'):
                                        m = re.search(r'src="([^"]+)"', result_data)
                                        if m:
                                            image_url = m.group(1)
                                            has_result = True
                                    else:
                                        image_url = result_data
                                        has_result = True

                        wl_info = whitelist.get(store_id, {'war_zone': '未分配', 'operator': '未分配'})

                        review = InspectionReview(
                            item_id=item_id,
                            store_name=str(row['门店名称']) if pd.notna(row['门店名称']) else '',
                            store_id=store_id,
                            area=str(row['所属区域']) if pd.notna(row['所属区域']) else '',
                            item_name=item_name,
                            item_category=str(row['检查项分类']) if '检查项分类' in df.columns and pd.notna(row['检查项分类']) else None,
                            image_url=image_url,
                            no_result=0 if has_result else 1,
                            operator=wl_info['operator']
                        )

                        # 自动标记无现场结果的为不合格
                        if not has_result:
                            review.review_result = '不合格'
                            review.problem_note = '无现场结果'
                            review.review_time = datetime.now()
                            auto_count += 1

                        session.add(review)
                        count += 1
                    except Exception as row_err:
                        error_rows.append(f"行{idx+2}: {str(row_err)}")
                        if len(error_rows) <= 3:
                            print(f"[DEBUG] 行{idx+2}处理失败: {row_err}")

                if error_rows:
                    print(f"[DEBUG] 共{len(error_rows)}行处理失败")

                session.commit()
                print(f"[DEBUG] 提交成功，共{count}条")

                return jsonify({
                    'success': True,
                    'message': f'导入成功，共{count}条检查项，自动标记{auto_count}条无现场结果',
                    'total_items': count,
                    'auto_reviewed': auto_count,
                    'errors': error_rows[:5] if error_rows else []
                })

            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)

        except Exception as e:
            import traceback
            print(f"[ERROR] 上传失败: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/inspection/export', methods=['GET'])
    def export_inspection_csv():
        """导出审核结果CSV"""
        try:
            from flask import Response
            from urllib.parse import quote
            import csv
            from io import StringIO

            session = get_db_session()
            reviews = session.query(InspectionReview)\
                .filter(InspectionReview.review_result.isnot(None))\
                .filter(InspectionReview.review_result != '')\
                .order_by(InspectionReview.store_id)\
                .all()

            if not reviews:
                return jsonify({'error': '暂无审核结果可导出'}), 400

            # 预加载白名单获取地理信息
            whitelist = {}
            for store in session.query(StoreWhitelist).all():
                whitelist[store.store_id] = {
                    'war_zone': store.war_zone or '',
                    'province': store.province or '',
                    'city': store.city or ''
                }

            output = StringIO()
            fieldnames = ['门店名称', '门店编号', '战区', '省份', '城市', '所属区域',
                          '检查项名称', '负责运营', '标准图', '审核结果', '问题描述', '审核时间']
            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()

            for r in reviews:
                loc = whitelist.get(r.store_id, {'war_zone': '', 'province': '', 'city': ''})
                writer.writerow({
                    '门店名称': r.store_name,
                    '门店编号': r.store_id,
                    '战区': loc['war_zone'],
                    '省份': loc['province'],
                    '城市': loc['city'],
                    '所属区域': r.area or '',
                    '检查项名称': r.item_name,
                    '负责运营': r.operator or '',
                    '标准图': r.image_url or '',
                    '审核结果': r.review_result or '',
                    '问题描述': r.problem_note or '',
                    '审核时间': r.review_time.strftime('%Y-%m-%d %H:%M:%S') if r.review_time else ''
                })

            csv_content = '\ufeff' + output.getvalue()
            output.close()

            filename = f'审核结果_{datetime.now().strftime("%Y-%m-%d")}.csv'
            filename_encoded = quote(filename)

            return Response(
                csv_content,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f"attachment; filename*=UTF-8''{filename_encoded}",
                    'Content-Type': 'text/csv; charset=utf-8'
                }
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/reset', methods=['POST'])
    def reset_inspection_data():
        """重置所有审核数据（清空表）- 需要密码验证"""
        session = get_db_session()
        try:
            data = request.get_json()
            password = data.get('password', '')
            if password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': '密码错误，无权操作'}), 401

            count = session.query(InspectionReview).count()
            session.query(InspectionReview).delete()
            session.commit()

            return jsonify({
                'success': True,
                'message': f'已清空{count}条检查项数据'
            })
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/inspection/sync-to-viewer', methods=['POST'])
    def sync_to_viewer():
        """将审核结果同步到展示系统（viewer_review_results表）"""
        session = get_db_session()
        try:
            from shared.database_models import ViewerReviewResult

            # 获取所有已审核的记录
            reviews = session.query(InspectionReview)\
                .filter(InspectionReview.review_result.isnot(None))\
                .filter(InspectionReview.review_result != '')\
                .all()

            if not reviews:
                return jsonify({'success': False, 'error': '暂无审核结果可同步'}), 400

            # 预加载白名单
            whitelist = {}
            for store in session.query(StoreWhitelist).all():
                whitelist[store.store_id] = store

            # 清空viewer表并写入
            session.query(ViewerReviewResult).delete()

            count = 0
            for r in reviews:
                wl = whitelist.get(r.store_id)
                result = ViewerReviewResult(
                    store_name=r.store_name,
                    store_id=r.store_id,
                    war_zone=wl.war_zone if wl else '[未匹配]',
                    province=wl.province if wl else '[未匹配]',
                    city=wl.city if wl else '[未匹配]',
                    area=r.area,
                    item_name=r.item_name,
                    item_category=r.item_category,
                    image_url=r.image_url,
                    review_result=r.review_result,
                    problem_note=r.problem_note,
                    review_time=r.review_time,
                    import_time=datetime.now()
                )
                session.add(result)
                count += 1

            session.commit()
            return jsonify({
                'success': True,
                'message': f'已同步{count}条审核结果到展示系统',
                'synced_count': count
            })
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()
