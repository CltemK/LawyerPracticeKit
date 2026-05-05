"""
OCR提供商模块
仅保留百度OCR在线API
"""
from ..ocr_service import OCRService


class BaiduOCRService:
    """百度OCR在线API服务"""

    def __init__(self, api_key='', secret_key=''):
        self.api_key = api_key
        self.secret_key = secret_key
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = OCRService(self.api_key, self.secret_key)
        return self._service

    def update_keys(self, api_key, secret_key):
        """更新密钥（重置内部服务实例）"""
        self.api_key = api_key
        self.secret_key = secret_key
        self._service = None

    def recognize_text(self, image_path: str) -> dict:
        """识别图片中的文字"""
        return self._get_service().recognize_text(image_path)

    def batch_recognize(self, image_paths, progress_callback=None):
        """批量识别图片"""
        return self._get_service().batch_recognize(image_paths, progress_callback)

    def get_provider_name(self) -> str:
        return "百度OCR（在线API）"

    def check_availability(self) -> tuple:
        """检查服务是否可用"""
        if not self.api_key or not self.secret_key:
            return False, "未配置API密钥"
        try:
            self._get_service().get_access_token()
            return True, "百度OCR已就绪"
        except Exception as e:
            return False, f"连接失败: {e}"


__all__ = ['BaiduOCRService']
