#!/usr/bin/env python3
"""
仅更新白名单脚本（保留审核结果和已处理状态）
Update Whitelist Only Script
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from viewer.data_importer import DataImporter
from shared.database_models import create_db_engine, create_session_factory

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("仅更新白名单工具（保留审核结果）")
print("=" * 60)
print()

# 1. 查找whitelist文件
print("📁 查找whitelist文件...")
project_root = Path(__file__).parent

whitelist_file = project_root / 'whitelist.xlsx'
if not whitelist_file.exists():
    print(f"❌ 未找到whitelist.xlsx")
    sys.exit(1)
print(f"✅ 找到whitelist: {whitelist_file}")
print()

# 2. 连接数据库
print("🔗 连接数据库...")
try:
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    print("✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)

print()

# 3. 导入whitelist（会清空旧数据）
print("📥 更新whitelist...")
print("⚠️  注意：只更新运营分配信息，不影响审核结果和已处理状态")
try:
    importer = DataImporter(session)
    result = importer.import_whitelist(str(whitelist_file))
    
    if result.success:
        print(f"✅ whitelist更新成功")
        print(f"   更新记录数: {result.records_count}")
    else:
        print(f"❌ whitelist更新失败: {result.error_message}")
        session.close()
        sys.exit(1)
except Exception as e:
    print(f"❌ 更新whitelist时出错: {e}")
    import traceback
    traceback.print_exc()
    session.close()
    sys.exit(1)

print()

# 4. 关闭连接
session.close()

print("=" * 60)
print("✅ 白名单更新完成！")
print("=" * 60)
print()
print("💡 说明:")
print("   - 运营分配信息已更新")
print("   - 审核结果数据保持不变")
print("   - 用户的"已处理"标记保持不变（存储在浏览器中）")
print()
print("📱 刷新网页即可看到新的运营分配")
print()
