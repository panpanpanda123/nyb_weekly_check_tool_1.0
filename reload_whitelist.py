"""
重新加载白名单数据（包含区域经理字段）
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import create_db_engine, create_session_factory
from viewer.data_importer import DataImporter

def reload_whitelist(excel_file: str = 'store_rank/whitelist.xlsx'):
    """重新加载白名单数据"""
    if not os.path.exists(excel_file):
        print(f"❌ 未找到白名单文件: {excel_file}")
        return
    
    print("=" * 60)
    print("重新加载白名单数据")
    print("=" * 60)
    
    # 创建数据库引擎
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
    )
    
    print(f"\n📊 连接数据库: {DATABASE_URL}")
    engine = create_db_engine(DATABASE_URL, echo=False)
    
    # 创建会话
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        print(f"\n📥 加载白名单: {excel_file}")
        
        # 导入白名单
        importer = DataImporter(session)
        result = importer.import_whitelist(excel_file)
        
        if result.success:
            print(f"✅ 白名单导入成功，共导入 {result.records_count} 条记录")
        else:
            print(f"❌ 白名单导入失败: {result.error_message}")
    
    except Exception as e:
        print(f"❌ 导入白名单时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()
    
    print("\n" + "=" * 60)
    print("✅ 白名单重新加载完成！")
    print("=" * 60)


if __name__ == '__main__':
    reload_whitelist()
