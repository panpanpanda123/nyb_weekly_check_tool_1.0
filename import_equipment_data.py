#!/usr/bin/env python3
"""
设备异常数据导入脚本
Import Equipment Status Data

用法:
  python3 import_equipment_data.py              # 导入所有设备
  python3 import_equipment_data.py --only-pos   # 只导入POS
  python3 import_equipment_data.py --only-stb   # 只导入机顶盒
  python3 import_equipment_data.py --clear-pos  # 清空POS数据
  python3 import_equipment_data.py --clear-stb  # 清空机顶盒数据
"""
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent / 'viewer'))
sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentStatus, StoreWhitelist, EquipmentImportLog
)

# 解析命令行参数
parser = argparse.ArgumentParser(description='设备异常数据导入工具')
parser.add_argument('--only-pos', action='store_true', help='只导入POS数据')
parser.add_argument('--only-stb', action='store_true', help='只导入机顶盒数据')
parser.add_argument('--clear-pos', action='store_true', help='清空POS数据')
parser.add_argument('--clear-stb', action='store_true', help='清空机顶盒数据')
args = parser.parse_args()

# 确定导入模式
import_pos = not args.only_stb  # 默认导入POS，除非指定only-stb
import_stb = not args.only_pos  # 默认导入机顶盒，除非指定only-pos

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

print("=" * 60)
print("设备异常数据导入工具")
if args.only_pos:
    print("模式: 只导入POS")
elif args.only_stb:
    print("模式: 只导入机顶盒")
elif args.clear_pos:
    print("模式: 清空POS数据")
elif args.clear_stb:
    print("模式: 清空机顶盒数据")
else:
    print("模式: 导入所有设备")
print("=" * 60)
print()

# 1. 查找数据文件
print("📁 查找数据文件...")
project_root = Path(__file__).parent
equipment_dir = project_root / 'equipment_status'

# 查找最新的文件
pos_files = list(equipment_dir.glob('牛约堡集团_点餐设备表*.xlsx')) if import_pos else []
stb_files = list(equipment_dir.glob('202*.xlsx')) if import_stb else []
operating_store_files = list(equipment_dir.glob('*在营门店*.xlsx'))

# 检查必需文件
if import_pos and not pos_files:
    print("❌ 未找到收银设备文件（需要导入POS但文件不存在）")
    sys.exit(1)
if import_stb and not stb_files:
    print("❌ 未找到机顶盒文件（需要导入机顶盒但文件不存在）")
    sys.exit(1)
if not operating_store_files:
    print("❌ 未找到在营门店文件")
    sys.exit(1)

# 使用最新的文件
pos_file = max(pos_files, key=lambda p: p.stat().st_mtime) if pos_files else None
stb_file = max(stb_files, key=lambda p: p.stat().st_mtime) if stb_files else None
operating_store_file = max(operating_store_files, key=lambda p: p.stat().st_mtime)

# 提取文件时间信息
def extract_data_time(filename):
    """从文件名提取时间信息，格式：20260306_1131 -> 2026年3月6日 11:31"""
    import re
    match = re.search(r'(\d{8})_(\d{4})', filename)
    if match:
        date_str = match.group(1)  # 20260306
        time_str = match.group(2)  # 1131
        year = date_str[0:4]
        month = date_str[4:6].lstrip('0')
        day = date_str[6:8].lstrip('0')
        hour = time_str[0:2]
        minute = time_str[2:4]
        return f"{year}年{month}月{day}日 {hour}:{minute}"
    return None

pos_data_time = extract_data_time(pos_file.name) if pos_file else None
stb_data_time = extract_data_time(stb_file.name) if stb_file else None

if pos_file:
    print(f"✅ 找到收银设备文件: {pos_file.name}")
    if pos_data_time:
        print(f"   数据时间: {pos_data_time}")
if stb_file:
    print(f"✅ 找到机顶盒文件: {stb_file.name}")
    if stb_data_time:
        print(f"   数据时间: {stb_data_time}")
print(f"✅ 找到在营门店文件: {operating_store_file.name}")
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

# 3. 读取在营门店列表
print("📖 读取在营门店列表...")
try:
    # 读取"营业门店" sheet
    df_operating = pd.read_excel(operating_store_file, sheet_name='营业门店')
    
    # C列是门店ID，I列是营业状态
    # 只保留营业状态为"营业中"的门店
    operating_stores = set()
    for _, row in df_operating.iterrows():
        store_id = str(row.iloc[2]).strip()  # C列（索引2）
        status = str(row.iloc[8]).strip()     # I列（索引8）
        
        if status == '营业中':
            operating_stores.add(store_id)
    
    print(f"✅ 找到 {len(operating_stores)} 家营业中门店")
except Exception as e:
    print(f"❌ 读取在营门店文件失败: {e}")
    import traceback
    traceback.print_exc()
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
if import_pos and pos_file:
    print("📥 处理收银设备数据...")
    try:
        # 清空所有旧数据和处理记录（不管什么类型）
        print("   清空所有旧设备数据和处理记录...")
        from shared.database_models import EquipmentProcessing
        session.query(EquipmentProcessing).delete()
        session.query(EquipmentStatus).delete()
        session.commit()
        print("   ✅ 已清空所有旧数据和处理记录")
        
        df_pos = pd.read_excel(pos_file, header=1)
        
        # 筛选离线设备
        df_offline_pos = df_pos[df_pos['状态'] == '离线'].copy()
        print(f"   找到 {len(df_offline_pos)} 台离线收银设备")
        
        pos_count = 0
        pos_skip_not_operating = 0
        pos_skip_no_whitelist = 0
        
        for _, row in df_offline_pos.iterrows():
            store_id = str(row['设备编号'])
            
            # 只保留在营门店列表中的门店
            if store_id not in operating_stores:
                pos_skip_not_operating += 1
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
        print(f"   跳过非营业中: {pos_skip_not_operating}")
        print(f"   跳过不在whitelist: {pos_skip_no_whitelist}")
        
    except Exception as e:
        print(f"❌ 处理收银设备数据失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        session.close()
        sys.exit(1)
    
    print()
elif args.clear_pos:
    print("🗑️  清空POS数据...")
    try:
        from shared.database_models import EquipmentProcessing
        deleted_processing = session.query(EquipmentProcessing).filter(EquipmentProcessing.equipment_type == 'POS').delete()
        deleted_equipment = session.query(EquipmentStatus).filter(EquipmentStatus.equipment_type == 'POS').delete()
        session.commit()
        print(f"   ✅ 已清空 {deleted_equipment} 条POS设备记录")
        print(f"   ✅ 已清空 {deleted_processing} 条POS处理记录")
    except Exception as e:
        print(f"❌ 清空POS数据失败: {e}")
        session.rollback()
    print()
else:
    print("⏭️  跳过POS数据处理")
    print()

# 6. 处理机顶盒数据
if import_stb and stb_file:
    print("📥 处理机顶盒数据...")
    try:
        # 清空所有旧数据和处理记录（不管什么类型）
        print("   清空所有旧设备数据和处理记录...")
        from shared.database_models import EquipmentProcessing
        session.query(EquipmentProcessing).delete()
        session.query(EquipmentStatus).delete()
        session.commit()
        print("   ✅ 已清空所有旧数据和处理记录")
        
        df_stb = pd.read_excel(stb_file)
        
        # 筛选离线设备
        df_offline_stb = df_stb[df_stb['状态'] == '离线'].copy()
        print(f"   找到 {len(df_offline_stb)} 台离线机顶盒")
        
        stb_count = 0
        stb_skip_not_operating = 0
        stb_skip_no_whitelist = 0
        
        for _, row in df_offline_stb.iterrows():
            store_id = str(row['设备编码'])
            
            # 只保留在营门店列表中的门店
            if store_id not in operating_stores:
                stb_skip_not_operating += 1
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
        print(f"   跳过非营业中: {stb_skip_not_operating}")
        print(f"   跳过不在whitelist: {stb_skip_no_whitelist}")
        
    except Exception as e:
        print(f"❌ 处理机顶盒数据失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        session.close()
        sys.exit(1)
    
    print()
elif args.clear_stb:
    print("🗑️  清空机顶盒数据...")
    try:
        from shared.database_models import EquipmentProcessing
        deleted_processing = session.query(EquipmentProcessing).filter(EquipmentProcessing.equipment_type == '机顶盒').delete()
        deleted_equipment = session.query(EquipmentStatus).filter(EquipmentStatus.equipment_type == '机顶盒').delete()
        session.commit()
        print(f"   ✅ 已清空 {deleted_equipment} 条机顶盒设备记录")
        print(f"   ✅ 已清空 {deleted_processing} 条机顶盒处理记录")
    except Exception as e:
        print(f"❌ 清空机顶盒数据失败: {e}")
        session.rollback()
    print()
else:
    print("⏭️  跳过机顶盒数据处理")
    print()

# 7. 提交数据
if not args.clear_pos and not args.clear_stb:
    print("💾 保存数据...")
    try:
        session.commit()
        print(f"✅ 数据保存成功")
        total_imported = 0
        if import_pos and pos_file:
            total_imported += pos_count
        if import_stb and stb_file:
            total_imported += stb_count
        print(f"   总计导入: {total_imported} 条记录")
        
        # 记录导入日志
        import_type = 'POS' if (import_pos and not import_stb) else ('机顶盒' if (import_stb and not import_pos) else '全部')
        data_time = pos_data_time or stb_data_time
        file_name = (pos_file.name if pos_file else '') + ('; ' + stb_file.name if stb_file else '')
        
        log = EquipmentImportLog(
            import_type=import_type,
            file_name=file_name,
            data_time=data_time,
            import_time=datetime.now()
        )
        session.add(log)
        session.commit()
        
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
