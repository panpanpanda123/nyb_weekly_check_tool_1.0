#!/usr/bin/env python3
"""
从处理结果反向生成上午快照
用于测试和恢复数据
"""
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentStatusSnapshot
)

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("从处理结果恢复上午快照")
print("=" * 60)
print()

# 1. 查找处理结果文件
print("📁 查找处理结果文件...")
project_root = Path(__file__).parent
result_files = list(project_root.glob('设备异常处理结果_*.xlsx'))

if not result_files:
    print("❌ 未找到处理结果文件")
    sys.exit(1)

# 使用最新的文件
result_file = max(result_files, key=lambda p: p.stat().st_mtime)
print(f"✅ 找到文件: {result_file.name}")
print()

# 2. 读取处理结果
print("📖 读取处理结果...")
try:
    df = pd.read_excel(result_file)
    print(f"✅ 读取 {len(df)} 条记录")
    print(f"   列名: {list(df.columns)}")
except Exception as e:
    print(f"❌ 读取文件失败: {e}")
    sys.exit(1)

print()

# 3. 连接数据库
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

# 4. 生成上午快照
print("📸 生成上午快照...")
try:
    today = date.today()
    snapshot_period = 'AM'
    
    # 检查今天上午快照是否已存在
    existing_count = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == snapshot_period)\
        .count()
    
    if existing_count > 0:
        print(f"⚠️  今天上午快照已存在 {existing_count} 条")
        confirm = input("是否删除并重新生成？(y/n): ")
        if confirm.lower() != 'y':
            print("❌ 取消操作")
            session.close()
            sys.exit(0)
        
        # 删除旧快照
        session.query(EquipmentStatusSnapshot)\
            .filter(EquipmentStatusSnapshot.snapshot_date == today)\
            .filter(EquipmentStatusSnapshot.snapshot_period == snapshot_period)\
            .delete()
        session.commit()
        print(f"✅ 已删除 {existing_count} 条旧快照")
    
    # 从处理结果提取门店ID
    # 假设列名是 '门店ID' 或 'store_id'
    store_id_column = None
    for col in df.columns:
        if '门店' in str(col) and 'ID' in str(col):
            store_id_column = col
            break
        elif col == 'store_id':
            store_id_column = col
            break
    
    if not store_id_column:
        # 尝试第一列
        store_id_column = df.columns[0]
        print(f"⚠️  未找到门店ID列，使用第一列: {store_id_column}")
    
    print(f"   使用列: {store_id_column}")
    
    # 获取所有门店ID（去重）
    store_ids = df[store_id_column].dropna().unique()
    print(f"   找到 {len(store_ids)} 个门店")
    
    # 创建快照
    snapshot_count = 0
    for store_id in store_ids:
        store_id = str(store_id).strip()
        if not store_id or store_id == 'nan':
            continue
        
        snapshot = EquipmentStatusSnapshot(
            snapshot_date=today,
            snapshot_period=snapshot_period,
            store_id=store_id,
            equipment_type='POS',  # 假设都是POS
            has_abnormal=1,
            created_at=datetime.now()
        )
        session.add(snapshot)
        snapshot_count += 1
    
    session.commit()
    print(f"✅ 创建 {snapshot_count} 条上午快照")
    
except Exception as e:
    print(f"❌ 生成快照失败: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
    session.close()
    sys.exit(1)

# 5. 验证
print()
print("🔍 验证快照...")
try:
    total_am = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'AM')\
        .count()
    
    total_pm = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'PM')\
        .count()
    
    print(f"✅ 今天上午快照: {total_am} 条")
    print(f"✅ 今天下午快照: {total_pm} 条")
    
except Exception as e:
    print(f"⚠️  验证失败: {e}")

# 6. 关闭连接
session.close()

print()
print("=" * 60)
print("✅ 上午快照恢复完成！")
print("=" * 60)
print()
print("💡 提示:")
print("   - 快照已生成，可以测试'经常出问题'功能")
print("   - 如果需要更多历史数据，可以多次运行并修改日期")
print()
