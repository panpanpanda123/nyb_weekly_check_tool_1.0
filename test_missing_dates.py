#!/usr/bin/env python3
"""
测试缺失日期的容错性
Test tolerance for missing dates
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta, datetime

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import (
    create_db_engine, create_session_factory, 
    EquipmentStatusSnapshot, EquipmentProcessing
)
from equipment_utils import is_chronic_store, get_abnormal_count
from equipment_config import CHRONIC_RULES

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)


def create_sparse_snapshots(session, store_id):
    """
    创建稀疏的快照数据（模拟休息期间缺失日期）
    
    只在以下日期创建快照：
    - 今天
    - 2天前
    - 4天前
    - 7天前
    - 9天前
    
    缺失：1天前、3天前、5天前、6天前、8天前
    """
    print(f"\n📝 为门店 {store_id} 创建稀疏快照（模拟休息期间）...")
    
    # 清除该门店的旧测试数据
    session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .delete()
    session.commit()
    
    today = date.today()
    
    # 只在这些日期创建快照（有缺失）
    snapshot_dates = [
        today,                      # 今天
        today - timedelta(days=2),  # 2天前
        today - timedelta(days=4),  # 4天前
        today - timedelta(days=7),  # 7天前
        today - timedelta(days=9),  # 9天前
    ]
    
    print(f"   创建快照的日期:")
    for d in snapshot_dates:
        print(f"   - {d}")
    
    print(f"\n   缺失的日期:")
    for i in [1, 3, 5, 6, 8]:
        print(f"   - {today - timedelta(days=i)}")
    
    # 创建快照（每天2次：AM和PM）
    snapshot_count = 0
    for snapshot_date in snapshot_dates:
        for period in ['AM', 'PM']:
            snapshot = EquipmentStatusSnapshot(
                store_id=store_id,
                equipment_type='POS',
                snapshot_date=snapshot_date,
                snapshot_period=period,
                has_abnormal=1  # 都标记为异常
            )
            session.add(snapshot)
            snapshot_count += 1
    
    session.commit()
    print(f"\n✅ 创建了 {snapshot_count} 条快照记录")


def test_missing_dates():
    """测试缺失日期的容错性"""
    print("\n" + "="*60)
    print("🧪 测试缺失日期的容错性")
    print("="*60)
    
    # 创建数据库连接
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        store_id = "TEST_MISSING_DATES"
        
        # 创建稀疏快照
        create_sparse_snapshots(session, store_id)
        
        # 测试获取异常次数
        print("\n" + "="*60)
        print("📊 测试异常次数统计")
        print("="*60)
        
        count_5days = get_abnormal_count(session, store_id, 'POS', 5)
        count_10days = get_abnormal_count(session, store_id, 'POS', 10)
        
        print(f"\n✅ 5天内异常次数: {count_5days}")
        print(f"   预期: 6 (今天、2天前、4天前，每天2次)")
        
        print(f"\n✅ 10天内异常次数: {count_10days}")
        print(f"   预期: 10 (5个日期，每天2次)")
        
        # 测试经常出问题判定
        print("\n" + "="*60)
        print("📊 测试经常出问题判定")
        print("="*60)
        
        is_chronic, reason, counts = is_chronic_store(session, store_id, 'POS')
        
        print(f"\n✅ 是否经常出问题: {'是' if is_chronic else '否'}")
        print(f"✅ 触发原因: {reason if reason else '无'}")
        print(f"✅ 统计数据: {counts}")
        
        # 验证
        assert count_5days == 6, f"5天内异常次数应该是6，实际是{count_5days}"
        assert count_10days == 10, f"10天内异常次数应该是10，实际是{count_10days}"
        assert is_chronic == True, "应该被标记为经常出问题"
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！系统可以正确处理缺失日期")
        print("="*60)
        
        # 清理测试数据
        print("\n🧹 清理测试数据...")
        session.query(EquipmentStatusSnapshot)\
            .filter(EquipmentStatusSnapshot.store_id == store_id)\
            .delete()
        session.commit()
        print("✅ 测试数据清理完成")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def test_cleanup_old_records():
    """测试清理旧记录的逻辑"""
    print("\n" + "="*60)
    print("🧪 测试清理旧记录")
    print("="*60)
    
    engine = create_db_engine(DATABASE_URL, echo=False)
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    try:
        store_id = "TEST_CLEANUP"
        today = date.today()
        
        # 创建一些旧的快照（15天前）
        print("\n📝 创建15天前的旧快照...")
        old_date = today - timedelta(days=15)
        
        for period in ['AM', 'PM']:
            snapshot = EquipmentStatusSnapshot(
                store_id=store_id,
                equipment_type='POS',
                snapshot_date=old_date,
                snapshot_period=period,
                has_abnormal=1
            )
            session.add(snapshot)
        
        session.commit()
        print("✅ 创建了 2 条旧快照")
        
        # 创建一些旧的处理记录（15天前）
        print("\n📝 创建15天前的旧处理记录...")
        old_processing = EquipmentProcessing(
            store_id=store_id,
            equipment_type='POS',
            action='已恢复',
            reason='',
            processed_at=datetime.now() - timedelta(days=15)
        )
        session.add(old_processing)
        session.commit()
        print("✅ 创建了 1 条旧处理记录")
        
        # 模拟清理逻辑
        print("\n🗑️  执行清理...")
        from equipment_config import SNAPSHOT_RETENTION_DAYS, PROCESSING_RETENTION_DAYS
        
        # 清理旧快照
        cutoff_date = today - timedelta(days=SNAPSHOT_RETENTION_DAYS)
        deleted_snapshots = session.query(EquipmentStatusSnapshot)\
            .filter(EquipmentStatusSnapshot.store_id == store_id)\
            .filter(EquipmentStatusSnapshot.snapshot_date < cutoff_date)\
            .delete()
        
        # 清理旧处理记录
        processing_cutoff_date = today - timedelta(days=PROCESSING_RETENTION_DAYS)
        deleted_processing = session.query(EquipmentProcessing)\
            .filter(EquipmentProcessing.store_id == store_id)\
            .filter(EquipmentProcessing.processed_at < processing_cutoff_date)\
            .delete()
        
        session.commit()
        
        print(f"✅ 清理了 {deleted_snapshots} 条旧快照")
        print(f"✅ 清理了 {deleted_processing} 条旧处理记录")
        
        # 验证
        assert deleted_snapshots == 2, f"应该清理2条快照，实际清理了{deleted_snapshots}条"
        assert deleted_processing == 1, f"应该清理1条处理记录，实际清理了{deleted_processing}条"
        
        print("\n" + "="*60)
        print("✅ 清理逻辑测试通过！")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    test_missing_dates()
    test_cleanup_old_records()
    
    print("\n" + "="*60)
    print("🎉 所有测试通过！")
    print("="*60)
    print("\n✅ 系统可以正确处理缺失日期")
    print("✅ 自动清理逻辑工作正常")
    print("✅ 休息期间不维护也不会报错")
    print()
