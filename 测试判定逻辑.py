#!/usr/bin/env python3
"""
测试设备异常判定逻辑
Test Equipment Abnormal Detection Logic
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from shared.database_models import create_db_engine, create_session_factory
from equipment_utils import is_chronic_store, get_unprocessed_dates
import os

# 数据库配置
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@127.0.0.1:5432/configurable_ops'
)

# 创建数据库引擎和会话
engine = create_db_engine(DATABASE_URL, echo=False)
SessionFactory = create_session_factory(engine)

def test_store(store_id: str, equipment_type: str = 'POS'):
    """测试单个门店的判定逻辑"""
    session = SessionFactory()
    
    try:
        print(f"\n{'='*60}")
        print(f"测试门店: {store_id} ({equipment_type})")
        print(f"{'='*60}")
        
        # 调用判定函数
        is_chronic, reason, counts = is_chronic_store(session, store_id, equipment_type)
        
        print(f"\n判定结果:")
        print(f"  是否经常出问题: {'是' if is_chronic else '否'}")
        print(f"  触发原因: {reason or '无'}")
        print(f"  统计数据: {counts}")
        
        # 如果有未处理日期，显示详细信息
        if 'unprocessed_dates' in counts and counts['unprocessed_dates']:
            print(f"\n未处理日期:")
            for date in counts['unprocessed_dates']:
                print(f"    - {date}")
        
        # 显示异常次数
        if '5days' in counts:
            print(f"\n异常次数统计:")
            print(f"  最近5天: {counts.get('5days', 0)}次")
            print(f"  最近10天: {counts.get('10days', 0)}次")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def test_unprocessed_dates(store_id: str, equipment_type: str = 'POS'):
    """测试未处理日期获取"""
    session = SessionFactory()
    
    try:
        print(f"\n{'='*60}")
        print(f"测试未处理日期: {store_id} ({equipment_type})")
        print(f"{'='*60}")
        
        unprocessed = get_unprocessed_dates(session, store_id, equipment_type, days=10)
        
        print(f"\n未处理日期列表:")
        if unprocessed:
            for date in unprocessed:
                print(f"  - {date}")
        else:
            print("  无未处理日期")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    print("设备异常判定逻辑测试")
    print("="*60)
    
    # 从命令行获取门店ID，或使用默认值
    if len(sys.argv) > 1:
        store_id = sys.argv[1]
    else:
        # 提示用户输入
        store_id = input("\n请输入要测试的门店ID（直接回车跳过）: ").strip()
        if not store_id:
            print("\n未输入门店ID，退出测试")
            sys.exit(0)
    
    # 测试判定逻辑
    test_store(store_id, 'POS')
    
    # 测试未处理日期
    test_unprocessed_dates(store_id, 'POS')
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}\n")
