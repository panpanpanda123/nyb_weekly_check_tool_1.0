#!/usr/bin/env python3
"""
设备异常数据导入脚本
Import Equipment Status Data
"""
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentStatus, StoreWhitelist
)

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("设备异常数据导入工具")
print("=" * 60)
print()

# 1. 查找数据文件
print("📁 查找数据文件...")
project_root = Path(__file__).parent
equipment_dir = project_root / 'equipment_status'

# 查找最新的文件
pos_files = list(equipment_dir.glob('牛约堡集团_点餐设备表*.xlsx'))
stb_files = list(equipment_dir.glob('202*.xlsx'))
store_files = list(equipment_dir.glob('牛约堡集团_门店档案*.xlsx'))

if not pos_files:
    print("❌ 未找到收银设备文件")
    sys.exit(1)
if not stb_files:
    print("❌ 未找到机顶盒文件")
    sys.exit(1)
if not store_files:
    print("❌ 未找到门店档案文件")
    sys.exit(1)

# 使用最新的文件
pos_file = max(pos_files, key=lambda p: p.stat().st_mtime)
stb_file = max(stb_files, key=lambda p: p.stat().st_mtime)
store_file = max(store_files, key=lambda p: p.stat().st_mtime)

print(f"✅ 找到收银设备文件: {pos_file.name}")
print(f"✅ 找到机顶盒文件: {stb_file.name}")
print(f"✅ 找到门店档案文件: {store_file.name}")
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

# 2.5 初始化数据库表
print("📋 初始化数据库表...")
try:
    from shared.database_models import init_viewer_db
    init_viewer_db(engine)
except Exception as e:
    print(f"⚠️  表可能已存在: {e}")

print()

# 3. 读取暂停营业门店列表
print("📖 读取暂停营业门店列表...")
try:
    df_closed = pd.read_excel(store_file, header=2)
    closed_stores = set(str(sid) for sid in df_closed['机构编码'].dropna())
    print(f"✅ 找到 {len(closed_stores)} 家暂停营业门店")
except Exception as e:
    print(f"❌ 读取门店档案失败: {e}")
    session.close()
    sys.exit(1)

print()

# 4. 读取whitelist
print("📖 读取whitelist...")
try:
    whitelist_dict = {}
    whitelist_records = session.query(StoreWhitelist).all()
    for record in whitelist_records:
        whitelist_dict[record.store_id] = {
            'store_name': record.store_name,
            'war_zone': record.war_zone,
            'regional_manager': record.regional_manager
        }
    print(f"✅ 加载 {len(whitelist_dict)} 条whitelist记录")
except Exception as e:
    print(f"❌ 读取whitelist失败: {e}")
    session.close()
    sys.exit(1)

print()

# 5. 处理收银设备数据
print("📥 处理收银设备数据...")
try:
    # 先清空旧数据和处理记录
    print("   清空旧设备数据和处理记录...")
    from shared.database_models import EquipmentProcessing
    session.query(EquipmentProcessing).delete()
    session.query(EquipmentStatus).delete()
    session.commit()
    print("   ✅ 已清空旧数据和处理记录")
    
    df_pos = pd.read_excel(pos_file, header=1)
    
    # 筛选离线设备
    df_offline_pos = df_pos[df_pos['状态'] == '离线'].copy()
    print(f"   找到 {len(df_offline_pos)} 台离线收银设备")
    
    pos_count = 0
    pos_skip_closed = 0
    pos_skip_no_whitelist = 0
    
    for _, row in df_offline_pos.iterrows():
        store_id = str(row['设备编号'])
        
        # 跳过暂停营业门店
        if store_id in closed_stores:
            pos_skip_closed += 1
            continue
        
        # 跳过不在whitelist中的门店
        if store_id not in whitelist_dict:
            pos_skip_no_whitelist += 1
            continue
        
        whitelist_info = whitelist_dict[store_id]
        
        equipment = EquipmentStatus(
            store_id=store_id,
            store_name=whitelist_info['store_name'],
            war_zone=whitelist_info['war_zone'],
            regional_manager=whitelist_info['regional_manager'],
            equipment_type='POS',
            equipment_id=store_id,
            equipment_name=str(row.get('设备名称', '')),
            status='离线',
            import_time=datetime.now()
        )
        session.add(equipment)
        pos_count += 1
    
    print(f"   导入 {pos_count} 条记录")
    print(f"   跳过暂停营业: {pos_skip_closed}")
    print(f"   跳过不在whitelist: {pos_skip_no_whitelist}")
    
except Exception as e:
    print(f"❌ 处理收银设备数据失败: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
    session.close()
    sys.exit(1)

print()

# 6. 处理机顶盒数据
print("📥 处理机顶盒数据...")
try:
    df_stb = pd.read_excel(stb_file)
    
    # 筛选离线设备
    df_offline_stb = df_stb[df_stb['状态'] == '离线'].copy()
    print(f"   找到 {len(df_offline_stb)} 台离线机顶盒")
    
    stb_count = 0
    stb_skip_closed = 0
    stb_skip_no_whitelist = 0
    
    for _, row in df_offline_stb.iterrows():
        store_id = str(row['设备编码'])
        
        # 跳过暂停营业门店
        if store_id in closed_stores:
            stb_skip_closed += 1
            continue
        
        # 跳过不在whitelist中的门店
        if store_id not in whitelist_dict:
            stb_skip_no_whitelist += 1
            continue
        
        whitelist_info = whitelist_dict[store_id]
        
        equipment = EquipmentStatus(
            store_id=store_id,
            store_name=whitelist_info['store_name'],
            war_zone=whitelist_info['war_zone'],
            regional_manager=whitelist_info['regional_manager'],
            equipment_type='机顶盒',
            equipment_id=store_id,
            equipment_name=str(row.get('名称', '')),
            status='离线',
            import_time=datetime.now()
        )
        session.add(equipment)
        stb_count += 1
    
    print(f"   导入 {stb_count} 条记录")
    print(f"   跳过暂停营业: {stb_skip_closed}")
    print(f"   跳过不在whitelist: {stb_skip_no_whitelist}")
    
except Exception as e:
    print(f"❌ 处理机顶盒数据失败: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
    session.close()
    sys.exit(1)

print()

# 7. 提交数据
print("💾 保存数据...")
try:
    session.commit()
    print(f"✅ 数据保存成功")
    print(f"   总计导入: {pos_count + stb_count} 条记录")
except Exception as e:
    print(f"❌ 保存数据失败: {e}")
    session.rollback()
    session.close()
    sys.exit(1)

# 8. 关闭连接
session.close()

print()
print("=" * 60)
print("✅ 设备异常数据导入完成！")
print("=" * 60)
print()
