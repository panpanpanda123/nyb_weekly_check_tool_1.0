#!/usr/bin/env python3
"""
活动参与度表结构迁移脚本
删除旧表，让ORM自动创建新表
"""
import sys
import os
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from sqlalchemy import text
from shared.database_models import create_db_engine, create_session_factory, init_viewer_db

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)


def migrate():
    print("=" * 60)
    print("活动参与度表结构迁移")
    print("=" * 60)

    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()

    try:
        # 删除旧表
        session.execute(text("DROP TABLE IF EXISTS promo_participation CASCADE;"))
        session.commit()
        print("✓ 旧表已删除")

        # 用ORM创建新表
        init_viewer_db(engine)
        print("✓ 新表已创建")

        print(f"\n{'=' * 60}")
        print("✓ 迁移完成，请运行 import_promo_data.py 导入数据")
        print(f"{'=' * 60}\n")

    except Exception as e:
        session.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    migrate()
