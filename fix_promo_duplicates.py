#!/usr/bin/env python3
"""
活动参与度重复数据快速修复脚本
Quick Fix Script for Promo Participation Duplicates
"""
import sys
import os
from pathlib import Path

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


def fix_promo_duplicates():
    """快速修复活动参与度重复数据"""
    print("="*60)
    print("活动参与度重复数据快速修复")
    print("="*60)
    
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        # 1. 删除可能存在的临时表
        print("\n正在清理临时表...")
        session.execute(text("DROP TABLE IF EXISTS promo_participation_new;"))
        session.commit()
        print("✓ 临时表已清理")
        
        # 2. 检查原表是否存在
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'promo_participation'
            );
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("✓ 原表不存在，无需修复")
            return
        
        # 3. 统计原表数据
        result = session.execute(text("SELECT COUNT(*) FROM promo_participation;"))
        old_count = result.scalar()
        print(f"\n✓ 原表记录数: {old_count}")
        
        # 4. 检查重复数据
        result = session.execute(text("""
            SELECT store_id, COUNT(*) as count
            FROM promo_participation
            GROUP BY store_id
            HAVING COUNT(*) > 1;
        """))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"\n⚠️  发现 {len(duplicates)} 个门店有重复数据")
            for store_id, count in duplicates[:5]:
                print(f"   - 门店 {store_id}: {count} 条记录")
            if len(duplicates) > 5:
                print(f"   ... 还有 {len(duplicates) - 5} 个门店")
        else:
            print("\n✓ 没有发现重复数据")
        
        # 5. 创建新表结构（store_id 作为主键）
        print("\n正在创建新表...")
        session.execute(text("""
            CREATE TABLE promo_participation_new (
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
        print("✓ 新表创建成功")
        
        # 6. 使用 CTE 复制数据（每个门店只保留最新的一条）
        print("\n正在复制数据（每个门店保留最新记录）...")
        session.execute(text("""
            WITH ranked_records AS (
                SELECT 
                    store_id,
                    store_name,
                    war_zone,
                    regional_manager,
                    order_count,
                    benefit_card_sales,
                    promo_package_sales,
                    participation_rate,
                    data_date,
                    import_time,
                    ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY import_time DESC) as rn
                FROM promo_participation
            )
            INSERT INTO promo_participation_new
            SELECT 
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
            FROM ranked_records
            WHERE rn = 1;
        """))
        session.commit()
        
        # 7. 统计新表数据
        result = session.execute(text("SELECT COUNT(*) FROM promo_participation_new;"))
        new_count = result.scalar()
        
        print(f"✓ 数据复制完成")
        print(f"  - 原表记录数: {old_count}")
        print(f"  - 新表记录数: {new_count}")
        print(f"  - 清理重复数据: {old_count - new_count} 条")
        
        # 8. 删除旧表
        print("\n正在删除旧表...")
        session.execute(text("DROP TABLE promo_participation;"))
        session.commit()
        print("✓ 旧表已删除")
        
        # 9. 重命名新表
        print("\n正在重命名新表...")
        session.execute(text("ALTER TABLE promo_participation_new RENAME TO promo_participation;"))
        session.commit()
        print("✓ 新表已重命名为 promo_participation")
        
        # 10. 创建索引
        print("\n正在创建索引...")
        session.execute(text("""
            CREATE INDEX idx_promo_war_zone ON promo_participation(war_zone);
        """))
        session.execute(text("""
            CREATE INDEX idx_promo_regional_manager ON promo_participation(regional_manager);
        """))
        session.execute(text("""
            CREATE INDEX idx_promo_data_date ON promo_participation(data_date);
        """))
        session.commit()
        print("✓ 索引创建完成")
        
        print(f"\n{'='*60}")
        print(f"✓ 修复完成！")
        print(f"  - 每个门店现在只有一条记录")
        print(f"  - store_id 已设置为主键")
        print(f"  - 总记录数: {new_count}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 尝试清理临时表
        try:
            session.execute(text("DROP TABLE IF EXISTS promo_participation_new;"))
            session.commit()
            print("\n✓ 已清理临时表")
        except:
            pass
    finally:
        session.close()


if __name__ == '__main__':
    fix_promo_duplicates()
