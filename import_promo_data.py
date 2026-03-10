#!/usr/bin/env python3
"""
活动参与度数据导入脚本
Import Promo Participation Data Script
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import re

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import (
    create_db_engine,
    create_session_factory,
    init_viewer_db,
    PromoParticipation,
    PromoImportLog,
    StoreWhitelist
)

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

# 数据文件夹
DATA_FOLDER = Path(__file__).parent / 'promo_data'


def find_latest_participation_file():
    """查找最新的活动参与度文件"""
    if not DATA_FOLDER.exists():
        print(f"❌ 数据文件夹不存在: {DATA_FOLDER}")
        return None
    
    # 查找所有活动参与度文件（格式：活动参与度YYYY年MM月DD日.xlsx 或 活动参与度MM月DD日.xlsx）
    files = list(DATA_FOLDER.glob('活动参与度*.xlsx'))
    
    # 过滤掉临时文件
    files = [f for f in files if not f.name.startswith('~$')]
    
    if not files:
        print(f"❌ 未找到活动参与度文件")
        return None
    
    # 按修改时间排序，取最新的
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_file = files[0]
    
    print(f"✓ 找到最新文件: {latest_file.name}")
    return latest_file


def extract_date_from_filename(filename):
    """从文件名提取日期"""
    # 尝试匹配格式：活动参与度3月9日.xlsx
    match = re.search(r'(\d+)月(\d+)日', filename)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = datetime.now().year
        return f"{year}-{month:02d}-{day:02d}"
    
    # 尝试匹配格式：活动参与度2026年3月9日.xlsx
    match = re.search(r'(\d{4})年(\d+)月(\d+)日', filename)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return f"{year}-{month:02d}-{day:02d}"
    
    # 默认使用今天的日期
    return datetime.now().strftime('%Y-%m-%d')


def load_promo_stores():
    """加载3月活动门店表"""
    promo_store_file = DATA_FOLDER / '3月活动门店表.xlsx'
    
    if not promo_store_file.exists():
        print(f"❌ 未找到活动门店表: {promo_store_file}")
        return set()
    
    try:
        df = pd.read_excel(promo_store_file)
        
        # 假设第一列是门店ID
        if len(df.columns) > 0:
            store_ids = set(df.iloc[:, 0].astype(str).str.strip())
            print(f"✓ 加载活动门店表: {len(store_ids)} 个门店")
            return store_ids
        else:
            print(f"❌ 活动门店表格式错误")
            return set()
            
    except Exception as e:
        print(f"❌ 读取活动门店表失败: {str(e)}")
        return set()


def import_promo_data():
    """导入活动参与度数据"""
    print("="*60)
    print("活动参与度数据导入")
    print("="*60)
    
    # 创建数据库引擎
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    
    # 初始化数据库表
    init_viewer_db(engine)
    
    session = SessionFactory()
    
    try:
        # 1. 查找最新的活动参与度文件
        participation_file = find_latest_participation_file()
        if not participation_file:
            return
        
        # 2. 提取数据日期
        data_date = extract_date_from_filename(participation_file.name)
        print(f"✓ 数据日期: {data_date}")
        
        # 3. 加载活动门店列表
        promo_store_ids = load_promo_stores()
        if not promo_store_ids:
            print("⚠️  未找到活动门店表，将导入所有门店")
        
        # 4. 读取活动参与度数据
        print(f"\n正在读取: {participation_file.name}")
        df = pd.read_excel(participation_file)
        
        print(f"✓ 读取到 {len(df)} 行数据")
        print(f"✓ 列名: {list(df.columns)}")
        
        # 5. 获取白名单数据（用于匹配区域经理）
        whitelist_dict = {}
        whitelist_records = session.query(StoreWhitelist).all()
        for record in whitelist_records:
            whitelist_dict[record.store_id] = {
                'store_name': record.store_name,
                'war_zone': record.war_zone,
                'regional_manager': record.regional_manager
            }
        print(f"✓ 加载白名单: {len(whitelist_dict)} 个门店")
        
        # 6. 清空旧数据（同一日期的）
        deleted = session.query(PromoParticipation)\
            .filter(PromoParticipation.data_date == data_date)\
            .delete(synchronize_session=False)
        session.commit()
        print(f"✓ 清空旧数据: {deleted} 条")
        
        # 7. 导入新数据
        imported_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # A列：门店ID
                store_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
                
                if not store_id or store_id == 'nan':
                    skipped_count += 1
                    continue
                
                # 如果有活动门店表，只导入在表中的门店
                if promo_store_ids and store_id not in promo_store_ids:
                    skipped_count += 1
                    continue
                
                # 从白名单获取门店信息
                whitelist_info = whitelist_dict.get(store_id, {})
                store_name = whitelist_info.get('store_name', '')
                war_zone = whitelist_info.get('war_zone', '')
                regional_manager = whitelist_info.get('regional_manager', '')
                
                # F列：订单量
                order_count = int(row.iloc[5]) if pd.notna(row.iloc[5]) and str(row.iloc[5]).replace('.', '').isdigit() else 0
                
                # I列：权益卡销量
                benefit_card_sales = int(row.iloc[8]) if pd.notna(row.iloc[8]) and str(row.iloc[8]).replace('.', '').isdigit() else 0
                
                # J列：活动套餐销量
                promo_package_sales = int(row.iloc[9]) if pd.notna(row.iloc[9]) and str(row.iloc[9]).replace('.', '').isdigit() else 0
                
                # K列：活动参与度
                # 如果订单数为0，参与度直接设为0
                if order_count == 0:
                    participation_rate = '0'
                else:
                    # 尝试读取参与度值
                    if pd.notna(row.iloc[10]):
                        participation_rate = str(row.iloc[10]).strip()
                    else:
                        participation_rate = '0'
                
                # 创建记录
                record = PromoParticipation(
                    store_id=store_id,
                    store_name=store_name,
                    war_zone=war_zone,
                    regional_manager=regional_manager,
                    order_count=order_count,
                    benefit_card_sales=benefit_card_sales,
                    promo_package_sales=promo_package_sales,
                    participation_rate=participation_rate,
                    data_date=data_date
                )
                
                session.add(record)
                imported_count += 1
                
            except Exception as e:
                print(f"⚠️  第 {index+1} 行导入失败: {str(e)}")
                continue
        
        # 8. 提交事务
        session.commit()
        print(f"\n✓ 导入成功: {imported_count} 条")
        print(f"✓ 跳过: {skipped_count} 条")
        
        # 9. 记录导入日志
        log = PromoImportLog(
            data_date=data_date,
            records_count=imported_count
        )
        session.add(log)
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"✓ 活动参与度数据导入完成")
        print(f"  - 数据日期: {data_date}")
        print(f"  - 导入记录: {imported_count} 条")
        print(f"{'='*60}\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    import_promo_data()
