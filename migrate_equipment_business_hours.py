#!/usr/bin/env python3
"""
数据库迁移：为 equipment_status 表添加营业时间相关字段
Migration: Add business_hours and is_open_at_data_time columns to equipment_status
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("数据库迁移：添加营业时间字段")
print("=" * 60)

try:
    from sqlalchemy import create_engine, text
    engine = create_engine(DATABASE_URL, echo=False)
    
    with engine.connect() as conn:
        # 检查列是否已存在
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'equipment_status' 
            AND column_name IN ('business_hours', 'is_open_at_data_time')
        """))
        existing_cols = {row[0] for row in result}
        
        if 'business_hours' not in existing_cols:
            conn.execute(text("ALTER TABLE equipment_status ADD COLUMN business_hours TEXT"))
            print("✅ 添加 business_hours 列")
        else:
            print("⏭️  business_hours 列已存在，跳过")
        
        if 'is_open_at_data_time' not in existing_cols:
            conn.execute(text("ALTER TABLE equipment_status ADD COLUMN is_open_at_data_time INTEGER DEFAULT 1"))
            print("✅ 添加 is_open_at_data_time 列")
        else:
            print("⏭️  is_open_at_data_time 列已存在，跳过")
        
        conn.commit()
    
    print()
    print("✅ 迁移完成！")

except Exception as e:
    print(f"❌ 迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
