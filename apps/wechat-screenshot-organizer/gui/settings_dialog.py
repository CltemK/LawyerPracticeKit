"""
设置对话框
配置百度OCR API密钥
"""
import os
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):
    """设置对话框"""

    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setMinimumWidth(480)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 百度OCR配置组
        ocr_group = QGroupBox('百度OCR API 配置')
        form = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText('请输入百度OCR API Key')
        form.addRow('API Key:', self.api_key_input)

        self.secret_key_input = QLineEdit()
        self.secret_key_input.setPlaceholderText('请输入百度OCR Secret Key')
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        form.addRow('Secret Key:', self.secret_key_input)

        ocr_group.setLayout(form)
        layout.addWidget(ocr_group)

        # 帮助信息
        help_label = QLabel(
            '获取密钥：访问 https://ai.baidu.com/tech/ocr 注册并创建应用\n'
            '免费额度：50000次/天，足够日常使用'
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet('color: #64748b; font-size: 12px;')
        layout.addWidget(help_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        test_btn = QPushButton('测试连接')
        test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(test_btn)

        save_btn = QPushButton('保存')
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.api_key_input.setText(config.get('api_key', ''))
                self.secret_key_input.setText(config.get('secret_key', ''))
            except Exception:
                pass

    def _save_config(self):
        """保存配置"""
        api_key = self.api_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()

        if not api_key or not secret_key:
            QMessageBox.warning(self, '提示', '请填写完整的API Key和Secret Key')
            return

        config = {'api_key': api_key, 'secret_key': secret_key}
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, '成功', '配置已保存')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {e}')

    def _test_connection(self):
        """测试OCR连接"""
        api_key = self.api_key_input.text().strip()
        secret_key = self.secret_key_input.text().strip()

        if not api_key or not secret_key:
            QMessageBox.warning(self, '提示', '请先填写API Key和Secret Key')
            return

        try:
            from core.ocr_providers import BaiduOCRService
            service = BaiduOCRService(api_key, secret_key)
            ok, msg = service.check_availability()
            if ok:
                QMessageBox.information(self, '成功', msg)
            else:
                QMessageBox.warning(self, '失败', msg)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'测试失败: {e}')

    @staticmethod
    def get_saved_keys():
        """静态方法：读取已保存的密钥"""
        config_file = SettingsDialog.CONFIG_FILE
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('api_key', ''), config.get('secret_key', '')
            except Exception:
                pass
        return '', ''
