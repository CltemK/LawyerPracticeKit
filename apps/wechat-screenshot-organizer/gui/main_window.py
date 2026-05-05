"""
主窗口
微信聊天记录截图整理工具的GUI界面
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QComboBox, QCheckBox, QProgressBar, QMessageBox, QSplitter,
    QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon

from .settings_dialog import SettingsDialog
from core.ocr_providers import BaiduOCRService
from core.time_parser import TimeParser
from core.doc_generator import DocGenerator


class OCRWorker(QThread):
    """后台OCR识别线程"""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(list)  # results
    error = pyqtSignal(str)

    def __init__(self, ocr_service, image_paths):
        super().__init__()
        self.ocr_service = ocr_service
        self.image_paths = image_paths

    def run(self):
        try:
            results = self.ocr_service.batch_recognize(
                self.image_paths,
                progress_callback=lambda cur, total, path: self.progress.emit(cur, total, os.path.basename(path))
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    STYLE = """
    QMainWindow { background: #f5f7fa; }
    QLabel#title { font-size: 20px; font-weight: bold; color: #1e293b; }
    QLabel#subtitle { font-size: 12px; color: #64748b; }
    QPushButton {
        padding: 8px 16px; border-radius: 6px; font-size: 13px;
        border: 1px solid #e2e8f0; background: white; color: #1e293b;
    }
    QPushButton:hover { background: #f1f5f9; }
    QPushButton#primary {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #667eea, stop:1 #764ba2);
        color: white; border: none; font-weight: bold; padding: 10px 24px;
    }
    QPushButton#primary:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5a6fd6, stop:1 #6a4192); }
    QPushButton#danger { color: #ef4444; border-color: #fecaca; }
    QPushButton#danger:hover { background: #fef2f2; }
    QListWidget {
        background: white; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 4px; font-size: 13px;
    }
    QListWidget::item { padding: 6px 8px; border-radius: 4px; }
    QListWidget::item:selected { background: #ede9fe; color: #5b21b6; }
    QListWidget::item:hover { background: #f8fafc; }
    QGroupBox {
        font-weight: bold; color: #1e293b; border: 1px solid #e2e8f0;
        border-radius: 8px; margin-top: 8px; padding-top: 16px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
    QComboBox, QCheckBox { font-size: 13px; }
    QProgressBar {
        border: 1px solid #e2e8f0; border-radius: 4px; text-align: center;
        background: #f1f5f9; height: 20px;
    }
    QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #667eea, stop:1 #764ba2); border-radius: 3px; }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('微信聊天记录截图整理工具')
        self.setMinimumSize(960, 640)
        self.image_paths = []
        self.ocr_results = []
        self.ocr_worker = None
        self.setStyleSheet(self.STYLE)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 顶部标题栏
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title = QLabel('微信聊天记录截图整理工具')
        title.setObjectName('title')
        subtitle = QLabel('上传截图 → OCR识别时间 → 按时间排序 → 生成Word文档')
        subtitle.setObjectName('subtitle')
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        settings_btn = QPushButton('设置')
        settings_btn.clicked.connect(self._open_settings)
        header.addWidget(settings_btn)
        layout.addLayout(header)

        # 工具栏
        toolbar = QHBoxLayout()
        upload_btn = QPushButton('上传图片')
        upload_btn.clicked.connect(self._upload_images)
        toolbar.addWidget(upload_btn)

        folder_btn = QPushButton('选择文件夹')
        folder_btn.clicked.connect(self._select_folder)
        toolbar.addWidget(folder_btn)

        clear_btn = QPushButton('清空')
        clear_btn.setObjectName('danger')
        clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()

        self.count_label = QLabel('已添加 0 张图片')
        self.count_label.setStyleSheet('color: #64748b;')
        toolbar.addWidget(self.count_label)
        layout.addLayout(toolbar)

        # 主内容区：左列表 + 右预览
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：图片列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_widget)
        splitter.addWidget(left)

        # 右侧：预览
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_label = QLabel('选择图片查看预览')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet('background: white; border: 1px solid #e2e8f0; border-radius: 8px; color: #94a3b8;')
        self.preview_label.setMinimumSize(320, 240)
        right_layout.addWidget(self.preview_label)
        splitter.addWidget(right)

        splitter.setSizes([360, 560])
        layout.addWidget(splitter, 1)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 底部操作栏
        bottom = QHBoxLayout()

        page_group = QGroupBox('文档设置')
        page_layout = QHBoxLayout(page_group)
        page_layout.addWidget(QLabel('每页图片:'))
        self.page_combo = QComboBox()
        self.page_combo.addItems(['1', '2', '4', '6', '9'])
        self.page_combo.setCurrentText('4')
        self.page_combo.currentTextChanged.connect(self._on_settings_changed)
        page_layout.addWidget(self.page_combo)

        self.timestamp_cb = QCheckBox('显示时间戳')
        self.timestamp_cb.setChecked(True)
        page_layout.addWidget(self.timestamp_cb)
        bottom.addWidget(page_group)

        bottom.addStretch()

        self.generate_btn = QPushButton('生成Word文档')
        self.generate_btn.setObjectName('primary')
        self.generate_btn.clicked.connect(self._generate_document)
        self.generate_btn.setEnabled(False)
        bottom.addWidget(self.generate_btn)

        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #64748b; font-size: 12px;')
        bottom.addWidget(self.status_label)

        layout.addLayout(bottom)

        # 预览设置
        self.preview_per_page = 4

    # ── 图片管理 ──

    def _upload_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, '选择图片', '',
            '图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)'
        )
        if files:
            self._add_images(files)

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            exts = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
            files = [
                os.path.join(folder, f) for f in sorted(os.listdir(folder))
                if os.path.splitext(f)[1].lower() in exts
            ]
            if files:
                self._add_images(files)
            else:
                QMessageBox.information(self, '提示', '文件夹中没有找到图片文件')

    def _add_images(self, paths):
        new = [p for p in paths if p not in self.image_paths]
        self.image_paths.extend(new)
        for p in new:
            self.list_widget.addItem(os.path.basename(p))
        self._update_count()
        self._run_ocr()

    def _clear_all(self):
        self.image_paths.clear()
        self.ocr_results.clear()
        self.list_widget.clear()
        self.preview_label.clear()
        self.preview_label.setText('选择图片查看预览')
        self._update_count()
        self.generate_btn.setEnabled(False)
        self.status_label.setText('')

    def _update_count(self):
        self.count_label.setText(f'已添加 {len(self.image_paths)} 张图片')

    def _on_selection_changed(self, row):
        if 0 <= row < len(self.image_paths):
            pixmap = QPixmap(self.image_paths[row])
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)

    def _on_settings_changed(self, text):
        try:
            self.preview_per_page = int(text)
        except ValueError:
            pass

    # ── OCR ──

    def _run_ocr(self):
        if not self.image_paths:
            return

        api_key, secret_key = SettingsDialog.get_saved_keys()
        if not api_key or not secret_key:
            self.status_label.setText('请先在设置中配置百度OCR密钥')
            return

        ocr_service = BaiduOCRService(api_key, secret_key)
        self.ocr_worker = OCRWorker(ocr_service, self.image_paths)
        self.ocr_worker.progress.connect(self._on_ocr_progress)
        self.ocr_worker.finished.connect(self._on_ocr_finished)
        self.ocr_worker.error.connect(self._on_ocr_error)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.image_paths))
        self.generate_btn.setEnabled(False)
        self.status_label.setText('正在识别...')
        self.ocr_worker.start()

    def _on_ocr_progress(self, current, total, filename):
        self.progress_bar.setValue(current)
        self.status_label.setText(f'识别中 ({current}/{total}): {filename}')

    def _on_ocr_finished(self, results):
        self.ocr_results = results
        self.progress_bar.setVisible(False)
        success = sum(1 for r in results if r.get('success'))
        self.status_label.setText(f'识别完成: {success}/{len(results)} 张成功')
        self.generate_btn.setEnabled(True)

    def _on_ocr_error(self, error):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f'识别失败: {error}')
        QMessageBox.critical(self, 'OCR错误', error)

    # ── 文档生成 ──

    def _generate_document(self):
        if not self.ocr_results:
            QMessageBox.warning(self, '提示', '没有可生成的结果，请先添加图片')
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, '保存Word文档', '微信聊天记录整理.docx',
            'Word文档 (*.docx);;所有文件 (*)'
        )
        if not output_path:
            return

        try:
            self.status_label.setText('正在生成文档...')
            self.generate_btn.setEnabled(False)

            doc_gen = DocGenerator(
                images_per_page=self.preview_per_page,
                show_timestamp=self.timestamp_cb.isChecked()
            )
            time_parser = TimeParser()
            doc_gen.generate_from_ocr_results(
                self.ocr_results, output_path, time_parser,
                title='微信聊天记录整理'
            )

            self.status_label.setText(f'文档已生成: {os.path.basename(output_path)}')
            QMessageBox.information(self, '成功', f'文档已生成:\n{output_path}')
        except Exception as e:
            self.status_label.setText(f'生成失败: {e}')
            QMessageBox.critical(self, '错误', f'生成文档失败:\n{e}')
        finally:
            self.generate_btn.setEnabled(True)

    # ── 设置 ──

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()
        # 设置可能已更新，如果有图片则重新识别
        if self.image_paths:
            self._run_ocr()
