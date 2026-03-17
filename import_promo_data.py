#!/usr/bin/env python3
"""
活动参与度数据导入脚本（新版）
从「3月活动门店数据概览.xlsx」的明细sheet导入数据
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import re

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import (
    create_db_engine,
    create_session_factory,
    init_viewer_db,
    PromoParticipation,
    PromoImportLog,
)

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

DATA_FOLDER = Path(__file__).parent / 'promo_data'
DATA_FILE = '3月活动门店数据概览.xlsx'


def find_data_file():
    """查找数据文件"""
    filepath = DATA_FOLDER / DATA_FILE
    if filepath.exists():
        print(f"✓ 找到数据文件: {filepath.name}")
        return filepath
    
    # fallback: 查找任何概览文件
    files = list(DATA_FOLDER.glob('*数据概览*.xlsx'))
    files = [f for f in files if not f.name.startswith('~$')]
    if files:
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        print(f"✓ 找到数据文件: {files[0].name}")
        return files[0]
    
    print(f"❌ 未找到数据文件，请将文件放入 {DATA_FOLDER}")
    return None


def extract_date_range_from_sheet_name(sheet_name):
    """从sheet名提取日期区间，如 '活动数据明细-3.9-15' -> '3月9日-15日'"""
    match = re.search(r'(\d+)\.(\d+)-(\d+)', sheet_name)
    if match:
        month = match.group(1)
        start_day = match.group(2)
        end_day = match.group(3)
        return f"{month}月{start_day}日-{end_day}日"
    return sheet_name


def import_promo_data():
    """导入活动参与度数据"""
    print("=" * 60)
    print("活动参与度数据导入（新版）")
    print("=" * 60)

    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    init_viewer_db(engine)
    session = SessionFactory()

    try:
        # 1. 查找数据文件
        filepath = find_data_file()
        if not filepath:
            return

        # 2. 读取Excel，找到明细sheet
        xls = pd.ExcelFile(filepath)
        print(f"✓ Sheet列表: {xls.sheet_names}")

        detail_sheet = None
        for name in xls.sheet_names:
            if '明细' in name:
                detail_sheet = name
                break

        if not detail_sheet:
            print("❌ 未找到包含'明细'的sheet")
            return

        data_date = extract_date_range_from_sheet_name(detail_sheet)
        print(f"✓ 数据区间: {data_date}")
        print(f"✓ 使用sheet: {detail_sheet}")

        # 3. 读取明细数据
        df = pd.read_excel(xls, sheet_name=detail_sheet)
        print(f"✓ 读取到 {len(df)} 行数据")
        print(f"✓ 列名: {list(df.columns)}")

        # 列名映射（处理换行符）
        col_map = {}
        for col in df.columns:
            clean = col.replace('\n', '')
            col_map[col] = clean
        df.rename(columns=col_map, inplace=True)
        print(f"✓ 清理后列名: {list(df.columns)}")

        # 4. 清空所有旧数据
        deleted = session.query(PromoParticipation).delete(synchronize_session=False)
        session.commit()
        print(f"✓ 清空旧数据: {deleted} 条")

        # 5. 导入新数据
        imported = 0
        skipped = 0

        for _, row in df.iterrows():
            try:
                store_id = str(row.get('门店ID', '')).strip()
                if not store_id or store_id == 'nan':
                    skipped += 1
                    continue

                record = PromoParticipation(
                    store_id=store_id,
                    store_name=str(row.get('门店名称', '')).strip(),
                    city_operator=str(row.get('省市运营', '')).strip(),
                    war_zone=str(row.get('战区', '')).strip(),
                    war_zone_manager=str(row.get('战区经理', '')).strip(),
                    regional_manager=str(row.get('区域经理', '')).strip(),
                    order_count=int(row.get('堂食pos+扫码点餐订单量', 0)) if pd.notna(row.get('堂食pos+扫码点餐订单量')) else 0,
                    pos_order_count=int(row.get('pos订单量', 0)) if pd.notna(row.get('pos订单量')) else 0,
                    scan_order_count=int(row.get('扫码点餐订单量', 0)) if pd.notna(row.get('扫码点餐订单量')) else 0,
                    benefit_card_sales=int(row.get('权益卡售卖数量', 0)) if pd.notna(row.get('权益卡售卖数量')) else 0,
                    promo_package_sales=int(row.get('活动套餐售卖数量', 0)) if pd.notna(row.get('活动套餐售卖数量')) else 0,
                    participation_rate=float(row.get('活动参与度', 0)) if pd.notna(row.get('活动参与度')) else 0.0,
                    data_date=data_date,
                )
                session.merge(record)  # merge = upsert by PK
                imported += 1
            except Exception as e:
                print(f"⚠️  行导入失败: {e}")
                skipped += 1

        session.commit()
        print(f"\n✓ 导入成功: {imported} 条")
        print(f"✓ 跳过: {skipped} 条")

        # 6. 记录导入日志
        log = PromoImportLog(
            data_date=data_date,
            records_count=imported,
        )
        session.add(log)
        session.commit()

        print(f"\n{'=' * 60}")
        print(f"✓ 导入完成 - {data_date} - {imported} 条记录")
        print(f"{'=' * 60}\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    import_promo_data()
