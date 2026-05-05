"""
创建测试用的示例图片
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_images():
    """创建模拟微信聊天截图的测试图片"""

    # 创建测试图片目录
    test_dir = "test_images"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    # 图片1: 私聊截图
    img1 = Image.new('RGB', (1080, 1920), color='white')
    draw1 = ImageDraw.Draw(img1)

    # 尝试使用系统字体
    try:
        font_large = ImageFont.truetype("msyh.ttc", 40)  # 微软雅黑
        font_small = ImageFont.truetype("msyh.ttc", 30)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 绘制私聊界面
    draw1.text((540, 100), "正八建设王忠平", fill='black', font=font_large, anchor="mm")
    draw1.text((540, 300), "2024年4月16日 中午12:57", fill='gray', font=font_small, anchor="mm")
    draw1.rectangle([100, 400, 900, 600], fill='lightgreen')
    draw1.text((500, 500), "把夷陵华美达这边款跟我安排一笔呢", fill='black', font=font_small, anchor="mm")

    draw1.text((540, 700), "2024年4月16日 下午13:02", fill='gray', font=font_small, anchor="mm")
    draw1.rectangle([100, 800, 900, 1000], fill='lightgreen')
    draw1.text((500, 900), "还个信用卡还得靠手机银行里面贷款5万呢", fill='black', font=font_small, anchor="mm")

    img1.save(os.path.join(test_dir, "test_chat_1.png"))
    print(f"[OK] 创建测试图片: {os.path.join(test_dir, 'test_chat_1.png')}")

    # 图片2: 群聊截图
    img2 = Image.new('RGB', (1080, 1920), color='white')
    draw2 = ImageDraw.Draw(img2)

    draw2.text((540, 100), "夷陵华美达施工群(7)", fill='black', font=font_large, anchor="mm")
    draw2.text((540, 300), "2024年1月22日 下午17:04", fill='gray', font=font_small, anchor="mm")

    # 第一条消息
    draw2.text((150, 400), "正八建设王忠平", fill='gray', font=font_small, anchor="lm")
    draw2.rectangle([100, 450, 500, 550], fill='white', outline='gray')
    draw2.text((300, 500), "好的", fill='black', font=font_small, anchor="mm")

    draw2.text((540, 650), "2024年1月22日 下午17:34", fill='gray', font=font_small, anchor="mm")

    # 第二条消息
    draw2.text((540, 850), "2024年1月23日 中午12:58", fill='gray', font=font_small, anchor="mm")
    draw2.text((150, 950), "韩旭光", fill='gray', font=font_small, anchor="lm")
    draw2.rectangle([100, 1000, 500, 1100], fill='white', outline='gray')
    draw2.text((300, 1050), "找到了", fill='black', font=font_small, anchor="mm")

    img2.save(os.path.join(test_dir, "test_chat_2.png"))
    print(f"[OK] 创建测试图片: {os.path.join(test_dir, 'test_chat_2.png')}")

    # 图片3: 无时间戳的图片
    img3 = Image.new('RGB', (1080, 1920), color='lightblue')
    draw3 = ImageDraw.Draw(img3)
    draw3.text((540, 960), "这是一张没有时间戳的测试图片", fill='black', font=font_large, anchor="mm")

    img3.save(os.path.join(test_dir, "test_chat_3.png"))
    print(f"[OK] 创建测试图片: {os.path.join(test_dir, 'test_chat_3.png')}")

    print(f"\n[OK] 所有测试图片已创建在 {test_dir} 目录")
    return test_dir

if __name__ == "__main__":
    create_test_images()
