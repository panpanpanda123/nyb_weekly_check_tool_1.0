"""
门店评级功能数据库初始化脚本
Initialize Database for Store Rating Feature
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import (
    create_db_engine,
    init_viewer_db,
    StoreRating,
    StoreOperationData
)
from viewer.data_importer import DataImporter
from sqlalchemy.orm import sessionmaker


def init_rating_tables():
    """初始化门店评级相关的数据库表"""
    print("=" * 60)
    print("门店评级功能数据库初始化")
    print("=" * 60)
    
    # 创建数据库引擎
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
    )
    
    print(f"\n📊 连接数据库: {DATABASE_URL}")
    engine = create_db_engine(DATABASE_URL, echo=False)
    
    # 初始化数据库表
    print("\n🔧 创建数据库表...")
    init_viewer_db(engine)
    
    print("\n✅ 数据库表创建完成！")
    print("\n新增表：")
    print(f"  - {StoreRating.__tablename__} (门店评级表)")
    print(f"  - {StoreOperationData.__tablename__} (门店运营数据表)")
    
    return engine


def load_operation_data(engine, excel_file: str = 'store_rank/whitelist.xlsx'):
    """加载门店运营数据"""
    if not os.path.exists(excel_file):
        print(f"\n⚠️  未找到运营数据文件: {excel_file}")
        print("   请确保文件存在后再运行数据导入")
        return
    
    print(f"\n📥 加载运营数据: {excel_file}")
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 导入运营数据
        importer = DataImporter(session)
        result = importer.import_operation_data(excel_file, sheet_name='Sheet2')
        
        if result.success:
            print(f"✅ 运营数据导入成功，共导入 {result.records_count} 条记录")
        else:
            print(f"❌ 运营数据导入失败: {result.error_message}")
    
    except Exception as e:
        print(f"❌ 导入运营数据时发生错误: {str(e)}")
    
    finally:
        session.close()


if __name__ == '__main__':
    try:
        # 初始化数据库表
        engine = init_rating_tables()
        
        # 加载运营数据
        load_operation_data(engine)
        
        print("\n" + "=" * 60)
        print("✅ 门店评级功能数据库初始化完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
