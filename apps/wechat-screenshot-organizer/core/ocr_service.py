"""
OCR服务模块
复用百度OCR API进行图片文字识别
"""
import os
import base64
import requests
from PIL import Image


class OCRService:
    """百度OCR服务封装类"""

    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = None

    def get_access_token(self):
        """获取百度OCR的access_token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        try:
            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                return self.access_token
            else:
                raise Exception(f"获取access_token失败: {response.text}")
        except Exception as e:
            raise Exception(f"网络请求失败: {str(e)}")

    def compress_image(self, image_path, max_size=4 * 1024 * 1024):
        """压缩图片到指定大小以下"""
        with open(image_path, "rb") as f:
            image_data = f.read()

        if len(image_data) <= max_size:
            return image_data

        img = Image.open(image_path)
        ratio = (max_size / len(image_data)) ** 0.5 * 0.9
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        temp_path = os.path.splitext(image_path)[0] + '_temp.jpg'
        try:
            img.save(temp_path, 'JPEG', quality=85)
            with open(temp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def recognize_text(self, image_path):
        """
        识别图片中的文字
        返回: {
            'success': bool,
            'text': str,  # 所有文字拼接
            'words_result': list,  # 详细结果
            'error': str  # 错误信息
        }
        """
        if not self.access_token:
            self.get_access_token()

        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={self.access_token}"

        try:
            # 读取并压缩图片
            image_data = self.compress_image(image_path)
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'image': encoded_image,
                'detect_direction': 'true',
                'paragraph': 'false',
            }

            response = requests.post(url, headers=headers, data=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'words_result' in result:
                    words_result = result['words_result']
                    text = '\n'.join([item['words'] for item in words_result])
                    return {
                        'success': True,
                        'text': text,
                        'words_result': words_result,
                        'error': None
                    }
                elif 'error_code' in result:
                    error_msg = f"{result['error_code']} - {result.get('error_msg', 'Unknown')}"
                    return {
                        'success': False,
                        'text': '',
                        'words_result': [],
                        'error': error_msg
                    }
            else:
                return {
                    'success': False,
                    'text': '',
                    'words_result': [],
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'words_result': [],
                'error': str(e)
            }

    def batch_recognize(self, image_paths, progress_callback=None):
        """
        批量识别图片
        progress_callback: 进度回调函数 callback(current, total, image_path)
        """
        results = []
        total = len(image_paths)

        for i, image_path in enumerate(image_paths):
            if progress_callback:
                progress_callback(i + 1, total, image_path)

            result = self.recognize_text(image_path)
            result['image_path'] = image_path
            results.append(result)

        return results
