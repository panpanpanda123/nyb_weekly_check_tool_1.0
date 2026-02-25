#!/usr/bin/env python3
"""
服务器数据导入脚本
Import Data to Server Script
"""
import sys
import os
from pathlib import Path
import glob

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from viewer.data_importer import DataImporter
from shared.database_models import create_db_engine, create_session_factory

# 数据库配置
DATABASE_URL = 'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'

print("=" * 60)
print("服务器数据导入工具")
print("=" * 60)
print()

# 1. 查找文件
print("📁 查找数据文件...")
project_root = Path(__file__).parent

# 查找whitelist
whitelist_file = project_root / 'whitelist.xlsx'
if not whitelist_file.exists():
    print(f"❌ 未找到whitelist.xlsx")
    sys.exit(1)
print(f"✅ 找到whitelist: {whitelist_file}")

# 查找审核结果CSV（支持日期标识）
csv_files = list(project_root.glob('审核结果_*.csv'))
if not csv_files:
    print(f"❌ 未找到审核结果CSV文件（审核结果_*.csv）")
    sys.exit(1)

# 如果有多个，使用最新的
csv_file = sorted(csv_files)[-1]
print(f"✅ 找到审核结果: {csv_file}")
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

# 3. 导入whitelist
print("📥 导入whitelist...")
try:
    importer = DataImporter(session)
    result = importer.import_whitelist(str(whitelist_file))
    
    if result.success:
        print(f"✅ whitelist导入成功")
        print(f"   导入记录数: {result.records_count}")
    else:
        print(f"❌ whitelist导入失败: {result.error_message}")
        session.close()
        sys.exit(1)
except Exception as e:
    print(f"❌ 导入whitelist时出错: {e}")
    session.close()
    sys.exit(1)

print()

# 4. 导入审核结果
print("📥 导入审核结果...")
try:
    result = importer.import_reviews(str(csv_file))
    
    if result.success:
        print(f"✅ 审核结果导入成功")
        print(f"   导入记录数: {result.records_count}")
        if result.unmatched_stores_count > 0:
            print(f"   ⚠️  未匹配门店数: {result.unmatched_stores_count}")
            print(f"   （这些门店在whitelist中找不到，已标记为[未匹配]）")
    else:
        print(f"❌ 审核结果导入失败: {result.error_message}")
        session.close()
        sys.exit(1)
except Exception as e:
    print(f"❌ 导入审核结果时出错: {e}")
    session.close()
    sys.exit(1)

print()

# 5. 关闭连接
session.close()

print("=" * 60)
print("✅ 数据导入完成！")
print("=" * 60)
print()
print("📱 访问地址: http://weeklycheck.blitzepanda.top")
print()
print("💡 提示:")
print("   - 如果有门店未匹配，请检查whitelist.xlsx")
print("   - 带'-'的门店ID会被自动处理")
print("   - 重复运行此脚本会清空旧数据并重新导入")
print()
