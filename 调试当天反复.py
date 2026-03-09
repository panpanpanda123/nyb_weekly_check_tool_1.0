#!/usr/bin/env python3
"""
调试"当天反复"判定逻辑
用于排查为什么会出现异常判定
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

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 80)
print("调试'当天反复'判定逻辑")
print("=" * 80)
print()

# 连接数据库
engine = create_db_engine(DATABASE_URL, echo=False)
SessionFactory = create_session_factory(engine)
session = SessionFactory()

today = date.today()
today_start = datetime.combine(today, datetime.min.time())
today_end = datetime.combine(today, datetime.max.time())

# 1. 检查今天的快照（按时段分组）
print("📸 今天的快照统计:")
am_snapshots = session.query(EquipmentStatusSnapshot)\
    .filter(EquipmentStatusSnapshot.snapshot_date >= today_start)\
    .filter(EquipmentStatusSnapshot.snapshot_date <= today_end)\
    .filter(EquipmentStatusSnapshot.snapshot_period == 'AM')\
    .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
    .all()

pm_snapshots = session.query(EquipmentStatusSnapshot)\
    .filter(EquipmentStatusSnapshot.snapshot_date >= today_start)\
    .filter(EquipmentStatusSnapshot.snapshot_date <= today_end)\
    .filter(EquipmentStatusSnapshot.snapshot_period == 'PM')\
    .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
    .all()

print(f"   上午(AM)异常快照: {len(am_snapshots)} 条")
print(f"   下午(PM)异常快照: {len(pm_snapshots)} 条")
print()

# 2. 检查今天的处理记录（按动作分组）
print("📝 今天的处理记录统计:")
recovered = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.processed_at >= today_start)\
    .filter(EquipmentProcessing.action == '已恢复')\
    .all()

not_recovered = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.processed_at >= today_start)\
    .filter(EquipmentProcessing.action == '未恢复')\
    .all()

print(f"   已恢复: {len(recovered)} 条")
print(f"   未恢复: {len(not_recovered)} 条")
print()

# 3. 找出可能触发"当天反复"的门店
print("🔍 可能触发'当天反复'的门店:")
print("   条件: 上午有异常 + 标记已恢复 + 下午有异常")
print()

am_store_ids = {s.store_id for s in am_snapshots}
pm_store_ids = {s.store_id for s in pm_snapshots}
recovered_store_ids = {p.store_id for p in recovered if p.equipment_type == 'POS'}

# 找到同时满足三个条件的门店
repeat_stores = am_store_ids & pm_store_ids & recovered_store_ids

print(f"   上午有异常的门店: {len(am_store_ids)} 家")
print(f"   下午有异常的门店: {len(pm_store_ids)} 家")
print(f"   标记已恢复的门店: {len(recovered_store_ids)} 家")
print(f"   → 应该触发'当天反复': {len(repeat_stores)} 家")
print()

if repeat_stores:
    print("   门店详情（前10家）:")
    for i, store_id in enumerate(list(repeat_stores)[:10], 1):
        # 获取快照信息
        am = [s for s in am_snapshots if s.store_id == store_id]
        pm = [s for s in pm_snapshots if s.store_id == store_id]
        proc = [p for p in recovered if p.store_id == store_id and p.equipment_type == 'POS']
        
        print(f"\n   {i}. 门店ID: {store_id}")
        print(f"      上午快照: {len(am)} 条")
        for snap in am:
            print(f"         - {snap.snapshot_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"      下午快照: {len(pm)} 条")
        for snap in pm:
            print(f"         - {snap.snapshot_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"      处理记录: {len(proc)} 条")
        for p in proc:
            print(f"         - {p.processed_at.strftime('%Y-%m-%d %H:%M:%S')} ({p.action})")
else:
    print("   ⚠️  没有找到符合条件的门店")

# 4. 检查是否有重复快照
print("\n" + "=" * 80)
print("🔍 检查重复快照（同一门店、同一时段有多条快照）:")
print("=" * 80)
print()

# 检查AM重复
am_duplicates = {}
for snap in am_snapshots:
    key = snap.store_id
    if key not in am_duplicates:
        am_duplicates[key] = []
    am_duplicates[key].append(snap)

am_dup_stores = {k: v for k, v in am_duplicates.items() if len(v) > 1}
if am_dup_stores:
    print(f"⚠️  发现 {len(am_dup_stores)} 家门店有重复的上午快照:")
    for store_id, snaps in list(am_dup_stores.items())[:5]:
        print(f"   门店 {store_id}: {len(snaps)} 条AM快照")
        for snap in snaps:
            print(f"      - {snap.snapshot_date.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print("✅ 上午快照无重复")

# 检查PM重复
pm_duplicates = {}
for snap in pm_snapshots:
    key = snap.store_id
    if key not in pm_duplicates:
        pm_duplicates[key] = []
    pm_duplicates[key].append(snap)

pm_dup_stores = {k: v for k, v in pm_duplicates.items() if len(v) > 1}
if pm_dup_stores:
    print(f"\n⚠️  发现 {len(pm_dup_stores)} 家门店有重复的下午快照:")
    for store_id, snaps in list(pm_dup_stores.items())[:5]:
        print(f"   门店 {store_id}: {len(snaps)} 条PM快照")
        for snap in snaps:
            print(f"      - {snap.snapshot_date.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print("✅ 下午快照无重复")

# 5. 检查当前设备异常状态
print("\n" + "=" * 80)
print("🔧 当前设备异常状态:")
print("=" * 80)
print()

current_equipment = session.query(EquipmentStatus)\
    .filter(EquipmentStatus.equipment_type == 'POS')\
    .all()

print(f"   当前POS异常: {len(current_equipment)} 条")

session.close()

print()
print("=" * 80)
print("✅ 调试完成")
print("=" * 80)
print()
