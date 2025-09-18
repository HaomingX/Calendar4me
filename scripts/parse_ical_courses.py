#!/usr/bin/env python3
"""
解析iCal数据并创建周期性课程事件
"""
import re
from datetime import datetime, timezone, timedelta
import json

# 你的iCal数据
ical_data = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//YZune//WakeUpSchedule//EN
BEGIN:VTIMEZONE
TZID:Asia/Shanghai
LAST-MODIFIED:20250410T142247Z
TZURL:https://www.tzurl.org/zoneinfo-outlook/Asia/Shanghai
X-LIC-LOCATION:Asia/Shanghai
BEGIN:STANDARD
TZNAME:CST
TZOFFSETFROM:+0800
TZOFFSETTO:+0800
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-1729b7e6-9403-4f2b-a3f4-add6a974f7ec
SUMMARY:电子信息工程中的数学模型与方法
DTSTART;TZID=Asia/Shanghai:20250915T080000
DTEND;TZID=Asia/Shanghai:20250915T093500
RRULE:FREQ=WEEKLY;UNTIL=20251109T160000Z;INTERVAL=1
LOCATION:线上 
DESCRIPTION:线上
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:电子信息工程中的数学模型与方法@线上\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-6d9e8a97-4ac2-4153-96df-6eed1dd99ad9
SUMMARY:人工智能算法与系统
DTSTART;TZID=Asia/Shanghai:20250915T185000
DTEND;TZID=Asia/Shanghai:20250915T220500
RRULE:FREQ=WEEKLY;UNTIL=20251109T160000Z;INTERVAL=1
LOCATION:线上 
DESCRIPTION:线上
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:人工智能算法与系统@线上\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-cc6dca31-83ee-4606-9ae6-7bfe0dd0a6ef
SUMMARY:职业能力和创业教育
DTSTART;TZID=Asia/Shanghai:20251110T180000
DTEND;TZID=Asia/Shanghai:20251110T184500
RRULE:FREQ=WEEKLY;UNTIL=20260104T160000Z;INTERVAL=1
LOCATION:阶梯教室 
DESCRIPTION:阶梯教室
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:职业能力和创业教育@阶梯教室\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-b16b0905-289d-4433-9fa1-cb92e3157c20
SUMMARY:电子信息工程中的数学模型与方法
DTSTART;TZID=Asia/Shanghai:20250918T080000
DTEND;TZID=Asia/Shanghai:20250918T093500
RRULE:FREQ=WEEKLY;UNTIL=20251112T160000Z;INTERVAL=1
LOCATION:线上 
DESCRIPTION:线上
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:电子信息工程中的数学模型与方法@线上\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-a34a0859-0934-4e9f-8806-ca16be93e53a
SUMMARY:知识图谱构建与应用
DTSTART;TZID=Asia/Shanghai:20250918T133000
DTEND;TZID=Asia/Shanghai:20250918T165500
RRULE:FREQ=WEEKLY;UNTIL=20251112T160000Z;INTERVAL=1
LOCATION:209 
DESCRIPTION:209
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:知识图谱构建与应用@209\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-77cb338f-beb9-4b7b-9b11-6ad132344df4
SUMMARY:数据科学前沿
DTSTART;TZID=Asia/Shanghai:20251113T083000
DTEND;TZID=Asia/Shanghai:20251113T115000
RRULE:FREQ=WEEKLY;UNTIL=20260107T160000Z;INTERVAL=1
LOCATION:209 
DESCRIPTION:209
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:数据科学前沿@209\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-17bdf3e0-46d2-4bd7-a787-263dd60a9703
SUMMARY:工程前沿技术讲座
DTSTART;TZID=Asia/Shanghai:20250917T185000
DTEND;TZID=Asia/Shanghai:20250917T202500
RRULE:FREQ=WEEKLY;UNTIL=20260106T160000Z;INTERVAL=1
LOCATION:线上 
DESCRIPTION:线上
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:工程前沿技术讲座@线上\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-e0dad0c2-7d0a-4343-921d-574b52283327
SUMMARY:自然语言处理
DTSTART;TZID=Asia/Shanghai:20251112T083000
DTEND;TZID=Asia/Shanghai:20251112T115000
RRULE:FREQ=WEEKLY;UNTIL=20260106T160000Z;INTERVAL=1
LOCATION:107 
DESCRIPTION:107
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:自然语言处理@107\n
END:VALARM
END:VEVENT
BEGIN:VEVENT
DTSTAMP:20250918T090003Z
UID:WakeUpSchedule-1cc212a7-9c4e-46b4-92c7-a718d8785d3e
SUMMARY:智能移动应用技术
DTSTART;TZID=Asia/Shanghai:20250916T083000
DTEND;TZID=Asia/Shanghai:20250916T115000
RRULE:FREQ=WEEKLY;UNTIL=20251110T160000Z;INTERVAL=1
LOCATION:310 
DESCRIPTION:310
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT20M
DESCRIPTION:智能移动应用技术@310\n
END:VALARM
END:VEVENT
END:VCALENDAR'''

def parse_ical_events(ical_data):
    """解析iCal数据，提取事件信息"""
    events = []
    current_event = {}
    
    for line in ical_data.split('\n'):
        line = line.strip()
        if line == 'BEGIN:VEVENT':
            current_event = {}
        elif line == 'END:VEVENT':
            if current_event:
                events.append(current_event)
        elif ':' in line:
            key, value = line.split(':', 1)
            current_event[key] = value
    
    return events

def parse_rrule(rrule):
    """解析RRULE"""
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
    
    return result

def parse_ical_time(time_str):
    """解析iCal时间格式 - 修复版本"""
    # 直接解析时间字符串，假设是北京时间
    if len(time_str) == 15:  # 格式: 20250915T080000
        dt = datetime.strptime(time_str, '%Y%m%dT%H%M%S')
        dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))  # 北京时间
        return dt.astimezone(timezone.utc)
    return None

def generate_recurring_course_data():
    """生成周期性课程数据"""
    events = parse_ical_events(ical_data)
    courses = []
    
    print(f"解析到 {len(events)} 个事件")
    
    for i, event in enumerate(events):
        print(f"\n事件 {i+1}: {event.get('SUMMARY', 'Unknown')}")
        
        if 'SUMMARY' not in event:
            print(f"  跳过：没有SUMMARY")
            continue
        
        # 查找时间字段（键名可能包含分号）
        start_time_str = None
        end_time_str = None
        
        for key, value in event.items():
            if key.startswith('DTSTART'):
                start_time_str = value
            elif key.startswith('DTEND'):
                end_time_str = value
        
        print(f"  开始时间字符串: {start_time_str}")
        print(f"  结束时间字符串: {end_time_str}")
        
        if not start_time_str or not end_time_str:
            print(f"  跳过：时间字段缺失")
            continue
        
        # 解析时间
        start_time = parse_ical_time(start_time_str)
        end_time = parse_ical_time(end_time_str)
        
        print(f"  解析后开始时间: {start_time}")
        print(f"  解析后结束时间: {end_time}")
        
        if not start_time or not end_time:
            print(f"  跳过：时间解析失败")
            continue
        
        # 解析RRULE
        rrule_data = parse_rrule(event.get('RRULE', ''))
        print(f"  RRULE数据: {rrule_data}")
        
        course = {
            'title': event['SUMMARY'],
            'description': event.get('DESCRIPTION', ''),
            'category': 'course',
            'location': event.get('LOCATION', ''),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'reminder_minutes_before': 20,
            'is_recurring': True,
            'recurrence_frequency': rrule_data.get('frequency', 'weekly'),
            'recurrence_interval': rrule_data.get('interval', 1),
            'recurrence_end_date': rrule_data.get('until_date').isoformat() if rrule_data.get('until_date') else None,
        }
        courses.append(course)
        print(f"  ✅ 添加课程: {course['title']}")
    
    return courses

if __name__ == "__main__":
    courses = generate_recurring_course_data()
    print(f"\n总共解析到 {len(courses)} 门周期性课程:")
    
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course['title']} - {course['location']}")
        print(f"   开始: {course['start_time']}")
        print(f"   重复: {course['recurrence_frequency']} (间隔{course['recurrence_interval']}周)")
        print(f"   结束: {course['recurrence_end_date']}")
        print()
    
    # 保存为JSON
    with open('recurring_courses.json', 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    
    print(f"周期性课程数据已保存到 recurring_courses.json")
