#!/usr/bin/env python3
"""
检查数据库中的设备数据
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentStatus, EquipmentProcessing
)

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("检查数据库中的设备数据")
print("=" * 60)
print()

# 连接数据库
try:
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    print("✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)

print()

# 查询POS设备数据
print("📊 POS设备数据统计：")
pos_count = session.query(EquipmentStatus).filter(EquipmentStatus.equipment_type == 'POS').count()
print(f"   总数: {pos_count} 条")

if pos_count > 0:
    # 显示前5条
    pos_records = session.query(EquipmentStatus).filter(
        EquipmentStatus.equipment_type == 'POS'
    ).limit(5).all()
    
    print("\n   前5条记录：")
    for record in pos_records:
        print(f"   - 门店: {record.store_id} {record.store_name}")
        print(f"     战区: {record.war_zone}, 区域经理: {record.regional_manager}")
        print(f"     导入时间: {record.import_time}")
        print()

print()

# 查询机顶盒设备数据
print("📊 机顶盒设备数据统计：")
stb_count = session.query(EquipmentStatus).filter(EquipmentStatus.equipment_type == '机顶盒').count()
print(f"   总数: {stb_count} 条")

if stb_count > 0:
    # 显示前5条
    stb_records = session.query(EquipmentStatus).filter(
        EquipmentStatus.equipment_type == '机顶盒'
    ).limit(5).all()
    
    print("\n   前5条记录：")
    for record in stb_records:
        print(f"   - 门店: {record.store_id} {record.store_name}")
        print(f"     战区: {record.war_zone}, 区域经理: {record.regional_manager}")
        print(f"     导入时间: {record.import_time}")
        print()

print()

# 查询POS处理记录
print("📊 POS处理记录统计：")
pos_processing_count = session.query(EquipmentProcessing).filter(
    EquipmentProcessing.equipment_type == 'POS'
).count()
print(f"   总数: {pos_processing_count} 条")

print()

# 查询机顶盒处理记录
print("📊 机顶盒处理记录统计：")
stb_processing_count = session.query(EquipmentProcessing).filter(
    EquipmentProcessing.equipment_type == '机顶盒'
).count()
print(f"   总数: {stb_processing_count} 条")

session.close()

print()
print("=" * 60)
print("✅ 检查完成")
print("=" * 60)
