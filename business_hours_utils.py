"""
门店营业时间解析工具
Business Hours Parsing Utility

支持的格式：
  [周一:08:30-23:00],[周二:08:30-23:00],...
  [周一:00:00-02:30,08:30-24:00],[周二:00:00-02:30,08:30-24:00],...
  每天可以有多个时间段，用逗号分隔
  24:00 表示当天结束（等同于次日 00:00）
  00:00-02:30 表示跨午夜延续段（前一天24:00的延续）
"""
import re
from datetime import datetime, date, timedelta


# 星期映射
WEEKDAY_MAP = {
    '周一': 0, '周二': 1, '周三': 2, '周四': 3,
    '周五': 4, '周六': 5, '周日': 6
}
WEEKDAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


def parse_business_hours(hours_str: str) -> dict:
    """
    解析营业时间字符串，返回每天的时间段列表（以分钟为单位）

    Args:
        hours_str: 营业时间字符串，如 "[周一:08:30-23:00],[周二:08:30-23:00],..."

    Returns:
        dict: {0: [(start_min, end_min), ...], 1: [...], ...}
              key 为 weekday (0=周一, 6=周日)
              时间段以分钟表示（0=00:00, 1440=24:00）
              跨午夜段：end_min > 1440 表示延续到次日
    """
    result = {i: [] for i in range(7)}

    if not hours_str or hours_str == 'nan':
        return result

    # 解析每个 [周X:...] 块
    pattern = r'\[(' + '|'.join(WEEKDAY_MAP.keys()) + r'):([^\]]+)\]'
    for match in re.finditer(pattern, hours_str):
        day_name = match.group(1)
        time_ranges_str = match.group(2)
        weekday = WEEKDAY_MAP[day_name]

        for time_range in time_ranges_str.split(','):
            time_range = time_range.strip()
            m = re.match(r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', time_range)
            if not m:
                continue
            sh, sm, eh, em = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            start_min = sh * 60 + sm
            end_min = eh * 60 + em  # 24:00 → 1440

            result[weekday].append((start_min, end_min))

    return result


def is_open_at(hours_str: str, check_dt: datetime) -> bool:
    """
    判断门店在指定时间点是否处于营业状态

    跨午夜逻辑：
      - 如果某天有 00:00-02:30 段，表示前一天 24:00 延续过来的
      - 判断时需要同时检查"当天的时间段"和"前一天跨午夜延续到今天的时间段"

    Args:
        hours_str: 营业时间字符串
        check_dt: 要检查的时间点

    Returns:
        bool: True=营业中，False=未营业
    """
    parsed = parse_business_hours(hours_str)
    if not any(parsed.values()):
        # 解析失败或为空，默认认为营业（保守策略，不误过滤）
        return True

    weekday = check_dt.weekday()  # 0=周一
    check_min = check_dt.hour * 60 + check_dt.minute

    # 1. 检查当天的时间段（排除 00:00 开头的跨午夜延续段）
    for start_min, end_min in parsed[weekday]:
        if start_min == 0 and end_min <= 240:
            # 这是跨午夜延续段（前一天的），跳过，在步骤2处理
            continue
        if start_min <= check_min < end_min:
            return True
        # 24:00 结尾特殊处理：end_min == 1440 表示到当天结束
        if end_min == 1440 and start_min <= check_min:
            return True

    # 2. 检查前一天是否有跨午夜延续到今天的时间段
    prev_weekday = (weekday - 1) % 7
    for start_min, end_min in parsed[prev_weekday]:
        if end_min == 1440:
            # 前一天到 24:00，今天 00:00 开始检查当天是否有延续段
            # 找今天 00:00 开头的延续段
            pass
        # 前一天有 24:00 结尾，今天的 00:00-X 段是延续
        # 实际上延续段已经在今天的 parsed[weekday] 里以 00:00-X 形式存在
        # 所以这里只需要检查今天 00:00 开头的段
    
    # 检查今天 00:00 开头的跨午夜延续段（来自前一天 24:00 的延续）
    for start_min, end_min in parsed[weekday]:
        if start_min == 0 and end_min <= 240:
            # 这是跨午夜延续段，check_min 在 [0, end_min) 内则营业
            if check_min < end_min:
                return True

    return False


def get_open_status_description(hours_str: str, check_dt: datetime) -> str:
    """
    返回营业状态描述，用于调试和展示

    Returns:
        str: 如 "营业中(08:30-23:00)" 或 "未营业(营业时间:10:00-22:00)"
    """
    parsed = parse_business_hours(hours_str)
    weekday = check_dt.weekday()
    day_name = WEEKDAY_NAMES[weekday]
    check_min = check_dt.hour * 60 + check_dt.minute

    if not parsed[weekday] and not any(parsed.values()):
        return "营业时间未知"

    is_open = is_open_at(hours_str, check_dt)

    # 格式化当天时间段
    def fmt_min(m):
        h, mn = divmod(m, 60)
        return f"{h:02d}:{mn:02d}"

    day_ranges = []
    for s, e in parsed[weekday]:
        day_ranges.append(f"{fmt_min(s)}-{fmt_min(e)}")
    ranges_str = ','.join(day_ranges) if day_ranges else '无'

    if is_open:
        return f"营业中({day_name}:{ranges_str})"
    else:
        return f"未营业({day_name}营业时间:{ranges_str})"
