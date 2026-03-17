"""
活动参与度相关API（新版）
"""
from flask import request, jsonify, send_file
from datetime import datetime
from sqlalchemy import func, desc, asc
import pandas as pd
from io import BytesIO
from shared.database_models import PromoParticipation, PromoImportLog


def register_promo_routes(app, get_db_session):
    """注册活动参与度相关路由"""

    @app.route('/api/promo/filters')
    def get_promo_filters():
        """获取筛选选项"""
        try:
            session = get_db_session()

            war_zones = [r[0] for r in session.query(PromoParticipation.war_zone)
                .filter(PromoParticipation.war_zone.isnot(None), PromoParticipation.war_zone != '')
                .distinct().order_by(PromoParticipation.war_zone).all()]

            war_zone_managers = [r[0] for r in session.query(PromoParticipation.war_zone_manager)
                .filter(PromoParticipation.war_zone_manager.isnot(None), PromoParticipation.war_zone_manager != '')
                .distinct().order_by(PromoParticipation.war_zone_manager).all()]

            city_operators = [r[0] for r in session.query(PromoParticipation.city_operator)
                .filter(PromoParticipation.city_operator.isnot(None), PromoParticipation.city_operator != '')
                .distinct().order_by(PromoParticipation.city_operator).all()]

            latest_log = session.query(PromoImportLog)\
                .order_by(PromoImportLog.import_time.desc()).first()
            data_date = latest_log.data_date if latest_log else None

            return jsonify({
                'success': True,
                'data': {
                    'war_zones': war_zones,
                    'war_zone_managers': war_zone_managers,
                    'city_operators': city_operators,
                    'data_date': data_date,
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/promo/regional-managers')
    def get_promo_regional_managers():
        """根据筛选条件获取区域经理列表"""
        try:
            session = get_db_session()
            query = session.query(PromoParticipation.regional_manager)\
                .filter(PromoParticipation.regional_manager.isnot(None),
                        PromoParticipation.regional_manager != '')

            war_zone = request.args.get('war_zone', '').strip()
            war_zone_manager = request.args.get('war_zone_manager', '').strip()
            if war_zone:
                query = query.filter(PromoParticipation.war_zone == war_zone)
            if war_zone_manager:
                query = query.filter(PromoParticipation.war_zone_manager == war_zone_manager)

            managers = [r[0] for r in query.distinct().order_by(PromoParticipation.regional_manager).all()]
            return jsonify({'success': True, 'data': {'regional_managers': managers}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/promo/all-regional-managers')
    def get_all_promo_regional_managers():
        """获取所有区域经理列表"""
        try:
            session = get_db_session()
            managers = [r[0] for r in session.query(PromoParticipation.regional_manager)
                .filter(PromoParticipation.regional_manager.isnot(None),
                        PromoParticipation.regional_manager != '')
                .distinct().order_by(PromoParticipation.regional_manager).all()]
            return jsonify({'success': True, 'data': {'regional_managers': managers}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/promo/overview')
    def get_promo_overview():
        """获取概览排名数据（按战区、战区经理、区域经理）"""
        try:
            session = get_db_session()

            def _rank(group_col):
                rows = session.query(
                    group_col,
                    func.avg(PromoParticipation.participation_rate).label('avg_rate'),
                    func.sum(PromoParticipation.order_count).label('total_orders'),
                    func.count(PromoParticipation.store_id).label('store_count'),
                ).filter(group_col.isnot(None), group_col != '')\
                 .group_by(group_col)\
                 .order_by(asc('avg_rate')).all()
                return [{
                    'name': r[0],
                    'avg_rate': round(float(r[1]), 4) if r[1] else 0,
                    'total_orders': int(r[2]) if r[2] else 0,
                    'store_count': int(r[3]) if r[3] else 0,
                } for r in rows]

            # 全局平均
            global_avg = session.query(func.avg(PromoParticipation.participation_rate)).scalar()
            total_stores = session.query(func.count(PromoParticipation.store_id)).scalar()

            return jsonify({
                'success': True,
                'data': {
                    'global_avg': round(float(global_avg), 4) if global_avg else 0,
                    'total_stores': total_stores or 0,
                    'by_war_zone': _rank(PromoParticipation.war_zone),
                    'by_war_zone_manager': _rank(PromoParticipation.war_zone_manager),
                    'by_regional_manager': _rank(PromoParticipation.regional_manager),
                    'by_city_operator': _rank(PromoParticipation.city_operator),
                }
            })
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/promo/search')
    def search_promo():
        """搜索门店明细"""
        try:
            session = get_db_session()

            war_zone = request.args.get('war_zone', '').strip()
            war_zone_manager = request.args.get('war_zone_manager', '').strip()
            regional_manager = request.args.get('regional_manager', '').strip()
            city_operator = request.args.get('city_operator', '').strip()
            store_search = request.args.get('store_search', '').strip()
            sort_by = request.args.get('sort_by', 'participation_rate').strip()
            sort_order = request.args.get('sort_order', 'asc').strip()
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))

            query = session.query(PromoParticipation)

            if store_search:
                query = query.filter(
                    (PromoParticipation.store_id == store_search) |
                    (PromoParticipation.store_name.like(f'%{store_search}%'))
                )
            if war_zone:
                query = query.filter(PromoParticipation.war_zone == war_zone)
            if war_zone_manager:
                query = query.filter(PromoParticipation.war_zone_manager == war_zone_manager)
            if regional_manager:
                query = query.filter(PromoParticipation.regional_manager == regional_manager)
            if city_operator:
                query = query.filter(PromoParticipation.city_operator == city_operator)

            total = query.count()

            # 排序
            sort_col_map = {
                'participation_rate': PromoParticipation.participation_rate,
                'order_count': PromoParticipation.order_count,
                'benefit_card_sales': PromoParticipation.benefit_card_sales,
                'promo_package_sales': PromoParticipation.promo_package_sales,
            }
            sort_col = sort_col_map.get(sort_by, PromoParticipation.participation_rate)
            if sort_order == 'desc':
                query = query.order_by(desc(sort_col))
            else:
                query = query.order_by(asc(sort_col))

            records = query.limit(per_page).offset((page - 1) * per_page).all()
            stores_list = [r.to_dict() for r in records]
            total_pages = max(1, (total + per_page - 1) // per_page)

            return jsonify({
                'success': True,
                'data': {
                    'stores': stores_list,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'has_more': page < total_pages,
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/promo/export')
    def export_promo():
        """导出数据"""
        try:
            session = get_db_session()
            records = session.query(PromoParticipation)\
                .order_by(PromoParticipation.participation_rate.asc()).all()

            if not records:
                return jsonify({'success': False, 'error': '暂无数据'}), 400

            data = [{
                '门店ID': r.store_id,
                '门店名称': r.store_name,
                '省市运营': r.city_operator,
                '战区': r.war_zone,
                '战区经理': r.war_zone_manager,
                '区域经理': r.regional_manager,
                '堂食订单量': r.order_count,
                'POS订单量': r.pos_order_count,
                '扫码订单量': r.scan_order_count,
                '权益卡销量': r.benefit_card_sales,
                '活动套餐销量': r.promo_package_sales,
                '活动参与度': f'{(r.participation_rate or 0) * 100:.1f}%',
                '数据区间': r.data_date,
            } for r in records]

            df = pd.DataFrame(data)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='活动参与度')
            output.seek(0)

            filename = f'活动参与度_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename,
            )
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
