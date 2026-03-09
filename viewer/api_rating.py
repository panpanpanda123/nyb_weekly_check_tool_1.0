"""
门店评级相关API
Store Rating Related APIs
"""
from flask import request, jsonify, Response
from datetime import datetime
import io
import csv
from urllib.parse import quote
from sqlalchemy import func
from shared.database_models import StoreWhitelist, StoreRating, StoreOperationData


def register_rating_routes(app, get_db_session):
    """注册门店评级相关路由"""
    
    @app.route('/api/rating/war-zones')
    def get_rating_war_zones():
        """获取战区列表"""
        try:
            session = get_db_session()
            
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
        """获取区域经理列表"""
        try:
            session = get_db_session()
            war_zone = request.args.get('war_zone', '').strip()
            
            query = session.query(StoreWhitelist.regional_manager)\
                .filter(StoreWhitelist.regional_manager.isnot(None))\
                .filter(StoreWhitelist.regional_manager != '')
            
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
        """获取门店列表"""
        try:
            session = get_db_session()
            
            war_zone = request.args.get('war_zone', '').strip()
            regional_manager = request.args.get('regional_manager', '').strip()
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 5))
            
            query = session.query(StoreWhitelist)
            
            if war_zone:
                query = query.filter(StoreWhitelist.war_zone == war_zone)
            
            if regional_manager:
                query = query.filter(StoreWhitelist.regional_manager == regional_manager)
            
            total = query.count()
            
            stores = query.order_by(StoreWhitelist.store_id)\
                .limit(per_page)\
                .offset((page - 1) * per_page)\
                .all()
            
            stores_data = []
            for store in stores:
                operation_data = session.query(StoreOperationData)\
                    .filter(StoreOperationData.store_id == store.store_id)\
                    .first()
                
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
        """提交门店评级"""
        try:
            data = request.get_json()
            
            if not data or 'store_id' not in data or 'rating' not in data:
                return jsonify({
                    'success': False,
                    'error': '缺少必需字段：store_id 或 rating'
                }), 400
            
            store_id = data['store_id']
            rating = data['rating']
            
            if rating not in ['A', 'B', 'C']:
                return jsonify({
                    'success': False,
                    'error': '无效的评级值，只允许 A、B、C'
                }), 400
            
            session = get_db_session()
            store = session.query(StoreWhitelist)\
                .filter(StoreWhitelist.store_id == store_id)\
                .first()
            
            if not store:
                return jsonify({
                    'success': False,
                    'error': '门店不存在'
                }), 404
            
            new_rating = StoreRating(
                store_id=store_id,
                rating=rating,
                rated_at=datetime.now(),
                rated_by=None
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
        """获取评级完成率统计"""
        try:
            session = get_db_session()
            
            war_zone = request.args.get('war_zone', '').strip()
            regional_manager = request.args.get('regional_manager', '').strip()
            
            store_query = session.query(StoreWhitelist)
            
            if war_zone:
                store_query = store_query.filter(StoreWhitelist.war_zone == war_zone)
            
            if regional_manager:
                store_query = store_query.filter(StoreWhitelist.regional_manager == regional_manager)
            
            stores_by_zone = {}
            for store in store_query.all():
                zone = store.war_zone or '未知战区'
                if zone not in stores_by_zone:
                    stores_by_zone[zone] = []
                stores_by_zone[zone].append(store.store_id)
            
            stats = []
            for zone, store_ids in stores_by_zone.items():
                total_stores = len(store_ids)
                
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
        """导出评级结果"""
        try:
            session = get_db_session()
            
            subquery = session.query(
                StoreRating.store_id,
                func.max(StoreRating.rated_at).label('max_rated_at')
            ).group_by(StoreRating.store_id).subquery()
            
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
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['门店ID', '门店名称', '城市', '战区', '区域经理', '评级', '评级时间'])
            
            for rating in ratings:
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
            
            filename = f'门店评级结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            filename_encoded = quote(filename)
            
            response = Response(
                '\ufeff' + output.getvalue(),
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
