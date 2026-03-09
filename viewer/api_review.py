"""
周清审核相关API
Review Related APIs
"""
from flask import request, jsonify
from sqlalchemy import func, distinct
from shared.database_models import StoreWhitelist, ViewerReviewResult


def register_review_routes(app, get_db_session):
    """注册周清审核相关路由"""
    
    @app.route('/api/filters')
    def get_filters():
        """获取所有筛选选项"""
        try:
            session = get_db_session()
            
            # 获取战区列表
            war_zones = session.query(StoreWhitelist.war_zone)\
                .filter(StoreWhitelist.war_zone.isnot(None))\
                .filter(StoreWhitelist.war_zone != '')\
                .distinct()\
                .order_by(StoreWhitelist.war_zone)\
                .all()
            war_zones = [wz[0] for wz in war_zones]
            
            # 获取省份列表
            provinces = session.query(StoreWhitelist.province)\
                .filter(StoreWhitelist.province.isnot(None))\
                .filter(StoreWhitelist.province != '')\
                .distinct()\
                .order_by(StoreWhitelist.province)\
                .all()
            provinces = [p[0] for p in provinces]
            
            # 获取城市列表
            cities = session.query(StoreWhitelist.city)\
                .filter(StoreWhitelist.city.isnot(None))\
                .filter(StoreWhitelist.city != '')\
                .distinct()\
                .order_by(StoreWhitelist.city)\
                .all()
            cities = [c[0] for c in cities]
            
            # 获取区域经理列表
            regional_managers = session.query(StoreWhitelist.regional_manager)\
                .filter(StoreWhitelist.regional_manager.isnot(None))\
                .filter(StoreWhitelist.regional_manager != '')\
                .distinct()\
                .order_by(StoreWhitelist.regional_manager)\
                .all()
            regional_managers = [rm[0] for rm in regional_managers]
            
            # 获取运营列表
            operators_query = session.query(
                func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator).label('operator')
            ).filter(
                func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator).isnot(None)
            ).filter(
                func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator) != ''
            ).distinct().order_by('operator')
            
            operators = [op[0] for op in operators_query.all()]
            
            # 审核结果选项
            review_results = ['合格', '不合格']
            
            return jsonify({
                'success': True,
                'data': {
                    'war_zones': war_zones,
                    'provinces': provinces,
                    'cities': cities,
                    'regional_managers': regional_managers,
                    'operators': operators,
                    'review_results': review_results
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取筛选选项失败: {str(e)}'
            }), 500

    @app.route('/api/filters/provinces')
    def get_provinces_by_war_zone():
        """根据战区获取省份列表"""
        try:
            war_zone = request.args.get('war_zone', '')
            
            if not war_zone:
                return jsonify({
                    'success': False,
                    'error': '缺少战区参数'
                }), 400
            
            session = get_db_session()
            
            provinces = session.query(StoreWhitelist.province)\
                .filter(StoreWhitelist.war_zone == war_zone)\
                .filter(StoreWhitelist.province.isnot(None))\
                .filter(StoreWhitelist.province != '')\
                .distinct()\
                .order_by(StoreWhitelist.province)\
                .all()
            provinces = [p[0] for p in provinces]
            
            return jsonify({
                'success': True,
                'data': {
                    'provinces': provinces
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取省份列表失败: {str(e)}'
            }), 500

    @app.route('/api/filters/cities')
    def get_cities_by_province():
        """根据省份获取城市列表"""
        try:
            province = request.args.get('province', '')
            
            if not province:
                return jsonify({
                    'success': False,
                    'error': '缺少省份参数'
                }), 400
            
            session = get_db_session()
            
            cities = session.query(StoreWhitelist.city)\
                .filter(StoreWhitelist.province == province)\
                .filter(StoreWhitelist.city.isnot(None))\
                .filter(StoreWhitelist.city != '')\
                .distinct()\
                .order_by(StoreWhitelist.city)\
                .all()
            cities = [c[0] for c in cities]
            
            return jsonify({
                'success': True,
                'data': {
                    'cities': cities
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取城市列表失败: {str(e)}'
            }), 500

    @app.route('/api/search')
    def search_reviews():
        """搜索审核结果"""
        try:
            session = get_db_session()
            
            # 获取筛选参数
            war_zone = request.args.get('war_zone', '').strip()
            province = request.args.get('province', '').strip()
            city = request.args.get('city', '').strip()
            regional_manager = request.args.get('regional_manager', '').strip()
            operator = request.args.get('operator', '').strip()
            review_result = request.args.get('review_result', '').strip()
            store_search = request.args.get('store_search', '').strip()
            
            # 获取分页参数
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # 构建查询
            store_query = session.query(distinct(ViewerReviewResult.store_id))
            
            # 门店搜索
            if store_search:
                store_query = store_query.filter(
                    (ViewerReviewResult.store_id == store_search) |
                    (ViewerReviewResult.store_name.like(f'%{store_search}%'))
                )
            
            # 应用筛选条件
            if war_zone:
                store_query = store_query.filter(ViewerReviewResult.war_zone == war_zone)
            if province:
                store_query = store_query.filter(ViewerReviewResult.province == province)
            if city:
                store_query = store_query.filter(ViewerReviewResult.city == city)
            
            # 只显示不合格的
            store_query = store_query.filter(ViewerReviewResult.review_result == '不合格')
            
            # 如果有区域经理或运营筛选
            if regional_manager or operator:
                store_query = store_query.join(
                    StoreWhitelist,
                    ViewerReviewResult.store_id == StoreWhitelist.store_id
                )
                if regional_manager:
                    store_query = store_query.filter(StoreWhitelist.regional_manager == regional_manager)
                if operator:
                    store_query = store_query.filter(
                        func.coalesce(StoreWhitelist.temp_operator, StoreWhitelist.city_operator) == operator
                    )
            
            # 获取总门店数
            total_stores = store_query.count()
            
            # 分页获取门店ID
            store_ids = [sid[0] for sid in store_query.limit(per_page).offset((page - 1) * per_page).all()]
            
            # 获取这些门店的所有不合格项
            results = session.query(ViewerReviewResult)\
                .filter(ViewerReviewResult.store_id.in_(store_ids))\
                .filter(ViewerReviewResult.review_result == '不合格')\
                .order_by(ViewerReviewResult.store_id, ViewerReviewResult.id)\
                .all()
            
            # 按门店分组
            stores_data = {}
            for result in results:
                if result.store_id not in stores_data:
                    stores_data[result.store_id] = {
                        'store_id': result.store_id,
                        'store_name': result.store_name,
                        'war_zone': result.war_zone,
                        'province': result.province,
                        'city': result.city,
                        'items': []
                    }
                stores_data[result.store_id]['items'].append(result.to_dict())
            
            stores_list = list(stores_data.values())
            total_pages = (total_stores + per_page - 1) // per_page
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': stores_list,
                    'total_stores': total_stores,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'has_more': page < total_pages
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'搜索失败: {str(e)}'
            }), 500

    @app.route('/api/unmatched-stores')
    def get_unmatched_stores():
        """获取所有未匹配的门店列表"""
        try:
            session = get_db_session()
            
            unmatched_results = session.query(ViewerReviewResult)\
                .filter(
                    (ViewerReviewResult.war_zone == "[未匹配]") |
                    (ViewerReviewResult.province == "[未匹配]") |
                    (ViewerReviewResult.city == "[未匹配]")
                )\
                .order_by(ViewerReviewResult.store_id, ViewerReviewResult.id)\
                .all()
            
            # 按门店ID分组统计
            stores_dict = {}
            for result in unmatched_results:
                if result.store_id not in stores_dict:
                    stores_dict[result.store_id] = {
                        'store_id': result.store_id,
                        'store_name': result.store_name,
                        'war_zone': result.war_zone,
                        'province': result.province,
                        'city': result.city,
                        'items_count': 0,
                        'items': []
                    }
                
                stores_dict[result.store_id]['items_count'] += 1
                stores_dict[result.store_id]['items'].append({
                    'item_name': result.item_name,
                    'review_result': result.review_result,
                    'review_time': result.review_time.strftime('%Y-%m-%d %H:%M:%S') if result.review_time else ''
                })
            
            stores_list = list(stores_dict.values())
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': stores_list,
                    'total_stores': len(stores_list),
                    'total_items': len(unmatched_results)
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取未匹配门店失败: {str(e)}'
            }), 500
