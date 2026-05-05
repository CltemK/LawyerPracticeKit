"""
OCR诊断测试脚本
检查百度OCR服务是否正常工作
"""
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core.ocr_providers import BaiduOCRService
from core.time_parser import TimeParser
from gui.settings_dialog import SettingsDialog


def test_ocr_diagnosis():
    print("=" * 70)
    print("OCR诊断测试")
    print("=" * 70)

    # 1. 检查配置
    print("\n1. 检查API配置:")
    api_key, secret_key = SettingsDialog.get_saved_keys()

    if not api_key or not secret_key:
        print("  [ERROR] API密钥未配置!")
        print("  请先运行: python main.py")
        print("  在设置对话框中配置百度OCR API密钥")
        return

    print(f"  [OK] API密钥已配置: {api_key[:10]}...")
    print(f"  [OK] Secret密钥已配置: {secret_key[:10]}...")

    # 2. 测试OCR连接
    print("\n2. 测试OCR服务连接:")
    try:
        ocr_service = BaiduOCRService(api_key, secret_key)
        ok, msg = ocr_service.check_availability()
        if ok:
            print(f"  [OK] {msg}")
        else:
            print(f"  [ERROR] {msg}")
            return
    except Exception as e:
        print(f"  [ERROR] 连接失败: {e}")
        return

    # 3. 检查测试图片
    print("\n3. 检查测试图片:")
    test_dir = os.path.join(parent_dir, 'test_images')
    if not os.path.exists(test_dir):
        print(f"  [ERROR] 测试图片目录不存在: {test_dir}")
        return

    image_files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print(f"  [ERROR] 测试图片目录中没有图片文件")
        return

    print(f"  [OK] 找到 {len(image_files)} 张测试图片")

    # 4. OCR识别测试
    print("\n4. OCR识别测试:")
    print("-" * 70)

    time_parser = TimeParser()

    for image_file in sorted(image_files):
        image_path = os.path.join(test_dir, image_file)
        print(f"\n  图片: {image_file}")
        print(f"  大小: {os.path.getsize(image_path) / 1024:.1f} KB")

        result = ocr_service.recognize_text(image_path)

        if not result['success']:
            print(f"  [ERROR] OCR识别失败: {result['error']}")
            continue

        text = result['text']
        print(f"\n  识别到的原始文本 ({len(text)} 字符):")
        print("  " + "-" * 66)

        lines = text.split('\n')
        for i, line in enumerate(lines[:20]):
            display_line = line[:60] + "..." if len(line) > 60 else line
            print(f"    {i+1:2d}. {display_line}")

        if len(lines) > 20:
            print(f"    ... 还有 {len(lines) - 20} 行 ...")

        print("  " + "-" * 66)

        timestamps = time_parser.extract_timestamps(text)
        if timestamps:
            print(f"    [OK] 找到 {len(timestamps)} 个时间戳:")
            for dt, original in timestamps:
                print(f"      - {original:30s} -> {time_parser.format_datetime(dt)}")
        else:
            print(f"    [WARNING] 未找到时间戳")

    print("\n诊断完成!")


if __name__ == "__main__":
    test_ocr_diagnosis()
