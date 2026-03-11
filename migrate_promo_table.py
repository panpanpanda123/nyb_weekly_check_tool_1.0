#!/usr/bin/env python3
"""
活动参与度表结构迁移脚本
Migration Script for Promo Participation Table
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from sqlalchemy import text
from shared.database_models import create_db_engine, create_session_factory

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)


def migrate_promo_table():
    """迁移活动参与度表结构"""
    print("="*60)
    print("活动参与度表结构迁移")
    print("="*60)
    
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        # 1. 检查表是否存在
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'promo_participation'
            );
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("✓ 表不存在，无需迁移")
            return
        
        print("✓ 找到现有表")
        
        # 2. 检查是否有重复数据
        result = session.execute(text("""
            SELECT store_id, COUNT(*) as count
            FROM promo_participation
            GROUP BY store_id
            HAVING COUNT(*) > 1;
        """))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"\n⚠️  发现 {len(duplicates)} 个门店有重复数据:")
            for store_id, count in duplicates[:10]:  # 只显示前10个
                print(f"   - 门店 {store_id}: {count} 条记录")
            if len(duplicates) > 10:
                print(f"   ... 还有 {len(duplicates) - 10} 个门店")
        
        # 3. 创建临时表，保留每个门店最新的一条记录
        print("\n正在创建临时表...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS promo_participation_new (
                store_id VARCHAR(50) PRIMARY KEY,
                store_name VARCHAR(255),
                war_zone VARCHAR(50),
                regional_manager VARCHAR(50),
                order_count INTEGER DEFAULT 0,
                benefit_card_sales INTEGER DEFAULT 0,
                promo_package_sales INTEGER DEFAULT 0,
                participation_rate VARCHAR(20),
                data_date VARCHAR(20),
                import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        session.commit()
        print("✓ 临时表创建成功")
        
        # 4. 复制数据（每个门店只保留最新的一条）
        print("\n正在复制数据（保留最新记录）...")
        session.execute(text("""
            INSERT INTO promo_participation_new
            SELECT DISTINCT ON (store_id)
                store_id,
                store_name,
                war_zone,
                regional_manager,
                order_count,
                benefit_card_sales,
                promo_package_sales,
                participation_rate,
                data_date,
                import_time
            FROM promo_participation
            ORDER BY store_id, import_time DESC;
        """))
        session.commit()
        
        # 5. 统计数据
        result = session.execute(text("SELECT COUNT(*) FROM promo_participation;"))
        old_count = result.scalar()
        
        result = session.execute(text("SELECT COUNT(*) FROM promo_participation_new;"))
        new_count = result.scalar()
        
        print(f"✓ 数据复制完成")
        print(f"  - 原表记录数: {old_count}")
        print(f"  - 新表记录数: {new_count}")
        print(f"  - 清理重复数据: {old_count - new_count} 条")
        
        # 6. 删除旧表
        print("\n正在删除旧表...")
        session.execute(text("DROP TABLE promo_participation;"))
        session.commit()
        print("✓ 旧表已删除")
        
        # 7. 重命名新表
        print("\n正在重命名新表...")
        session.execute(text("ALTER TABLE promo_participation_new RENAME TO promo_participation;"))
        session.commit()
        print("✓ 新表已重命名")
        
        # 8. 创建索引
        print("\n正在创建索引...")
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_promo_war_zone 
            ON promo_participation(war_zone);
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_promo_regional_manager 
            ON promo_participation(regional_manager);
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_promo_data_date 
            ON promo_participation(data_date);
        """))
        session.commit()
        print("✓ 索引创建完成")
        
        print(f"\n{'='*60}")
        print(f"✓ 表结构迁移完成")
        print(f"  - 每个门店现在只有一条记录")
        print(f"  - store_id 已设置为主键")
        print(f"{'='*60}\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    migrate_promo_table()
