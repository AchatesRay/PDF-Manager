"""设置对话框"""

from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QDialogButtonBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from src.utils.config import Config


class SettingsDialog(QDialog):
    """设置对话框

    配置选项：
    - 存储路径
    - OCR工作线程数
    """

    def __init__(self, config: Optional["Config"] = None, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self._config = config

        self.setWindowTitle("设置")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 存储设置组
        storage_group = QGroupBox("存储设置")
        storage_layout = QFormLayout(storage_group)

        # 存储路径
        path_layout = QHBoxLayout()
        self._storage_path_edit = QLineEdit()
        self._storage_path_edit.setPlaceholderText("选择数据存储路径...")
        path_layout.addWidget(self._storage_path_edit)

        self._browse_button = QPushButton("浏览...")
        self._browse_button.setFixedWidth(80)
        self._browse_button.clicked.connect(self._on_browse_storage_path)
        path_layout.addWidget(self._browse_button)

        storage_layout.addRow("存储路径:", path_layout)

        layout.addWidget(storage_group)

        # OCR设置组
        ocr_group = QGroupBox("OCR设置")
        ocr_layout = QFormLayout(ocr_group)

        # OCR工作线程数
        self._ocr_workers_spin = QSpinBox()
        self._ocr_workers_spin.setMinimum(1)
        self._ocr_workers_spin.setMaximum(16)
        self._ocr_workers_spin.setValue(2)
        ocr_layout.addRow("OCR工作线程数:", self._ocr_workers_spin)

        layout.addWidget(ocr_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _load_settings(self) -> None:
        """加载当前设置"""
        if self._config is None:
            return

        # 存储路径
        storage_path = self._config.get("storage_path", "./data")
        self._storage_path_edit.setText(str(storage_path))

        # OCR工作线程数
        ocr_workers = self._config.get("ocr_workers", 2)
        self._ocr_workers_spin.setValue(int(ocr_workers))

    def _on_browse_storage_path(self) -> None:
        """浏览存储路径"""
        current_path = self._storage_path_edit.text()
        if not current_path:
            current_path = "./data"

        folder = QFileDialog.getExistingDirectory(
            self,
            "选择存储路径",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self._storage_path_edit.setText(folder)

    def _on_accept(self) -> None:
        """确定按钮点击"""
        # 验证输入
        storage_path = self._storage_path_edit.text().strip()
        if not storage_path:
            QMessageBox.warning(self, "错误", "请设置存储路径")
            return

        # 保存设置
        if self._config is not None:
            self._config.set("storage_path", storage_path)
            self._config.set("ocr_workers", self._ocr_workers_spin.value())
            self._config.save()

        self.accept()

    def get_storage_path(self) -> str:
        """获取存储路径"""
        return self._storage_path_edit.text().strip()

    def get_ocr_workers(self) -> int:
        """获取OCR工作线程数"""
        return self._ocr_workers_spin.value()