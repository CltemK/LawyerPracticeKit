"""
测试时间解析模块
"""
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core.time_parser import TimeParser
from datetime import datetime

def test_time_parser():
    print("=" * 50)
    print("测试时间解析模块")
    print("=" * 50)

    parser = TimeParser()

    # 测试用例
    test_cases = [
        "2024年4月16日 中午12:57",
        "2024年4月16日 下午13:02",
        "2024年1月22日 下午17:04",
        "昨天 15:30",
        "今天 上午10:30",
        "4月16日 下午13:02",
    ]

    print("\n测试单个时间戳提取:")
    for text in test_cases:
        timestamps = parser.extract_timestamps(text)
        if timestamps:
            dt, original = timestamps[0]
            formatted = parser.format_datetime(dt)
            print(f"输入: {text:30s} -> 输出: {formatted}")
        else:
            print(f"输入: {text:30s} -> 未识别")

    # 测试多时间戳文本
    print("\n测试多时间戳提取:")
    multi_text = """
    2024年4月16日 中午12:57
    正八建设王忠平
    2024年4月16日 下午13:02
    韩旭光
    2024年4月16日 下午13:50
    """

    timestamps = parser.extract_timestamps(multi_text)
    print(f"文本中找到 {len(timestamps)} 个时间戳:")
    for dt, original in timestamps:
        print(f"  - {original} -> {parser.format_datetime(dt)}")

    if timestamps:
        time_range = (timestamps[0][0], timestamps[-1][0])
        print(f"\n时间范围: {parser.format_time_range(time_range[0], time_range[1])}")

    print("\n[OK] 时间解析模块测试完成")

if __name__ == "__main__":
    test_time_parser()
