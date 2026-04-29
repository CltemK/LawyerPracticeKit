"""
完整流程测试（不调用真实API）
测试从图片到Word文档的完整流程
"""
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core.time_parser import TimeParser
from core.doc_generator import DocGenerator
from datetime import datetime

def test_full_workflow():
    print("=" * 60)
    print("完整工作流程测试")
    print("=" * 60)

    # 模拟OCR识别结果
    test_images_dir = "test_images"
    mock_ocr_results = [
        {
            'image_path': os.path.join(test_images_dir, 'test_chat_1.png'),
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
            'image_path': os.path.join(test_images_dir, 'test_chat_2.png'),
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
            'image_path': os.path.join(test_images_dir, 'test_chat_3.png'),
            'text': '这是一张没有时间戳的测试图片',
            'success': True
        }
    ]

    # 检查图片是否存在
    print("\n1. 检查测试图片:")
    all_exist = True
    for result in mock_ocr_results:
        exists = os.path.exists(result['image_path'])
        status = "[OK]" if exists else "[FAIL]"
        print(f"  {status} {result['image_path']}")
        if not exists:
            all_exist = False

    if not all_exist:
        print("\n[ERROR] 部分测试图片不存在，请先运行 create_test_images.py")
        return

    # 创建时间解析器
    time_parser = TimeParser()

    print("\n2. 解析时间戳:")
    for i, result in enumerate(mock_ocr_results, 1):
        print(f"\n  图片 {i}: {os.path.basename(result['image_path'])}")
        if result['success']:
            timestamps = time_parser.extract_timestamps(result['text'])
            if timestamps:
                print(f"    找到 {len(timestamps)} 个时间戳:")
                for dt, original in timestamps[:3]:  # 只显示前3个
                    print(f"      - {original} -> {time_parser.format_datetime(dt)}")
                if len(timestamps) > 3:
                    print(f"      ... 还有 {len(timestamps) - 3} 个")

                time_range = time_parser.get_time_range(result['text'])
                if time_range:
                    print(f"    时间范围: {time_parser.format_time_range(time_range[0], time_range[1])}")
            else:
                print("    未识别到时间戳")

    # 生成Word文档
    print("\n3. 生成Word文档:")
    output_path = "test_output.docx"

    try:
        doc_generator = DocGenerator(images_per_page=4)
        doc_generator.generate_from_ocr_results(
            mock_ocr_results,
            output_path,
            time_parser,
            title="微信聊天记录测试文档"
        )
        print(f"  [OK] 文档已生成: {output_path}")

        # 检查文件大小
        file_size = os.path.getsize(output_path)
        print(f"  [OK] 文件大小: {file_size / 1024:.2f} KB")

    except Exception as e:
        print(f"  [FAIL] 生成文档失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("[OK] 完整工作流程测试通过！")
    print("=" * 60)
    print(f"\n请打开 {output_path} 查看生成的Word文档")

if __name__ == "__main__":
    test_full_workflow()
