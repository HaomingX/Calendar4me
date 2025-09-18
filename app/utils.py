#!/usr/bin/env python3
"""
周期性事件处理工具
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import re


def parse_rrule(rrule: str) -> dict:
    """解析RRULE字符串"""
    if not rrule:
        return {}
    
    result = {}
    parts = rrule.split(';')
    
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            result[key] = value
    
    return result


def generate_recurrence_dates(
    start_date: datetime,
    end_date: datetime,
    frequency: str = "weekly",
    interval: int = 1,
    until_date: Optional[datetime] = None,
    count: Optional[int] = None
) -> List[tuple]:
    """
    生成重复事件的日期列表
    
    Args:
        start_date: 开始日期
        end_date: 结束日期（单次事件的持续时间）
        frequency: 重复频率 (daily, weekly, monthly)
        interval: 重复间隔
        until_date: 重复结束日期
        count: 重复次数（可选）
    
    Returns:
        List[tuple]: [(start_time, end_time), ...]
    """
    dates = []
    current_start = start_date
    current_end = end_date
    
    # 计算持续时间
    duration = end_date - start_date
    
    # 确定结束条件
    if count:
        max_iterations = count
    elif until_date:
        max_iterations = 1000  # 设置一个合理的上限
    else:
        max_iterations = 52  # 默认最多52周
    
    iteration = 0
    while iteration < max_iterations:
        # 检查是否超过结束日期
        if until_date and current_start > until_date:
            break
            
        dates.append((current_start, current_end))
        
        # 计算下一次重复
        if frequency == "daily":
            current_start += timedelta(days=interval)
        elif frequency == "weekly":
            current_start += timedelta(weeks=interval)
        elif frequency == "monthly":
            # 简单的月份计算，不考虑月份天数差异
            current_start += timedelta(days=30 * interval)
        else:
            break
            
        current_end = current_start + duration
        iteration += 1
    
    return dates


def create_rrule_string(
    frequency: str = "weekly",
    interval: int = 1,
    until_date: Optional[datetime] = None,
    count: Optional[int] = None
) -> str:
    """创建RRULE字符串"""
    parts = [f"FREQ={frequency.upper()}"]
    
    if interval > 1:
        parts.append(f"INTERVAL={interval}")
    
    if until_date:
        # 转换为UTC并格式化为RRULE格式
        utc_date = until_date.astimezone(timezone.utc)
        parts.append(f"UNTIL={utc_date.strftime('%Y%m%dT%H%M%SZ')}")
    
    if count:
        parts.append(f"COUNT={count}")
    
    return ";".join(parts)


def parse_ical_rrule(rrule: str) -> dict:
    """解析iCal格式的RRULE"""
    result = {}
    
    # 解析FREQ
    freq_match = re.search(r'FREQ=(\w+)', rrule)
    if freq_match:
        result['frequency'] = freq_match.group(1).lower()
    
    # 解析INTERVAL
    interval_match = re.search(r'INTERVAL=(\d+)', rrule)
    if interval_match:
        result['interval'] = int(interval_match.group(1))
    else:
        result['interval'] = 1
    
    # 解析UNTIL
    until_match = re.search(r'UNTIL=(\d{8}T\d{6}Z)', rrule)
    if until_match:
        until_str = until_match.group(1)
        until_date = datetime.strptime(until_str, '%Y%m%dT%H%M%SZ')
        until_date = until_date.replace(tzinfo=timezone.utc)
        result['until_date'] = until_date
    
    # 解析COUNT
    count_match = re.search(r'COUNT=(\d+)', rrule)
    if count_match:
        result['count'] = int(count_match.group(1))
    
    return result


def get_week_number(start_date: datetime, reference_date: datetime) -> int:
    """计算从开始日期到参考日期的周数"""
    delta = reference_date - start_date
    return (delta.days // 7) + 1


def is_date_in_range(date: datetime, start_date: datetime, end_date: datetime) -> bool:
    """检查日期是否在指定范围内"""
    return start_date <= date <= end_date
