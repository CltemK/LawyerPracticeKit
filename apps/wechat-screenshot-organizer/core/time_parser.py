"""
时间解析模块
从OCR识别的文本中提取和解析微信聊天记录的时间戳
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


class TimeParser:
    """微信聊天记录时间戳解析器"""

    # 微信时间格式正则表达式
    # 注意：使用[:：]同时匹配英文冒号和中文冒号（OCR可能识别为中文冒号）
    PATTERNS = [
        # 完整格式: 2024年4月16日 中午12:57 或 2024年4月16日 中午12：57
        r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(上午|中午|下午|晚上|凌晨)?(\d{1,2})[:：](\d{2})',
        # 相对日期: 昨天 下午15:30 或 昨天 下午15：30
        r'(昨天|今天|前天)\s*(上午|中午|下午|晚上|凌晨)?(\d{1,2})[:：](\d{2})',
        # 月日格式: 4月16日 下午13:02 或 4月16日 下午13：02
        r'(\d{1,2})月(\d{1,2})日\s*(上午|中午|下午|晚上|凌晨)?(\d{1,2})[:：](\d{2})',
    ]

    # 时间关键词，用于过滤非时间文本
    TIME_KEYWORDS = ['年', '月', '日', '上午', '下午', '中午', '晚上', '凌晨', '昨天', '今天', '前天', ':', '：']

    def __init__(self, reference_date=None):
        """
        初始化时间解析器
        reference_date: 参考日期，用于解析相对时间（默认为当前日期）
        """
        self.reference_date = reference_date or datetime.now()

    def contains_time_keyword(self, text: str) -> bool:
        """检查文本是否包含时间关键词"""
        return any(keyword in text for keyword in self.TIME_KEYWORDS)

    def parse_time_period(self, period: str, hour: int) -> int:
        """
        将中文时段转换为24小时制
        period: 上午/中午/下午/晚上/凌晨
        hour: 原始小时数
        返回: 24小时制的小时数
        """
        if not period:
            return hour

        if period == '中午':
            return 12
        elif period in ('下午', '晚上'):
            return hour if hour >= 12 else hour + 12
        # 上午、凌晨：保持原值
        return hour

    def parse_relative_date(self, relative: str) -> datetime:
        """
        解析相对日期
        relative: 昨天/今天/前天
        """
        if relative == '今天':
            return self.reference_date
        elif relative == '昨天':
            return self.reference_date - timedelta(days=1)
        elif relative == '前天':
            return self.reference_date - timedelta(days=2)
        return self.reference_date

    def _try_add_timestamp(self, year: int, month: int, day: int,
                           period: str, hour: int, minute: int,
                           original_text: str,
                           timestamps: list, seen_times: set) -> bool:
        """尝试构造datetime并去重追加，成功返回True"""
        try:
            hour = self.parse_time_period(period, hour)
            dt = datetime(year, month, day, hour, minute)
            time_key = (dt.year, dt.month, dt.day, dt.hour, dt.minute)
            if time_key not in seen_times:
                timestamps.append((dt, original_text))
                seen_times.add(time_key)
            return True
        except (ValueError, TypeError):
            return False

    def extract_timestamps(self, text: str) -> List[Tuple[datetime, str]]:
        """
        从文本中提取所有时间戳
        返回: [(datetime对象, 原始文本), ...]
        """
        timestamps = []
        seen_times = set()

        # 提取完整日期格式的年份，用于推断月日格式的年份
        full_date_years = [
            int(m.group(1)) for m in re.finditer(self.PATTERNS[0], text)
        ]
        inferred_year = (
            max(set(full_date_years), key=full_date_years.count)
            if full_date_years else self.reference_date.year
        )

        for pattern in self.PATTERNS:
            for match in re.finditer(pattern, text):
                original_text = match.group(0)
                groups = match.groups()

                if len(groups) == 6:  # 完整日期: 年月日 时段 时:分
                    year, month, day, period, hour, minute = groups
                    self._try_add_timestamp(
                        int(year), int(month), int(day), period,
                        int(hour), int(minute),
                        original_text, timestamps, seen_times)

                elif len(groups) == 4 and groups[0] in ('昨天', '今天', '前天'):  # 相对日期
                    relative, period, hour, minute = groups
                    base = self.parse_relative_date(relative)
                    self._try_add_timestamp(
                        base.year, base.month, base.day, period,
                        int(hour), int(minute),
                        original_text, timestamps, seen_times)

                elif len(groups) == 5:  # 月日格式: 月日 时段 时:分
                    month, day, period, hour, minute = groups
                    self._try_add_timestamp(
                        inferred_year, int(month), int(day), period,
                        int(hour), int(minute),
                        original_text, timestamps, seen_times)

        timestamps.sort(key=lambda x: x[0])
        return timestamps

    def get_time_range(self, text: str) -> Optional[Tuple[datetime, datetime]]:
        """获取文本中的时间范围（最早和最晚）"""
        timestamps = self.extract_timestamps(text)
        if not timestamps:
            return None
        return (timestamps[0][0], timestamps[-1][0])

    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
        """格式化日期时间"""
        return dt.strftime(format_str)

    @staticmethod
    def format_time_range(start: datetime, end: datetime) -> str:
        """格式化时间范围"""
        if start.date() == end.date():
            # 同一天
            return f"{start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}"
        else:
            # 跨天
            return f"{start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%Y-%m-%d %H:%M')}"
