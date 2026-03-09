#!/usr/bin/env python3
"""
测试预计恢复日期功能
验证在预计恢复期内的门店是否被正确过滤
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentProcessing, EquipmentStatus
)
from equipment_utils import should_suppress

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 80)
print("测试预计恢复日期功能")
print("=" * 80)
print()

# 连接数据库
engine = create_db_engine(DATABASE_URL, echo=False)
SessionFactory = create_session_factory(engine)
session = SessionFactory()

# 1. 查找所有有预计恢复日期的处理记录
print("📋 查找有预计恢复日期的处理记录:")
print()

processing_with_recovery = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.expected_recovery_date.isnot(None))\
    .all()

print(f"   找到 {len(processing_with_recovery)} 条记录")
print()

if processing_with_recovery:
    print("   详细信息:")
    for i, p in enumerate(processing_with_recovery[:10], 1):
        print(f"\n   {i}. 门店ID: {p.store_id}")
        print(f"      设备类型: {p.equipment_type}")
        print(f"      处理动作: {p.action}")
        print(f"      处理时间: {p.processed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      预计恢复日期: {p.expected_recovery_date.strftime('%Y-%m-%d')}")
        print(f"      暂时不提示截止: {p.suppressed_until.strftime('%Y-%m-%d') if p.suppressed_until else '无'}")
        
        # 检查是否应该暂时不提示
        should_hide = should_suppress(session, p.store_id, p.equipment_type)
        status = "✅ 暂时不提示" if should_hide else "❌ 需要提示"
        print(f"      当前状态: {status}")
        
        # 检查该门店是否还有设备异常
        current_equipment = session.query(EquipmentStatus)\
            .filter(EquipmentStatus.store_id == p.store_id)\
            .filter(EquipmentStatus.equipment_type == p.equipment_type)\
            .first()
        
        if current_equipment:
            print(f"      ⚠️  当前仍有设备异常")
        else:
            print(f"      ✅ 当前无设备异常")

# 2. 统计在预计恢复期内的门店
print("\n" + "=" * 80)
print("📊 统计在预计恢复期内的门店:")
print("=" * 80)
print()

# 获取所有当前有异常的门店
all_abnormal_stores = session.query(EquipmentStatus.store_id, EquipmentStatus.equipment_type)\
    .distinct()\
    .all()

print(f"   当前有异常的门店: {len(all_abnormal_stores)} 家")

# 检查哪些在预计恢复期内
suppressed_count = 0
need_alert_count = 0

for store_id, equipment_type in all_abnormal_stores:
    if should_suppress(session, store_id, equipment_type):
        suppressed_count += 1
    else:
        need_alert_count += 1

print(f"   在预计恢复期内（暂时不提示）: {suppressed_count} 家")
print(f"   需要提示: {need_alert_count} 家")
print()

# 3. 显示即将到期的预计恢复日期
print("=" * 80)
print("⏰ 即将到期的预计恢复日期（3天内）:")
print("=" * 80)
print()

three_days_later = date.today() + timedelta(days=3)

expiring_soon = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.suppressed_until.isnot(None))\
    .filter(EquipmentProcessing.suppressed_until >= datetime.now())\
    .filter(EquipmentProcessing.suppressed_until <= datetime.combine(three_days_later, datetime.max.time()))\
    .all()

if expiring_soon:
    print(f"   找到 {len(expiring_soon)} 条即将到期的记录:")
    for p in expiring_soon:
        days_left = (p.suppressed_until.date() - date.today()).days
        print(f"\n   门店ID: {p.store_id}")
        print(f"   设备类型: {p.equipment_type}")
        print(f"   预计恢复日期: {p.expected_recovery_date.strftime('%Y-%m-%d')}")
        print(f"   剩余天数: {days_left} 天")
else:
    print("   ✅ 没有即将到期的记录")

# 4. 显示已过期但未处理的记录
print("\n" + "=" * 80)
print("⚠️  已过期但未处理的记录:")
print("=" * 80)
print()

expired = session.query(EquipmentProcessing)\
    .filter(EquipmentProcessing.suppressed_until.isnot(None))\
    .filter(EquipmentProcessing.suppressed_until < datetime.now())\
    .all()

if expired:
    print(f"   找到 {len(expired)} 条已过期的记录:")
    for p in expired:
        # 检查该门店是否还有设备异常
        current_equipment = session.query(EquipmentStatus)\
            .filter(EquipmentStatus.store_id == p.store_id)\
            .filter(EquipmentStatus.equipment_type == p.equipment_type)\
            .first()
        
        if current_equipment:
            print(f"\n   ⚠️  门店ID: {p.store_id} ({p.equipment_type})")
            print(f"      预计恢复日期: {p.expected_recovery_date.strftime('%Y-%m-%d')}")
            print(f"      当前状态: 仍有设备异常，需要重新处理")
        else:
            print(f"\n   ✅ 门店ID: {p.store_id} ({p.equipment_type})")
            print(f"      预计恢复日期: {p.expected_recovery_date.strftime('%Y-%m-%d')}")
            print(f"      当前状态: 已恢复")
else:
    print("   ✅ 没有已过期的记录")

session.close()

print()
print("=" * 80)
print("✅ 测试完成")
print("=" * 80)
print()
