#!/usr/bin/env python3
"""
查看设备异常处理记录（只读，不修改数据）
View Equipment Processing Records (Read-only)
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, date
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from shared.database_models import (
    create_db_engine, create_session_factory,
    EquipmentProcessing, EquipmentStatus, EquipmentStatusSnapshot
)

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

def view_processing_records(days=7):
    """查看最近N天的处理记录"""
    print("=" * 80)
    print(f"设备异常处理记录查询（最近{days}天）")
    print("=" * 80)
    print()
    
    # 连接数据库（只读）
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        # 查询最近N天的处理记录
        cutoff_date = datetime.now() - timedelta(days=days)
        
        records = session.query(EquipmentProcessing)\
            .filter(EquipmentProcessing.processed_at >= cutoff_date)\
            .order_by(EquipmentProcessing.processed_at.desc())\
            .all()
        
        if not records:
            print(f"📭 最近{days}天没有处理记录")
            return
        
        print(f"📊 找到 {len(records)} 条处理记录\n")
        
        # 按日期分组
        records_by_date = {}
        for record in records:
            date_key = record.processed_at.strftime('%Y-%m-%d')
            if date_key not in records_by_date:
                records_by_date[date_key] = []
            records_by_date[date_key].append(record)
        
        # 按日期显示
        for date_key in sorted(records_by_date.keys(), reverse=True):
            day_records = records_by_date[date_key]
            print(f"\n{'='*80}")
            print(f"📅 {date_key} ({len(day_records)} 条记录)")
            print(f"{'='*80}")
            
            # 按时段分组
            am_records = [r for r in day_records if r.processed_at.hour < 14]
            pm_records = [r for r in day_records if r.processed_at.hour >= 14]
            
            if am_records:
                print(f"\n🌅 上午 ({len(am_records)} 条)")
                print("-" * 80)
                for r in sorted(am_records, key=lambda x: x.processed_at):
                    time_str = r.processed_at.strftime('%H:%M:%S')
                    action_emoji = '✅' if r.action == '已恢复' else '⚠️'
                    print(f"{action_emoji} {time_str} | {r.store_id:6s} | {r.equipment_type:6s} | {r.action:6s} | {r.reason or '-'}")
            
            if pm_records:
                print(f"\n🌆 下午 ({len(pm_records)} 条)")
                print("-" * 80)
                for r in sorted(pm_records, key=lambda x: x.processed_at):
                    time_str = r.processed_at.strftime('%H:%M:%S')
                    action_emoji = '✅' if r.action == '已恢复' else '⚠️'
                    print(f"{action_emoji} {time_str} | {r.store_id:6s} | {r.equipment_type:6s} | {r.action:6s} | {r.reason or '-'}")
        
        # 统计信息
        print(f"\n{'='*80}")
        print("📈 统计信息")
        print(f"{'='*80}")
        
        total_recovered = sum(1 for r in records if r.action == '已恢复')
        total_not_recovered = sum(1 for r in records if r.action == '未恢复')
        
        print(f"总记录数: {len(records)}")
        print(f"已恢复: {total_recovered} ({total_recovered/len(records)*100:.1f}%)")
        print(f"未恢复: {total_not_recovered} ({total_not_recovered/len(records)*100:.1f}%)")
        
        # 按门店统计
        store_stats = {}
        for r in records:
            if r.store_id not in store_stats:
                store_stats[r.store_id] = {'recovered': 0, 'not_recovered': 0}
            if r.action == '已恢复':
                store_stats[r.store_id]['recovered'] += 1
            else:
                store_stats[r.store_id]['not_recovered'] += 1
        
        print(f"\n涉及门店数: {len(store_stats)}")
        
        # 找出处理次数最多的门店
        top_stores = sorted(store_stats.items(), 
                          key=lambda x: x[1]['recovered'] + x[1]['not_recovered'], 
                          reverse=True)[:10]
        
        if top_stores:
            print(f"\n处理次数最多的门店（Top 10）:")
            for store_id, stats in top_stores:
                total = stats['recovered'] + stats['not_recovered']
                print(f"  {store_id}: {total}次 (已恢复:{stats['recovered']}, 未恢复:{stats['not_recovered']})")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print()


def view_snapshots(days=7):
    """查看最近N天的快照记录"""
    print("=" * 80)
    print(f"设备异常快照记录查询（最近{days}天）")
    print("=" * 80)
    print()
    
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        cutoff_date = date.today() - timedelta(days=days)
        
        snapshots = session.query(EquipmentStatusSnapshot)\
            .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff_date)\
            .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
            .order_by(EquipmentStatusSnapshot.snapshot_date.desc())\
            .all()
        
        if not snapshots:
            print(f"📭 最近{days}天没有快照记录")
            return
        
        print(f"📊 找到 {len(snapshots)} 条快照记录\n")
        
        # 按日期分组
        snapshots_by_date = {}
        for snap in snapshots:
            snap_date = snap.snapshot_date.date() if hasattr(snap.snapshot_date, 'date') else snap.snapshot_date
            date_key = snap_date.strftime('%Y-%m-%d')
            if date_key not in snapshots_by_date:
                snapshots_by_date[date_key] = {'AM': [], 'PM': []}
            snapshots_by_date[date_key][snap.snapshot_period].append(snap)
        
        # 按日期显示
        for date_key in sorted(snapshots_by_date.keys(), reverse=True):
            day_snaps = snapshots_by_date[date_key]
            am_count = len(day_snaps['AM'])
            pm_count = len(day_snaps['PM'])
            total_count = am_count + pm_count
            
            print(f"\n{'='*80}")
            print(f"📅 {date_key} (上午:{am_count}, 下午:{pm_count}, 总计:{total_count})")
            print(f"{'='*80}")
            
            if am_count > 0:
                print(f"🌅 上午异常门店: {am_count} 家")
                store_ids = [s.store_id for s in day_snaps['AM']]
                print(f"   {', '.join(store_ids[:20])}" + (" ..." if len(store_ids) > 20 else ""))
            
            if pm_count > 0:
                print(f"🌆 下午异常门店: {pm_count} 家")
                store_ids = [s.store_id for s in day_snaps['PM']]
                print(f"   {', '.join(store_ids[:20])}" + (" ..." if len(store_ids) > 20 else ""))
            
            # 找出当天反复的门店（AM+PM都有异常）
            am_stores = set(s.store_id for s in day_snaps['AM'])
            pm_stores = set(s.store_id for s in day_snaps['PM'])
            repeat_stores = am_stores & pm_stores
            
            if repeat_stores:
                print(f"🔄 当天反复门店: {len(repeat_stores)} 家")
                print(f"   {', '.join(list(repeat_stores)[:20])}" + (" ..." if len(repeat_stores) > 20 else ""))
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print()


def export_to_excel(days=7):
    """导出处理记录到Excel"""
    print("=" * 80)
    print(f"导出处理记录到Excel（最近{days}天）")
    print("=" * 80)
    print()
    
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        records = session.query(EquipmentProcessing)\
            .filter(EquipmentProcessing.processed_at >= cutoff_date)\
            .order_by(EquipmentProcessing.processed_at.desc())\
            .all()
        
        if not records:
            print(f"📭 最近{days}天没有处理记录")
            return
        
        # 转换为DataFrame
        data = []
        for r in records:
            data.append({
                '处理时间': r.processed_at.strftime('%Y-%m-%d %H:%M:%S'),
                '日期': r.processed_at.strftime('%Y-%m-%d'),
                '时段': '上午' if r.processed_at.hour < 14 else '下午',
                '门店ID': r.store_id,
                '设备类型': r.equipment_type,
                '处理动作': r.action,
                '未恢复原因': r.reason or '',
                '预计恢复日期': r.expected_recovery_date.strftime('%Y-%m-%d') if r.expected_recovery_date else ''
            })
        
        df = pd.DataFrame(data)
        
        # 保存到Excel
        filename = f'处理记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(filename, index=False, sheet_name='处理记录')
        
        print(f"✅ 导出成功: {filename}")
        print(f"   记录数: {len(records)}")
        
    except Exception as e:
        print(f"❌ 导出失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
    
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='查看设备异常处理记录（只读）')
    parser.add_argument('--days', type=int, default=7, help='查询最近N天的记录（默认7天）')
    parser.add_argument('--snapshots', action='store_true', help='查看快照记录')
    parser.add_argument('--export', action='store_true', help='导出到Excel')
    
    args = parser.parse_args()
    
    if args.snapshots:
        view_snapshots(args.days)
    elif args.export:
        export_to_excel(args.days)
    else:
        view_processing_records(args.days)
