"""
设备异常监控工具函数
Equipment Monitoring Utility Functions
"""
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from shared.database_models import EquipmentStatusSnapshot, EquipmentProcessing
from equipment_config import CHRONIC_RULES, SNAPSHOT_RETENTION_DAYS


def get_abnormal_count(session: Session, store_id: str, equipment_type: str, days: int, exclude_today: bool = True) -> int:
    """
    获取最近N天内的异常次数
    
    Args:
        session: 数据库会话
        store_id: 门店ID
        equipment_type: 设备类型（POS/机顶盒）
        days: 天
        exclude_today: 是否排除今天（默认True，避免第一天就触发）
        
    Returns:
        int: 异常次数
    """
    cutoff_date = date.today() - timedelta(days=days)
    
    query = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .filter(EquipmentStatusSnapshot.equipment_type == equipment_type)\
        .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff_date)\
        .filter(EquipmentStatusSnapshot.has_abnormal == 1)
    
    # 排除今天的快照（避免第一天就触发"经常出问题"）
    if exclude_today:
        today_start = datetime.combine(date.today(), datetime.min.time())
        query = query.filter(EquipmentStatusSnapshot.snapshot_date < today_start)
    
    count = query.count()
    
    return count


def is_chronic_store(session: Session, store_id: str, equipment_type: str) -> tuple:
    """
    判断是否经常出问题
    
    Args:
        session: 数据库会话
        store_id: 门店ID
        equipment_type: 设备类型（POS/机顶盒）
        
    Returns:
        tuple: (是否经常出问题, 触发原因描述, 异常次数字典)
        例如: (True, "多次出问题（当天反复）", {'5days': 3, '10days': 4, 'today_repeat': 1, 'unprocessed_dates': ['03-09']})
    """
    # 只对POS启用历史追踪
    if equipment_type != 'POS':
        return False, None, {}
    
    # 规则1: 当天上午有异常+标记已恢复+下午又异常 = 立即标记"当天反复"
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 检查今天上午是否有异常快照
    am_abnormal = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .filter(EquipmentStatusSnapshot.equipment_type == equipment_type)\
        .filter(EquipmentStatusSnapshot.snapshot_date >= today_start)\
        .filter(EquipmentStatusSnapshot.snapshot_date <= today_end)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'AM')\
        .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
        .first()
    
    # 检查今天下午是否有异常快照
    pm_abnormal = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .filter(EquipmentStatusSnapshot.equipment_type == equipment_type)\
        .filter(EquipmentStatusSnapshot.snapshot_date >= today_start)\
        .filter(EquipmentStatusSnapshot.snapshot_date <= today_end)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'PM')\
        .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
        .first()
    
    # 检查今天是否有处理记录
    today_processing = session.query(EquipmentProcessing)\
        .filter(EquipmentProcessing.store_id == store_id)\
        .filter(EquipmentProcessing.equipment_type == equipment_type)\
        .filter(EquipmentProcessing.processed_at >= today_start)\
        .first()
    
    # 情况1：上午有异常 + 标记"已恢复" + 下午又有异常 = 当天反复
    if am_abnormal and pm_abnormal and today_processing and today_processing.action == '已恢复':
        return True, "多次出问题（当天反复）", {'today_repeat': 1}
    
    # 情况2：上午有异常 + 下午有异常 + 没有处理 = 未处理
    # 注意：只有当下午快照存在时才判定（说明已经到下午了）
    unprocessed_dates = []
    if am_abnormal and pm_abnormal and not today_processing:
        unprocessed_dates.append(today.strftime('%m-%d'))
        return True, "多次出问题（未及时处理）", {'unprocessed': 1, 'unprocessed_dates': unprocessed_dates}
    
    # 规则2: 计算各个时间窗口的异常次数（排除今天，避免第一天就触发）
    abnormal_counts = {}
    for rule in CHRONIC_RULES:
        days = rule['days']
        count = get_abnormal_count(session, store_id, equipment_type, days, exclude_today=True)
        abnormal_counts[f'{days}days'] = count
    
    # 检查是否满足任一规则
    for rule in CHRONIC_RULES:
        days = rule['days']
        threshold = rule['threshold']
        count = abnormal_counts[f'{days}days']
        
        if count >= threshold:
            reason = f"多次出问题（{days}天{count}次）"
            return True, reason, abnormal_counts
    
    return False, None, abnormal_counts


def should_suppress(session: Session, store_id: str, equipment_type: str) -> bool:
    """
    判断是否应该暂时不提示（在预计恢复期内）
    
    Args:
        session: 数据库会话
        store_id: 门店ID
        equipment_type: 设备类型
        
    Returns:
        bool: True=暂时不提示（在预计恢复期内），False=需要提示
    """
    # 查询最新的处理记录
    processing = session.query(EquipmentProcessing)\
        .filter(EquipmentProcessing.store_id == store_id)\
        .filter(EquipmentProcessing.equipment_type == equipment_type)\
        .order_by(EquipmentProcessing.processed_at.desc())\
        .first()
    
    if processing and processing.suppressed_until:
        # 如果还在暂时不提示期内（预计恢复日期未到）
        today = date.today()
        suppressed_date = processing.suppressed_until.date() if hasattr(processing.suppressed_until, 'date') else processing.suppressed_until
        
        if suppressed_date >= today:
            return True  # 暂时不提示
    
    return False  # 需要提示


def calculate_chronic_stats(session: Session, store_ids: list) -> dict:
    """
    批量计算门店的经常出问题统计
    
    Args:
        session: 数据库会话
        store_ids: 门店ID列表
        
    Returns:
        dict: {store_id: {'is_chronic': bool, 'reason': str, 'counts': dict}}
    """
    stats = {}
    
    for store_id in store_ids:
        # 只对POS计算
        is_chronic, reason, counts = is_chronic_store(session, store_id, 'POS')
        stats[store_id] = {
            'is_chronic': is_chronic,
            'chronic_reason': reason,
            'abnormal_count_5days': counts.get('5days', 0),
            'abnormal_count_10days': counts.get('10days', 0)
        }
    
    return stats
