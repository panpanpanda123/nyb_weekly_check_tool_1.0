#!/usr/bin/env python3
"""
检查"当天反复"判定逻辑
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentStatusSnapshot, EquipmentProcessing, EquipmentStatus
)
from equipment_utils import is_chronic_store

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("检查'当天反复'判定逻辑")
print("=" * 60)
print()

# 连接数据库
engine = create_db_engine(DATABASE_URL, echo=False)
SessionFactory = create_session_factory(engine)
session = SessionFactory()

today = date.today()

# 1. 检查今天的快照
print("📸 今天的快照:")
am_snapshots = session.query(EquipmentStatusSnapshot)\
    .filter(EquipmentStatusSnapshot.snapshot_date == today)\
    .filter(EquipmentStatusSnapshot.snapshot_period == 'AM')\
    .all()

pm_snapshots = session.query(EquipmentStatusSnapshot)\
    .filter(EquipmentStatusSnapshot.snapshot_date == today)\
    .filter(EquipmentStatusSnapshot.snapshot_period == 'PM')\
    .all()

print(f"   上午(AM)快照: {len(am_snapshots)} 条")
print(f"   下午(PM)快照: {len(pm_snapshots)} 条")

# 2. 检查今天的处理记录
print("\n📝 今天的处理记录:")
today_processing = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.processed_at >= datetime.combine(today, datetime.min.time()))\
    .all()

print(f"   处理记录: {len(today_processing)} 条")
for p in today_processing[:5]:
    print(f"   - {p.store_id} ({p.equipment_type}): {p.action} at {p.processed_at}")

# 3. 检查当前设备异常
print("\n🔧 当前设备异常:")
current_equipment = session.query(EquipmentStatus)\
    .filter(EquipmentStatus.equipment_type == 'POS')\
    .all()

print(f"   POS异常: {len(current_equipment)} 条")

# 4. 查找可能触发"当天反复"的门店
print("\n🔍 查找可能触发'当天反复'的门店:")
print("   条件: 上午有异常 + 今天处理过 + 下午有异常")
print()

am_store_ids = {s.store_id for s in am_snapshots if s.has_abnormal == 1}
pm_store_ids = {s.store_id for s in pm_snapshots if s.has_abnormal == 1}
processed_store_ids = {p.store_id for p in today_processing if p.equipment_type == 'POS'}

# 找到同时满足三个条件的门店
repeat_stores = am_store_ids & pm_store_ids & processed_store_ids

print(f"   上午有异常的门店: {len(am_store_ids)} 家")
print(f"   下午有异常的门店: {len(pm_store_ids)} 家")
print(f"   今天处理过的门店: {len(processed_store_ids)} 家")
print(f"   → 应该触发'当天反复': {len(repeat_stores)} 家")
print()

if repeat_stores:
    print("   门店列表:")
    for store_id in list(repeat_stores)[:10]:
        # 测试判定逻辑
        is_chronic, reason, counts = is_chronic_store(session, store_id, 'POS')
        status = "✅" if is_chronic and reason == "当天反复" else "❌"
        print(f"   {status} {store_id}: {reason or '未触发'}")
else:
    print("   ⚠️  没有找到符合条件的门店")
    print()
    print("   可能原因:")
    print("   1. 上午没有导入快照")
    print("   2. 今天没有处理记录")
    print("   3. 下午没有异常（都恢复了）")

# 5. 检查一个具体门店（如果有）
if repeat_stores:
    test_store_id = list(repeat_stores)[0]
    print(f"\n🧪 测试门店 {test_store_id}:")
    
    # 上午快照
    am = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == test_store_id)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'AM')\
        .first()
    print(f"   上午快照: {'✅ 有异常' if am and am.has_abnormal == 1 else '❌ 无'}")
    
    # 下午快照
    pm = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == test_store_id)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'PM')\
        .first()
    print(f"   下午快照: {'✅ 有异常' if pm and pm.has_abnormal == 1 else '❌ 无'}")
    
    # 处理记录
    processing = session.query(EquipmentProcessing)\
        .filter(EquipmentProcessing.store_id == test_store_id)\
        .filter(EquipmentProcessing.equipment_type == 'POS')\
        .filter(EquipmentProcessing.processed_at >= datetime.combine(today, datetime.min.time()))\
        .first()
    print(f"   处理记录: {'✅ 有' if processing else '❌ 无'}")
    if processing:
        print(f"      动作: {processing.action}")
        print(f"      时间: {processing.processed_at}")
    
    # 判定结果
    is_chronic, reason, counts = is_chronic_store(session, test_store_id, 'POS')
    print(f"\n   判定结果: {'🔴 经常出问题' if is_chronic else '⚪ 正常'}")
    print(f"   触发原因: {reason or '无'}")

session.close()

print()
print("=" * 60)
print("✅ 检查完成")
print("=" * 60)
print()
