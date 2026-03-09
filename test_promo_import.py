#!/usr/bin/env python3
"""
活动参与度数据导入测试脚本
Test Promo Data Import
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import create_db_engine, create_session_factory, PromoParticipation
import os

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

def test_promo_data():
    """测试活动参与度数据"""
    print("="*60)
    print("活动参与度数据测试")
    print("="*60)
    
    # 创建数据库引擎
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        # 查询总数
        total = session.query(PromoParticipation).count()
        print(f"\n✓ 数据总数: {total} 条")
        
        if total == 0:
            print("\n⚠️  数据库中没有数据，请先运行导入脚本：")
            print("   python3 import_promo_data.py")
            return
        
        # 查询前5条数据
        print("\n前5条数据：")
        print("-"*60)
        records = session.query(PromoParticipation).limit(5).all()
        
        for i, record in enumerate(records, 1):
            print(f"\n{i}. 门店ID: {record.store_id}")
            print(f"   门店名称: {record.store_name}")
            print(f"   战区: {record.war_zone}")
            print(f"   区域经理: {record.regional_manager}")
            print(f"   订单量: {record.order_count}")
            print(f"   权益卡销量: {record.benefit_card_sales}")
            print(f"   活动套餐销量: {record.promo_package_sales}")
            print(f"   活动参与度: {record.participation_rate}")
            print(f"   数据日期: {record.data_date}")
        
        # 统计各战区数量
        print("\n" + "="*60)
        print("各战区门店数量：")
        print("-"*60)
        
        from sqlalchemy import func
        war_zone_stats = session.query(
            PromoParticipation.war_zone,
            func.count(PromoParticipation.id).label('count')
        ).group_by(PromoParticipation.war_zone).all()
        
        for zone, count in war_zone_stats:
            print(f"  {zone or '未知'}: {count} 个门店")
        
        # 统计各区域经理数量
        print("\n" + "="*60)
        print("各区域经理门店数量：")
        print("-"*60)
        
        manager_stats = session.query(
            PromoParticipation.regional_manager,
            func.count(PromoParticipation.id).label('count')
        ).group_by(PromoParticipation.regional_manager).all()
        
        for manager, count in manager_stats:
            print(f"  {manager or '未知'}: {count} 个门店")
        
        print("\n" + "="*60)
        print("✓ 测试完成")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    test_promo_data()
