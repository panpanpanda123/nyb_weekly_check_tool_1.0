#!/usr/bin/env python3
"""
迁移脚本：为 equipment_processing 表添加 equipment_type 字段
Migration Script: Add equipment_type column to equipment_processing table
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from sqlalchemy import text
from shared.database_models import create_db_engine, get_database_url

def migrate_equipment_processing():
    """迁移 equipment_processing 表"""
    try:
        # 获取数据库连接
        database_url = get_database_url()
        engine = create_db_engine(database_url, echo=True)
        
        print("=" * 60)
        print("开始迁移 equipment_processing 表...")
        print("=" * 60)
        
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'equipment_processing'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ equipment_processing 表不存在，无需迁移")
                return
            
            # 检查 equipment_type 列是否已存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'equipment_processing' 
                    AND column_name = 'equipment_type'
                );
            """))
            column_exists = result.scalar()
            
            if column_exists:
                print("✓ equipment_type 列已存在，无需迁移")
                return
            
            print("\n1. 清空现有处理记录（因为需要添加必需字段）...")
            conn.execute(text("DELETE FROM equipment_processing;"))
            conn.commit()
            print("   ✓ 已清空处理记录")
            
            print("\n2. 添加 equipment_type 列...")
            conn.execute(text("""
                ALTER TABLE equipment_processing 
                ADD COLUMN equipment_type VARCHAR(50) NOT NULL DEFAULT 'POS';
            """))
            conn.commit()
            print("   ✓ 已添加 equipment_type 列")
            
            print("\n3. 创建复合索引...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_processing_store_type 
                ON equipment_processing(store_id, equipment_type);
            """))
            conn.commit()
            print("   ✓ 已创建索引 idx_processing_store_type")
            
            print("\n4. 移除默认值...")
            conn.execute(text("""
                ALTER TABLE equipment_processing 
                ALTER COLUMN equipment_type DROP DEFAULT;
            """))
            conn.commit()
            print("   ✓ 已移除默认值")
            
        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("\n注意事项：")
        print("- 所有旧的处理记录已被清空")
        print("- 新的处理记录将按设备类型（POS/机顶盒）分别记录")
        print("- 请重新运行 import_equipment_data.py 导入设备数据")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    migrate_equipment_processing()
