"""
设备异常监控工具函数
Equipment Monitoring Utility Functions
"""
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from shared.database_models import EquipmentStatusSnapshot, EquipmentProcessing
from equipment_config import CHRONIC_RULES, SNAPSHOT_RETENTION_DAYS


def get_abnormal_count(session: Session, store_id: str, equipment_type: str, days: int) -> int:
    """
    获取最近N天内的异常次数
    
    Args:
        session: 数据库会话
        store_id: 门店ID
        equipment_type: 设备类型（POS/机顶盒）
        days: 天
        
    Returns:
        int: 异常次数
    """
    cutoff_date = date.today() - timedelta(days=days)
    
    count = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .filter(EquipmentStatusSnapshot.equipment_type == equipment_type)\
        .filter(EquipmentStatusSnapshot.snapshot_date >= cutoff_date)\
        .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
        .count()
    
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
        例如: (True, "5天内3次", {'5days': 3, '10days': 4})
    """
    # 只对POS启用历史追踪
    if equipment_type != 'POS':
        return False, None, {}
    
    # 规则1: 当天上午有异常+处理过+下午又异常 = 立即标记
    today = date.today()
    
    # 检查今天上午是否有异常
    am_abnormal = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .filter(EquipmentStatusSnapshot.equipment_type == equipment_type)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'AM')\
        .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
        .first()
    
    # 检查今天下午是否有异常
    pm_abnormal = session.query(EquipmentStatusSnapshot)\
        .filter(EquipmentStatusSnapshot.store_id == store_id)\
        .filter(EquipmentStatusSnapshot.equipment_type == equipment_type)\
        .filter(EquipmentStatusSnapshot.snapshot_date == today)\
        .filter(EquipmentStatusSnapshot.snapshot_period == 'PM')\
        .filter(EquipmentStatusSnapshot.has_abnormal == 1)\
        .first()
    
    # 检查今天是否处理过
    today_processing = session.query(EquipmentProcessing)\
        .filter(EquipmentProcessing.store_id == store_id)\
        .filter(EquipmentProcessing.equipment_type == equipment_type)\
        .filter(EquipmentProcessing.processed_at >= datetime.combine(today, datetime.min.time()))\
        .first()
    
    if am_abnormal and pm_abnormal and today_processing:
        # 上午有问题 + 处理过 + 下午又有问题 = 立即标记
        return True, "当天反复", {'today_repeat': 1}
    
    # 规则2: 计算各个时间窗口的异常次数
    abnormal_counts = {}
    for rule in CHRONIC_RULES:
        days = rule['days']
        count = get_abnormal_count(session, store_id, equipment_type, days)
        abnormal_counts[f'{days}days'] = count
    
    # 检查是否满足任一规则
    for rule in CHRONIC_RULES:
        days = rule['days']
        threshold = rule['threshold']
        count = abnormal_counts[f'{days}days']
        
        if count >= threshold:
            reason = f"{days}天{count}次"
            return True, reason, abnormal_counts
    
    return False, None, abnormal_counts


def should_suppress(session: Session, store_id: str, equipment_type: str) -> bool:
    """
    判断是否应该暂时不提示
    
    Args:
        session: 数据库会话
        store_id: 门店ID
        equipment_type: 设备类型
        
    Returns:
        bool: 是否应该暂时不提示
    """
    processing = session.query(EquipmentProcessing)\
        .filter(EquipmentProcessing.store_id == store_id)\
        .filter(EquipmentProcessing.equipment_type == equipment_type)\
        .first()
    
    if processing and processing.suppressed_until:
        # 如果还在暂时不提示期内
        if processing.suppressed_until.date() >= date.today():
            return True
    
    return False


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
