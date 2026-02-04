"""
导出门店数据到JSON文件
Export Store Data to JSON File
"""
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database_models import StoreWhitelist, StoreOperationData

# 数据库配置
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops"

# 输出目录
OUTPUT_DIR = Path('rating_data')
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / 'stores.json'


def export_stores():
    """导出门店数据"""
    print("=" * 60)
    print("导出门店数据到JSON文件")
    print("=" * 60)
    
    # 连接数据库
    print(f"\n📊 连接数据库: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 查询所有门店
        print("\n📥 查询门店数据...")
        stores = session.query(StoreWhitelist).all()
        
        # 查询运营数据
        operation_data_dict = {}
        operation_data_list = session.query(StoreOperationData).all()
        for op_data in operation_data_list:
            operation_data_dict[op_data.store_id] = op_data
        
        # 转换为JSON格式
        stores_json = []
        for store in stores:
            op_data = operation_data_dict.get(store.store_id)
            
            store_dict = {
                'store_id': store.store_id,
                'store_name': store.store_name,
                'city': store.city,
                'war_zone': store.war_zone,
                'regional_manager': store.regional_manager,
                'dine_in_revenue': float(op_data.dine_in_revenue) if op_data and op_data.dine_in_revenue else None
            }
            stores_json.append(store_dict)
        
        # 保存到文件
        print(f"\n💾 保存到文件: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(stores_json, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 成功导出 {len(stores_json)} 家门店数据")
        print(f"📁 文件路径: {OUTPUT_FILE.absolute()}")
        
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        raise
    finally:
        session.close()
    
    print("\n" + "=" * 60)
    print("✅ 导出完成！")
    print("=" * 60)


if __name__ == '__main__':
    export_stores()
