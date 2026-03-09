"""
活动参与度相关API
Promo Participation Related APIs
"""
from flask import request, jsonify, send_file
from datetime import datetime
import pandas as pd
from io import BytesIO
from shared.database_models import PromoParticipation, PromoImportLog


def register_promo_routes(app, get_db_session):
    """注册活动参与度相关路由"""
    
    @app.route('/api/promo/filters')
    def get_promo_filters():
        """获取活动参与度筛选选项"""
        try:
            session = get_db_session()
            
            war_zones = session.query(PromoParticipation.war_zone)\
                .filter(PromoParticipation.war_zone.isnot(None))\
                .filter(PromoParticipation.war_zone != '')\
                .distinct()\
                .order_by(PromoParticipation.war_zone)\
                .all()
            war_zones = [wz[0] for wz in war_zones]
            
            latest_log = session.query(PromoImportLog)\
                .order_by(PromoImportLog.import_time.desc())\
                .first()
            
            data_date = latest_log.data_date if latest_log and latest_log.data_date else None
            
            return jsonify({
                'success': True,
                'data': {
                    'war_zones': war_zones,
                    'data_date': data_date
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'获取筛选选项失败: {str(e)}'
            }), 500

    @app.route('/api/promo/regional-managers')
    def get_promo_regional_managers():
        """根据战区获取区域经理列表"""
        try:
            session = get_db_session()
            
            war_zone = request.args.get('war_zone', '').strip()
            
            if not war_zone:
                return jsonify({
                    'success': False,
                    'error': '缺少战区参数'
                }), 400
            
            regional_managers = session.query(PromoParticipation.regional_manager)\
                .filter(PromoParticipation.war_zone == war_zone)\
                .filter(PromoParticipation.regional_manager.isnot(None))\
                .filter(PromoParticipation.regional_manager != '')\
                .distinct()\
                .order_by(PromoParticipation.regional_manager)\
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

    @app.route('/api/promo/all-regional-managers')
    def get_all_promo_regional_managers():
        """获取所有区域经理列表"""
        try:
            session = get_db_session()
            
            regional_managers = session.query(PromoParticipation.regional_manager)\
                .filter(PromoParticipation.regional_manager.isnot(None))\
                .filter(PromoParticipation.regional_manager != '')\
                .distinct()\
                .order_by(PromoParticipation.regional_manager)\
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

    @app.route('/api/promo/search')
    def search_promo():
        """搜索活动参与度数据"""
        try:
            session = get_db_session()
            
            war_zone = request.args.get('war_zone', '').strip()
            regional_manager = request.args.get('regional_manager', '').strip()
            store_search = request.args.get('store_search', '').strip()
            sort_by = request.args.get('sort_by', 'participation_rate').strip()
            sort_order = request.args.get('sort_order', 'desc').strip()
            
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
            if regional_manager:
                query = query.filter(PromoParticipation.regional_manager == regional_manager)
            
            total = query.count()
            
            # 排序
            if sort_by == 'participation_rate':
                all_records = query.all()
                
                def parse_rate(rate_str):
                    try:
                        return float(rate_str.replace('%', ''))
                    except:
                        return 0.0
                
                all_records.sort(key=lambda x: parse_rate(x.participation_rate), reverse=(sort_order == 'desc'))
                
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                records = all_records[start_idx:end_idx]
                
            elif sort_by == 'order_count':
                if sort_order == 'desc':
                    query = query.order_by(PromoParticipation.order_count.desc())
                else:
                    query = query.order_by(PromoParticipation.order_count.asc())
                records = query.limit(per_page).offset((page - 1) * per_page).all()
                
            elif sort_by == 'benefit_card_sales':
                if sort_order == 'desc':
                    query = query.order_by(PromoParticipation.benefit_card_sales.desc())
                else:
                    query = query.order_by(PromoParticipation.benefit_card_sales.asc())
                records = query.limit(per_page).offset((page - 1) * per_page).all()
                
            elif sort_by == 'promo_package_sales':
                if sort_order == 'desc':
                    query = query.order_by(PromoParticipation.promo_package_sales.desc())
                else:
                    query = query.order_by(PromoParticipation.promo_package_sales.asc())
                records = query.limit(per_page).offset((page - 1) * per_page).all()
            else:
                query = query.order_by(PromoParticipation.store_id)
                records = query.limit(per_page).offset((page - 1) * per_page).all()
            
            stores_list = [record.to_dict() for record in records]
            
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            
            return jsonify({
                'success': True,
                'data': {
                    'stores': stores_list,
                    'total': total,
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

    @app.route('/api/promo/export')
    def export_promo():
        """导出活动参与度数据"""
        try:
            session = get_db_session()
            
            records = session.query(PromoParticipation)\
                .order_by(PromoParticipation.store_id)\
                .all()
            
            if not records:
                return jsonify({
                    'success': False,
                    'error': '暂无数据可导出'
                }), 400
            
            export_data = []
            for record in records:
                export_data.append({
                    '门店ID': record.store_id,
                    '门店名称': record.store_name,
                    '战区': record.war_zone,
                    '区域经理': record.regional_manager,
                    '订单量': record.order_count,
                    '权益卡销量': record.benefit_card_sales,
                    '活动套餐销量': record.promo_package_sales,
                    '活动参与度': record.participation_rate,
                    '数据日期': record.data_date
                })
            
            df = pd.DataFrame(export_data)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='活动参与度')
                
                worksheet = writer.sheets['活动参与度']
                worksheet.column_dimensions['A'].width = 12
                worksheet.column_dimensions['B'].width = 25
                worksheet.column_dimensions['C'].width = 10
                worksheet.column_dimensions['D'].width = 12
                worksheet.column_dimensions['E'].width = 12
                worksheet.column_dimensions['F'].width = 15
                worksheet.column_dimensions['G'].width = 15
                worksheet.column_dimensions['H'].width = 15
                worksheet.column_dimensions['I'].width = 15
            
            output.seek(0)
            
            filename = f'活动参与度_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            
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
