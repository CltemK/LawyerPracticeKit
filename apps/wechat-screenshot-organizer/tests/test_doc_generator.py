"""
测试OCR和文档生成的集成功能
使用模拟数据测试
"""
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core.time_parser import TimeParser
from core.doc_generator import DocGenerator
from datetime import datetime

def test_doc_generation():
    print("=" * 50)
    print("测试Word文档生成")
    print("=" * 50)

    # 模拟OCR结果
    mock_ocr_results = [
        {
            'image_path': '../test_image_1.png',
            'text': '''
            正八建设王忠平
            2024年4月16日 中午12:57
            把夷陵华美达这边款跟我安排一笔呢
            2024年4月16日 下午13:02
            还个信用卡还得靠手机银行里面贷款5万呢
            ''',
            'success': True
        },
        {
            'image_path': '../test_image_2.png',
            'text': '''
            夷陵华美达施工群(7)
            2024年1月22日 下午17:04
            正八建设王忠平
            好的
            2024年1月22日 下午17:34
            2024年1月23日 中午12:58
            韩旭光
            找到了
            ''',
            'success': True
        },
        {
            'image_path': '../test_image_3.png',
            'text': '这是一张没有时间戳的图片',
            'success': True
        }
    ]

    # 创建时间解析器
    time_parser = TimeParser()

    print("\n解析OCR结果中的时间:")
    for i, result in enumerate(mock_ocr_results, 1):
        print(f"\n图片 {i}: {os.path.basename(result['image_path'])}")
        if result['success']:
            time_range = time_parser.get_time_range(result['text'])
            if time_range:
                print(f"  时间范围: {time_parser.format_time_range(time_range[0], time_range[1])}")
            else:
                print("  未识别到时间")

    # 测试文档生成器配置
    print("\n\n测试文档生成器配置:")
    for images_per_page in [2, 4, 6]:
        doc_gen = DocGenerator(images_per_page=images_per_page)
        print(f"  每页{images_per_page}张图片 -> 网格: {doc_gen.grid_rows}行 x {doc_gen.grid_cols}列")

    print("\n[OK] 文档生成测试完成")
    print("\n注意: 实际生成Word文档需要真实的图片文件")

if __name__ == "__main__":
    test_doc_generation()
