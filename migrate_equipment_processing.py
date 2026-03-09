"""
设备异常处理表迁移脚本
Migration script for equipment processing table
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from sqlalchemy import text
from shared.database_models import create_db_engine

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

def run_migration():
    """运行数据库迁移"""
    print("🚀 开始数据库迁移...")
    
    engine = create_db_engine(DATABASE_URL, echo=False)
    
    with engine.connect() as conn:
        try:
            # 1. 创建 equipment_status_snapshot 表
            print("\n📋 创建 equipment_status_snapshot 表...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS equipment_status_snapshot (
                    id SERIAL PRIMARY KEY,
                    store_id VARCHAR(50) NOT NULL,
                    equipment_type VARCHAR(20) NOT NULL,
                    snapshot_date DATE NOT NULL,
                    snapshot_period VARCHAR(2) NOT NULL,
                    has_abnormal INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT unique_snapshot UNIQUE (store_id, equipment_type, snapshot_date, snapshot_period)
                )
            """))
            conn.commit()
            print("✅ equipment_status_snapshot 表创建成功")
            
            # 2. 创建索引
            print("\n📋 创建索引...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_snapshot_store_type_date 
                ON equipment_status_snapshot (store_id, equipment_type, snapshot_date)
            """))
            conn.commit()
            print("✅ 索引创建成功")
            
            # 3. 检查 equipment_processing 表是否存在 expected_recovery_date 字段
            print("\n📋 检查 equipment_processing 表字段...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'equipment_processing' 
                AND column_name = 'expected_recovery_date'
            """))
            
            if result.fetchone() is None:
                print("📋 添加 expected_recovery_date 字段...")
                conn.execute(text("""
                    ALTER TABLE equipment_processing 
                    ADD COLUMN expected_recovery_date TIMESTAMP
                """))
                conn.commit()
                print("✅ expected_recovery_date 字段添加成功")
            else:
                print("ℹ️  expected_recovery_date 字段已存在，跳过")
            
            # 4. 检查 equipment_processing 表是否存在 suppressed_until 字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'equipment_processing' 
                AND column_name = 'suppressed_until'
            """))
            
            if result.fetchone() is None:
                print("📋 添加 suppressed_until 字段...")
                conn.execute(text("""
                    ALTER TABLE equipment_processing 
                    ADD COLUMN suppressed_until TIMESTAMP
                """))
                conn.commit()
                print("✅ suppressed_until 字段添加成功")
            else:
                print("ℹ️  suppressed_until 字段已存在，跳过")
            
            # 5. 创建 equipment_import_log 表（如果不存在）
            print("\n📋 创建 equipment_import_log 表...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS equipment_import_log (
                    id SERIAL PRIMARY KEY,
                    import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_time VARCHAR(50),
                    pos_count INTEGER DEFAULT 0,
                    stb_count INTEGER DEFAULT 0,
                    total_count INTEGER DEFAULT 0
                )
            """))
            conn.commit()
            print("✅ equipment_import_log 表创建成功")
            
            print("\n" + "="*50)
            print("✅ 数据库迁移完成！")
            print("="*50)
            
            # 显示统计信息
            print("\n📊 数据统计:")
            
            # 快照表记录数
            result = conn.execute(text("SELECT COUNT(*) FROM equipment_status_snapshot"))
            snapshot_count = result.fetchone()[0]
            print(f"  - 快照记录数: {snapshot_count}")
            
            # 处理记录数
            result = conn.execute(text("SELECT COUNT(*) FROM equipment_processing"))
            processing_count = result.fetchone()[0]
            print(f"  - 处理记录数: {processing_count}")
            
            # 导入日志记录数
            result = conn.execute(text("SELECT COUNT(*) FROM equipment_import_log"))
            log_count = result.fetchone()[0]
            print(f"  - 导入日志数: {log_count}")
            
            print("\n✅ 迁移验证通过！")
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            conn.rollback()
            raise


if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)
