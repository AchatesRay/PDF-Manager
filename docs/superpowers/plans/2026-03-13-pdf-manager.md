# PDF Manager Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个本地PDF管理工具，支持扫描版PDF的OCR识别、全文搜索和文件夹管理。

**Architecture:** 三层架构（UI层 → 业务逻辑层 → 服务层 → 数据层），使用PyQt6作为GUI框架，PaddleOCR进行中文OCR识别，Whoosh+jieba实现全文搜索。

**Tech Stack:** Python 3.11, PyQt6, PaddleOCR, Whoosh, jieba, PyMuPDF, SQLite

---

## File Structure

```
pdf-manager/
├── src/
│   ├── __init__.py
│   ├── main.py                      # 应用入口
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py           # 主窗口
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── folder_tree.py       # 文件夹树组件
│   │   │   ├── pdf_list.py          # PDF列表组件
│   │   │   └── pdf_viewer.py        # PDF预览组件
│   │   └── dialogs/
│   │       ├── __init__.py
│   │       ├── settings_dialog.py   # 设置对话框
│   │       └── import_dialog.py     # 导入进度对话框
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pdf_manager.py           # PDF管理服务
│   │   ├── folder_manager.py        # 文件夹管理服务
│   │   └── search_service.py        # 搜索服务
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py           # OCR处理服务
│   │   ├── index_service.py         # Whoosh索引服务
│   │   └── pdf_service.py           # PDF处理服务
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py              # SQLite数据库操作
│   │   └── schemas.py               # 数据结构定义
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # 配置管理
│       └── logger.py                # 日志工具
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_pdf_service.py
│   ├── test_ocr_service.py
│   ├── test_index_service.py
│   ├── test_folder_manager.py
│   ├── test_pdf_manager.py
│   └── test_search_service.py
├── requirements.txt
└── README.md
```

---

## Chunk 1: Project Setup & Data Models

### Task 1: 项目初始化

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `README.md`

- [ ] **Step 1: 创建 requirements.txt**

```txt
PyQt6>=6.4.0
paddlepaddle>=2.5.0
paddleocr>=2.7.0
PyMuPDF>=1.23.0
whoosh>=2.7.4
jieba>=0.42.1
Pillow>=10.0.0
pytest>=7.0.0
pytest-qt>=4.2.0
```

- [ ] **Step 2: 创建 src/__init__.py**

```python
"""PDF Manager - 本地PDF管理工具"""

__version__ = "0.1.0"
```

- [ ] **Step 3: 创建 README.md**

```markdown
# PDF Manager

本地PDF管理工具，支持扫描版PDF的OCR识别和全文搜索。

## 功能

- 文件夹分类管理PDF文件
- 自动识别扫描版PDF内容（OCR）
- 全文搜索，支持中文
- 内置PDF预览

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python src/main.py
```
```

- [ ] **Step 4: 提交**

```bash
git add requirements.txt src/__init__.py README.md
git commit -m "feat: 项目初始化"
```

---

### Task 2: 配置管理模块

**Files:**
- Create: `src/utils/__init__.py`
- Create: `src/utils/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py` (将在utils测试中添加)

- [ ] **Step 1: 创建 utils/__init__.py**

```python
"""工具模块"""
from .config import Config
from .logger import setup_logger

__all__ = ["Config", "setup_logger"]
```

- [ ] **Step 2: 创建配置类**

```python
# src/utils/config.py
"""配置管理模块"""

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "storage_path": "./data",
    "ocr_language": "ch",
    "ocr_workers": 2,
    "thumbnail_size": 200,
}


class Config:
    """配置管理类"""

    def __init__(self, config_path: str | Path | None = None):
        self._config_path = Path(config_path) if config_path else None
        self._config: dict[str, Any] = DEFAULT_CONFIG.copy()
        if self._config_path and self._config_path.exists():
            self.load()

    def load(self) -> None:
        """从文件加载配置"""
        if self._config_path and self._config_path.exists():
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self._config.update(loaded)

    def save(self) -> None:
        """保存配置到文件"""
        if self._config_path:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self._config[key] = value

    @property
    def storage_path(self) -> Path:
        """数据存储路径"""
        return Path(self._config["storage_path"])

    @storage_path.setter
    def storage_path(self, path: str | Path) -> None:
        self._config["storage_path"] = str(path)

    @property
    def database_path(self) -> Path:
        """数据库文件路径"""
        return self.storage_path / "pdf_manager.db"

    @property
    def pdfs_path(self) -> Path:
        """PDF文件存储路径"""
        return self.storage_path / "pdfs"

    @property
    def thumbnails_path(self) -> Path:
        """缩略图存储路径"""
        return self.storage_path / "thumbnails"

    @property
    def index_path(self) -> Path:
        """索引存储路径"""
        return self.storage_path / "index"

    def ensure_directories(self) -> None:
        """确保所有必要目录存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.pdfs_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 3: 创建测试文件**

```python
# tests/__init__.py
"""测试模块"""
```

```python
# tests/test_config.py
"""配置模块测试"""

import pytest
import tempfile
import json
from pathlib import Path

from src.utils.config import Config, DEFAULT_CONFIG


class TestConfig:
    """配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        assert config.get("storage_path") == "./data"
        assert config.get("ocr_workers") == 2

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        config = Config()
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

    def test_set_and_get(self):
        """测试设置和获取"""
        config = Config()
        config.set("custom_key", "custom_value")
        assert config.get("custom_key") == "custom_value"

    def test_load_config(self):
        """测试从文件加载配置"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"ocr_workers": 4, "custom": "value"}, f)
            config_path = f.name

        try:
            config = Config(config_path)
            assert config.get("ocr_workers") == 4
            assert config.get("custom") == "value"
            assert config.get("storage_path") == "./data"  # 默认值保留
        finally:
            Path(config_path).unlink()

    def test_save_config(self):
        """测试保存配置到文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = Config(config_path)
            config.set("ocr_workers", 3)
            config.save()

            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["ocr_workers"] == 3

    def test_path_properties(self):
        """测试路径属性"""
        config = Config()
        config.storage_path = "/custom/path"
        assert config.storage_path == Path("/custom/path")
        assert config.database_path == Path("/custom/path/pdf_manager.db")
        assert config.pdfs_path == Path("/custom/path/pdfs")

    def test_ensure_directories(self):
        """测试创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            config.storage_path = Path(tmpdir) / "data"
            config.ensure_directories()

            assert config.storage_path.exists()
            assert config.pdfs_path.exists()
            assert config.thumbnails_path.exists()
            assert config.index_path.exists()
```

- [ ] **Step 4: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_config.py -v
```

Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/utils/ tests/__init__.py tests/test_config.py
git commit -m "feat: 添加配置管理模块"
```

---

### Task 3: 日志模块

**Files:**
- Create: `src/utils/logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1: 创建日志模块**

```python
# src/utils/logger.py
"""日志模块"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "pdf_manager",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "pdf_manager") -> logging.Logger:
    """获取已配置的日志记录器"""
    return logging.getLogger(name)
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_logger.py
"""日志模块测试"""

import pytest
import logging
import tempfile
from pathlib import Path

from src.utils.logger import setup_logger, get_logger


class TestLogger:
    """日志模块测试"""

    def test_setup_logger_returns_logger(self):
        """测试返回日志记录器"""
        logger = setup_logger("test_logger1")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger1"

    def test_logger_has_console_handler(self):
        """测试日志记录器有控制台处理器"""
        logger = setup_logger("test_logger2")
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_logger_with_file(self):
        """测试日志记录到文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logger("test_logger3", log_file=log_file)

            logger.info("Test message")

            assert log_file.exists()
            content = log_file.read_text(encoding="utf-8")
            assert "Test message" in content

    def test_get_logger_returns_same_instance(self):
        """测试获取同一个日志记录器实例"""
        logger1 = setup_logger("shared_logger")
        logger2 = get_logger("shared_logger")
        assert logger1 is logger2

    def test_logger_level(self):
        """测试日志级别设置"""
        logger = setup_logger("test_logger4", level=logging.DEBUG)
        assert logger.level == logging.DEBUG
```

- [ ] **Step 3: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_logger.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add src/utils/logger.py tests/test_logger.py
git commit -m "feat: 添加日志模块"
```

---

### Task 4: 数据模型定义

**Files:**
- Create: `src/models/__init__.py`
- Create: `src/models/schemas.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: 创建 models/__init__.py**

```python
"""数据模型模块"""
from .schemas import Folder, PDF, PDFPage
from .database import Database

__all__ = ["Folder", "PDF", "PDFPage", "Database"]
```

- [ ] **Step 2: 创建数据结构定义**

```python
# src/models/schemas.py
"""数据结构定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class PDFType(Enum):
    """PDF类型枚举"""
    TEXT = "text"
    SCANNED = "scanned"
    MIXED = "mixed"


class PDFStatus(Enum):
    """PDF处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class OCRStatus(Enum):
    """OCR处理状态枚举"""
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"


@dataclass
class Folder:
    """文件夹数据模型"""
    name: str
    id: Optional[int] = None
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class PDF:
    """PDF文件数据模型"""
    filename: str
    file_path: str
    folder_id: Optional[int] = None
    id: Optional[int] = None
    file_size: int = 0
    page_count: int = 0
    pdf_type: PDFType = PDFType.SCANNED
    status: PDFStatus = PDFStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class PDFPage:
    """PDF页面数据模型"""
    pdf_id: int
    page_number: int
    id: Optional[int] = None
    ocr_text: str = ""
    ocr_status: OCRStatus = OCRStatus.PENDING
    thumbnail_path: Optional[str] = None
```

- [ ] **Step 3: 创建测试**

```python
# tests/test_schemas.py
"""数据结构测试"""

import pytest
from datetime import datetime

from src.models.schemas import (
    Folder, PDF, PDFPage,
    PDFType, PDFStatus, OCRStatus
)


class TestFolder:
    """文件夹模型测试"""

    def test_create_folder(self):
        """测试创建文件夹"""
        folder = Folder(name="测试文件夹")
        assert folder.name == "测试文件夹"
        assert folder.id is None
        assert folder.parent_id is None
        assert folder.created_at is not None

    def test_create_nested_folder(self):
        """测试创建嵌套文件夹"""
        folder = Folder(name="子文件夹", parent_id=1)
        assert folder.parent_id == 1


class TestPDF:
    """PDF模型测试"""

    def test_create_pdf(self):
        """测试创建PDF记录"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        assert pdf.filename == "test.pdf"
        assert pdf.status == PDFStatus.PENDING
        assert pdf.pdf_type == PDFType.SCANNED

    def test_pdf_with_folder(self):
        """测试带文件夹的PDF"""
        pdf = PDF(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            folder_id=1,
            page_count=10
        )
        assert pdf.folder_id == 1
        assert pdf.page_count == 10


class TestPDFPage:
    """PDF页面模型测试"""

    def test_create_page(self):
        """测试创建页面"""
        page = PDFPage(pdf_id=1, page_number=1)
        assert page.pdf_id == 1
        assert page.page_number == 1
        assert page.ocr_status == OCRStatus.PENDING
        assert page.ocr_text == ""

    def test_page_with_text(self):
        """测试带文本的页面"""
        page = PDFPage(
            pdf_id=1,
            page_number=1,
            ocr_text="测试文本",
            ocr_status=OCRStatus.DONE
        )
        assert page.ocr_text == "测试文本"
        assert page.ocr_status == OCRStatus.DONE
```

- [ ] **Step 4: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_schemas.py -v
```

Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/models/__init__.py src/models/schemas.py tests/test_schemas.py
git commit -m "feat: 添加数据模型定义"
```

---

### Task 5: 数据库操作模块

**Files:**
- Create: `src/models/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: 创建数据库模块**

```python
# src/models/database.py
"""数据库操作模块"""

import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from contextlib import contextmanager

from .schemas import Folder, PDF, PDFPage, PDFType, PDFStatus, OCRStatus


class Database:
    """SQLite数据库操作类"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_tables()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_tables(self):
        """确保数据表存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建文件夹表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (parent_id) REFERENCES folders(id)
                )
            """)

            # 创建PDF表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pdfs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    page_count INTEGER DEFAULT 0,
                    pdf_type TEXT DEFAULT 'scanned',
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (folder_id) REFERENCES folders(id)
                )
            """)

            # 创建页面表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pdf_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    ocr_text TEXT,
                    ocr_status TEXT DEFAULT 'pending',
                    thumbnail_path TEXT,
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pdfs_folder ON pdfs(folder_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pages_pdf ON pdf_pages(pdf_id)
            """)

    # ==================== 文件夹操作 ====================

    def create_folder(self, folder: Folder) -> int:
        """创建文件夹，返回ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO folders (name, parent_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (folder.name, folder.parent_id, folder.created_at, folder.updated_at)
            )
            return cursor.lastrowid

    def get_folder(self, folder_id: int) -> Optional[Folder]:
        """获取文件夹"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_folder(row)
            return None

    def get_folders_by_parent(self, parent_id: Optional[int] = None) -> List[Folder]:
        """获取指定父文件夹下的所有文件夹"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if parent_id is None:
                cursor.execute("SELECT * FROM folders WHERE parent_id IS NULL")
            else:
                cursor.execute("SELECT * FROM folders WHERE parent_id = ?", (parent_id,))
            return [self._row_to_folder(row) for row in cursor.fetchall()]

    def get_all_folders(self) -> List[Folder]:
        """获取所有文件夹"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM folders ORDER BY name")
            return [self._row_to_folder(row) for row in cursor.fetchall()]

    def update_folder(self, folder: Folder) -> bool:
        """更新文件夹"""
        if folder.id is None:
            return False
        folder.updated_at = datetime.now()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE folders SET name = ?, parent_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (folder.name, folder.parent_id, folder.updated_at, folder.id)
            )
            return cursor.rowcount > 0

    def delete_folder(self, folder_id: int) -> bool:
        """删除文件夹"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
            return cursor.rowcount > 0

    def _row_to_folder(self, row: sqlite3.Row) -> Folder:
        """将数据库行转换为Folder对象"""
        return Folder(
            id=row["id"],
            name=row["name"],
            parent_id=row["parent_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )

    # ==================== PDF操作 ====================

    def create_pdf(self, pdf: PDF) -> int:
        """创建PDF记录，返回ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pdfs (folder_id, filename, file_path, file_size, page_count, pdf_type, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pdf.folder_id, pdf.filename, pdf.file_path, pdf.file_size,
                    pdf.page_count, pdf.pdf_type.value, pdf.status.value,
                    pdf.created_at, pdf.updated_at
                )
            )
            return cursor.lastrowid

    def get_pdf(self, pdf_id: int) -> Optional[PDF]:
        """获取PDF"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pdfs WHERE id = ?", (pdf_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_pdf(row)
            return None

    def get_pdfs_by_folder(self, folder_id: Optional[int] = None) -> List[PDF]:
        """获取指定文件夹下的所有PDF"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if folder_id is None:
                cursor.execute("SELECT * FROM pdfs WHERE folder_id IS NULL ORDER BY filename")
            else:
                cursor.execute("SELECT * FROM pdfs WHERE folder_id = ? ORDER BY filename", (folder_id,))
            return [self._row_to_pdf(row) for row in cursor.fetchall()]

    def get_all_pdfs(self) -> List[PDF]:
        """获取所有PDF"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pdfs ORDER BY filename")
            return [self._row_to_pdf(row) for row in cursor.fetchall()]

    def update_pdf(self, pdf: PDF) -> bool:
        """更新PDF"""
        if pdf.id is None:
            return False
        pdf.updated_at = datetime.now()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE pdfs SET folder_id = ?, filename = ?, file_path = ?,
                file_size = ?, page_count = ?, pdf_type = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    pdf.folder_id, pdf.filename, pdf.file_path, pdf.file_size,
                    pdf.page_count, pdf.pdf_type.value, pdf.status.value,
                    pdf.updated_at, pdf.id
                )
            )
            return cursor.rowcount > 0

    def update_pdf_status(self, pdf_id: int, status: PDFStatus) -> bool:
        """更新PDF状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE pdfs SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, datetime.now(), pdf_id)
            )
            return cursor.rowcount > 0

    def delete_pdf(self, pdf_id: int) -> bool:
        """删除PDF（级联删除页面）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pdfs WHERE id = ?", (pdf_id,))
            return cursor.rowcount > 0

    def _row_to_pdf(self, row: sqlite3.Row) -> PDF:
        """将数据库行转换为PDF对象"""
        return PDF(
            id=row["id"],
            folder_id=row["folder_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            page_count=row["page_count"],
            pdf_type=PDFType(row["pdf_type"]),
            status=PDFStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )

    # ==================== 页面操作 ====================

    def create_page(self, page: PDFPage) -> int:
        """创建页面记录，返回ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pdf_pages (pdf_id, page_number, ocr_text, ocr_status, thumbnail_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (page.pdf_id, page.page_number, page.ocr_text, page.ocr_status.value, page.thumbnail_path)
            )
            return cursor.lastrowid

    def get_page(self, page_id: int) -> Optional[PDFPage]:
        """获取页面"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pdf_pages WHERE id = ?", (page_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_page(row)
            return None

    def get_pages_by_pdf(self, pdf_id: int) -> List[PDFPage]:
        """获取PDF的所有页面"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pdf_pages WHERE pdf_id = ? ORDER BY page_number", (pdf_id,))
            return [self._row_to_page(row) for row in cursor.fetchall()]

    def update_page(self, page: PDFPage) -> bool:
        """更新页面"""
        if page.id is None:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE pdf_pages SET ocr_text = ?, ocr_status = ?, thumbnail_path = ?
                WHERE id = ?
                """,
                (page.ocr_text, page.ocr_status.value, page.thumbnail_path, page.id)
            )
            return cursor.rowcount > 0

    def update_page_ocr(self, page_id: int, ocr_text: str, ocr_status: OCRStatus) -> bool:
        """更新页面OCR结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE pdf_pages SET ocr_text = ?, ocr_status = ? WHERE id = ?",
                (ocr_text, ocr_status.value, page_id)
            )
            return cursor.rowcount > 0

    def delete_pages_by_pdf(self, pdf_id: int) -> int:
        """删除PDF的所有页面"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pdf_pages WHERE pdf_id = ?", (pdf_id,))
            return cursor.rowcount

    def _row_to_page(self, row: sqlite3.Row) -> PDFPage:
        """将数据库行转换为PDFPage对象"""
        return PDFPage(
            id=row["id"],
            pdf_id=row["pdf_id"],
            page_number=row["page_number"],
            ocr_text=row["ocr_text"] or "",
            ocr_status=OCRStatus(row["ocr_status"]),
            thumbnail_path=row["thumbnail_path"],
        )

    # ==================== 统计操作 ====================

    def get_pdf_count(self, folder_id: Optional[int] = None) -> int:
        """获取PDF数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if folder_id is None:
                cursor.execute("SELECT COUNT(*) FROM pdfs")
            else:
                cursor.execute("SELECT COUNT(*) FROM pdfs WHERE folder_id = ?", (folder_id,))
            return cursor.fetchone()[0]

    def get_status_counts(self) -> dict:
        """获取各状态的PDF数量"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM pdfs GROUP BY status")
            return {row[0]: row[1] for row in cursor.fetchall()}
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_database.py
"""数据库模块测试"""

import pytest
import tempfile
from pathlib import Path

from src.models.database import Database
from src.models.schemas import Folder, PDF, PDFPage, PDFType, PDFStatus, OCRStatus


@pytest.fixture
def db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield Database(db_path)


class TestFolderOperations:
    """文件夹操作测试"""

    def test_create_folder(self, db):
        """测试创建文件夹"""
        folder = Folder(name="测试文件夹")
        folder_id = db.create_folder(folder)
        assert folder_id > 0

    def test_get_folder(self, db):
        """测试获取文件夹"""
        folder = Folder(name="测试文件夹")
        folder_id = db.create_folder(folder)

        retrieved = db.get_folder(folder_id)
        assert retrieved is not None
        assert retrieved.name == "测试文件夹"

    def test_get_folders_by_parent(self, db):
        """测试获取子文件夹"""
        parent = Folder(name="父文件夹")
        parent_id = db.create_folder(parent)

        child1 = Folder(name="子文件夹1", parent_id=parent_id)
        child2 = Folder(name="子文件夹2", parent_id=parent_id)
        db.create_folder(child1)
        db.create_folder(child2)

        children = db.get_folders_by_parent(parent_id)
        assert len(children) == 2

    def test_update_folder(self, db):
        """测试更新文件夹"""
        folder = Folder(name="原名称")
        folder_id = db.create_folder(folder)

        folder.id = folder_id
        folder.name = "新名称"
        db.update_folder(folder)

        updated = db.get_folder(folder_id)
        assert updated.name == "新名称"

    def test_delete_folder(self, db):
        """测试删除文件夹"""
        folder = Folder(name="测试文件夹")
        folder_id = db.create_folder(folder)

        assert db.delete_folder(folder_id)
        assert db.get_folder(folder_id) is None


class TestPDFOperations:
    """PDF操作测试"""

    def test_create_pdf(self, db):
        """测试创建PDF"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)
        assert pdf_id > 0

    def test_get_pdf(self, db):
        """测试获取PDF"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_folder(Folder(name="folder"))
        pdf.folder_id = pdf_id
        created_id = db.create_pdf(pdf)

        retrieved = db.get_pdf(created_id)
        assert retrieved is not None
        assert retrieved.filename == "test.pdf"

    def test_update_pdf_status(self, db):
        """测试更新PDF状态"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)

        db.update_pdf_status(pdf_id, PDFStatus.PROCESSING)
        updated = db.get_pdf(pdf_id)
        assert updated.status == PDFStatus.PROCESSING

    def test_delete_pdf(self, db):
        """测试删除PDF"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)

        assert db.delete_pdf(pdf_id)
        assert db.get_pdf(pdf_id) is None


class TestPageOperations:
    """页面操作测试"""

    def test_create_page(self, db):
        """测试创建页面"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)

        page = PDFPage(pdf_id=pdf_id, page_number=1)
        page_id = db.create_page(page)
        assert page_id > 0

    def test_update_page_ocr(self, db):
        """测试更新页面OCR"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)

        page = PDFPage(pdf_id=pdf_id, page_number=1)
        page_id = db.create_page(page)

        db.update_page_ocr(page_id, "识别的文本", OCRStatus.DONE)
        updated = db.get_page(page_id)
        assert updated.ocr_text == "识别的文本"
        assert updated.ocr_status == OCRStatus.DONE

    def test_cascade_delete(self, db):
        """测试级联删除"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)

        page = PDFPage(pdf_id=pdf_id, page_number=1)
        db.create_page(page)

        db.delete_pdf(pdf_id)
        pages = db.get_pages_by_pdf(pdf_id)
        assert len(pages) == 0


class TestStatistics:
    """统计操作测试"""

    def test_get_pdf_count(self, db):
        """测试获取PDF数量"""
        pdf1 = PDF(filename="test1.pdf", file_path="/path/1")
        pdf2 = PDF(filename="test2.pdf", file_path="/path/2")
        db.create_pdf(pdf1)
        db.create_pdf(pdf2)

        assert db.get_pdf_count() == 2

    def test_get_status_counts(self, db):
        """测试获取状态统计"""
        pdf1 = PDF(filename="test1.pdf", file_path="/path/1", status=PDFStatus.DONE)
        pdf2 = PDF(filename="test2.pdf", file_path="/path/2", status=PDFStatus.PROCESSING)
        db.create_pdf(pdf1)
        db.create_pdf(pdf2)

        counts = db.get_status_counts()
        assert counts.get("done") == 1
        assert counts.get("processing") == 1
```

- [ ] **Step 3: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_database.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add src/models/database.py tests/test_database.py
git commit -m "feat: 添加数据库操作模块"
```

---

## Chunk 2: Services Layer

### Task 6: PDF处理服务

**Files:**
- Create: `src/services/__init__.py`
- Create: `src/services/pdf_service.py`
- Create: `tests/test_pdf_service.py`

- [ ] **Step 1: 创建 services/__init__.py**

```python
"""服务层模块"""
from .pdf_service import PDFService
from .ocr_service import OCRService
from .index_service import IndexService

__all__ = ["PDFService", "OCRService", "IndexService"]
```

- [ ] **Step 2: 创建PDF处理服务**

```python
# src/services/pdf_service.py
"""PDF处理服务"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io

from src.models.schemas import PDFType


class PDFService:
    """PDF处理服务类"""

    def __init__(self, thumbnail_size: int = 200):
        """
        初始化PDF服务

        Args:
            thumbnail_size: 缩略图尺寸
        """
        self.thumbnail_size = thumbnail_size

    def validate_pdf(self, file_path: Path) -> bool:
        """
        验证PDF文件是否有效

        Args:
            file_path: PDF文件路径

        Returns:
            是否为有效PDF
        """
        try:
            doc = fitz.open(file_path)
            doc.close()
            return True
        except Exception:
            return False

    def get_page_count(self, file_path: Path) -> int:
        """
        获取PDF页数

        Args:
            file_path: PDF文件路径

        Returns:
            页数
        """
        doc = fitz.open(file_path)
        count = doc.page_count
        doc.close()
        return count

    def get_file_size(self, file_path: Path) -> int:
        """
        获取文件大小

        Args:
            file_path: PDF文件路径

        Returns:
            文件大小（字节）
        """
        return file_path.stat().st_size

    def detect_pdf_type(self, file_path: Path, sample_pages: int = 3) -> PDFType:
        """
        检测PDF类型

        Args:
            file_path: PDF文件路径
            sample_pages: 检测的样本页数

        Returns:
            PDF类型
        """
        doc = fitz.open(file_path)
        pages_to_check = min(sample_pages, doc.page_count)
        has_text = False

        for i in range(pages_to_check):
            text = doc[i].get_text()
            if len(text.strip()) > 50:
                has_text = True
                break

        doc.close()
        return PDFType.TEXT if has_text else PDFType.SCANNED

    def extract_text_from_page(self, file_path: Path, page_number: int) -> str:
        """
        从指定页面提取文本

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）

        Returns:
            提取的文本
        """
        doc = fitz.open(file_path)
        if 0 <= page_number < doc.page_count:
            text = doc[page_number].get_text()
            doc.close()
            return text.strip()
        doc.close()
        return ""

    def extract_all_text(self, file_path: Path) -> str:
        """
        提取PDF所有文本

        Args:
            file_path: PDF文件路径

        Returns:
            提取的文本
        """
        doc = fitz.open(file_path)
        texts = []
        for i in range(doc.page_count):
            text = doc[i].get_text().strip()
            if text:
                texts.append(text)
        doc.close()
        return "\n".join(texts)

    def render_page_to_image(
        self, file_path: Path, page_number: int, dpi: int = 150
    ) -> Optional[Image.Image]:
        """
        将PDF页面渲染为图像

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）
            dpi: 渲染DPI

        Returns:
            PIL Image对象
        """
        doc = fitz.open(file_path)
        if 0 <= page_number < doc.page_count:
            page = doc[page_number]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
        doc.close()
        return None

    def generate_thumbnail(
        self, file_path: Path, page_number: int
    ) -> Optional[Image.Image]:
        """
        生成页面缩略图

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）

        Returns:
            缩略图Image对象
        """
        img = self.render_page_to_image(file_path, page_number, dpi=72)
        if img:
            # 计算缩略图尺寸，保持宽高比
            ratio = self.thumbnail_size / max(img.width, img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            return img.resize(new_size, Image.Resampling.LANCZOS)
        return None

    def save_thumbnail(
        self, file_path: Path, page_number: int, output_path: Path
    ) -> bool:
        """
        保存页面缩略图

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）
            output_path: 输出路径

        Returns:
            是否成功
        """
        thumbnail = self.generate_thumbnail(file_path, page_number)
        if thumbnail:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            thumbnail.save(output_path, "PNG")
            return True
        return False
```

- [ ] **Step 3: 创建测试**

```python
# tests/test_pdf_service.py
"""PDF处理服务测试"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image

from src.services.pdf_service import PDFService
from src.models.schemas import PDFType


@pytest.fixture
def pdf_service():
    """创建PDF服务实例"""
    return PDFService(thumbnail_size=200)


@pytest.fixture
def sample_pdf_path():
    """创建示例PDF文件路径（需要实际PDF文件）"""
    # 这里使用一个简单的测试PDF
    # 在实际测试中，需要准备真实的PDF文件
    return None


class TestPDFService:
    """PDF服务测试"""

    def test_thumbnail_size(self, pdf_service):
        """测试缩略图尺寸设置"""
        assert pdf_service.thumbnail_size == 200

    def test_validate_pdf_invalid(self, pdf_service):
        """测试验证无效PDF"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"Not a PDF file")
            invalid_path = Path(f.name)

        try:
            assert not pdf_service.validate_pdf(invalid_path)
        finally:
            invalid_path.unlink()

    def test_detect_pdf_type_with_text(self, pdf_service):
        """测试检测文字型PDF（需要真实PDF）"""
        # 此测试需要真实的PDF文件
        # 在CI/CD中应该使用预置的测试PDF
        pass

    def test_render_page_to_image_invalid_page(self, pdf_service):
        """测试渲染无效页码"""
        # 需要真实PDF文件
        pass

    def test_generate_thumbnail_respects_size(self, pdf_service):
        """测试缩略图尺寸"""
        # 需要真实PDF文件
        pass
```

- [ ] **Step 4: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_pdf_service.py -v
```

Expected: 基础测试通过

- [ ] **Step 5: 提交**

```bash
git add src/services/ tests/test_pdf_service.py
git commit -m "feat: 添加PDF处理服务"
```

---

### Task 7: OCR处理服务

**Files:**
- Create: `src/services/ocr_service.py`
- Create: `tests/test_ocr_service.py`

- [ ] **Step 1: 创建OCR服务**

```python
# src/services/ocr_service.py
"""OCR处理服务"""

from pathlib import Path
from typing import Optional, List
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger()


class OCRService:
    """OCR处理服务类"""

    def __init__(self, lang: str = "ch", use_gpu: bool = False):
        """
        初始化OCR服务

        Args:
            lang: OCR语言，ch表示中文
            use_gpu: 是否使用GPU
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self._ocr = None

    @property
    def ocr(self):
        """延迟加载OCR引擎"""
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                use_gpu=self.use_gpu,
                show_log=False
            )
        return self._ocr

    def recognize_image(self, image: Image.Image) -> str:
        """
        识别图像中的文字

        Args:
            image: PIL Image对象

        Returns:
            识别的文字
        """
        try:
            # PaddleOCR需要numpy数组或文件路径
            import numpy as np
            img_array = np.array(image)

            result = self.ocr.ocr(img_array, cls=True)

            if not result or not result[0]:
                return ""

            # 提取所有识别的文本
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]  # line[1][0] 是识别的文字
                    texts.append(text)

            return "\n".join(texts)

        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return ""

    def recognize_image_file(self, image_path: Path) -> str:
        """
        识别图像文件中的文字

        Args:
            image_path: 图像文件路径

        Returns:
            识别的文字
        """
        try:
            image = Image.open(image_path)
            return self.recognize_image(image)
        except Exception as e:
            logger.error(f"无法打开图像文件 {image_path}: {e}")
            return ""

    def recognize_pdf_page(
        self, pdf_service, pdf_path: Path, page_number: int
    ) -> str:
        """
        识别PDF页面的文字

        Args:
            pdf_service: PDF服务实例
            pdf_path: PDF文件路径
            page_number: 页码（从0开始）

        Returns:
            识别的文字
        """
        # 渲染PDF页面为图像
        image = pdf_service.render_page_to_image(pdf_path, page_number)
        if image is None:
            logger.error(f"无法渲染PDF页面: {pdf_path}, 页码: {page_number}")
            return ""

        # OCR识别
        return self.recognize_image(image)

    def is_available(self) -> bool:
        """
        检查OCR服务是否可用

        Returns:
            是否可用
        """
        try:
            # 尝试初始化OCR引擎
            _ = self.ocr
            return True
        except Exception as e:
            logger.error(f"OCR服务不可用: {e}")
            return False
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_ocr_service.py
"""OCR处理服务测试"""

import pytest
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np

from src.services.ocr_service import OCRService


class TestOCRService:
    """OCR服务测试"""

    def test_init(self):
        """测试初始化"""
        service = OCRService(lang="ch", use_gpu=False)
        assert service.lang == "ch"
        assert service.use_gpu is False
        assert service._ocr is None

    @patch("src.services.ocr_service.PaddleOCR")
    def test_lazy_load_ocr(self, mock_paddle_ocr):
        """测试延迟加载OCR引擎"""
        mock_ocr_instance = Mock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        service = OCRService()
        # 第一次访问会加载
        _ = service.ocr
        mock_paddle_ocr.assert_called_once()

        # 第二次访问不会重复加载
        _ = service.ocr
        mock_paddle_ocr.assert_called_once()

    @patch("src.services.ocr_service.PaddleOCR")
    def test_recognize_image(self, mock_paddle_ocr):
        """测试图像识别"""
        # 模拟OCR返回结果
        mock_ocr_instance = Mock()
        mock_ocr_instance.ocr.return_value = [
            [
                [[0, 0], [100, 0], [100, 20], [0, 20]],  # 位置
                ("测试文字", 0.99)  # (文字, 置信度)
            ]
        ]
        mock_paddle_ocr.return_value = mock_ocr_instance

        service = OCRService()
        service._ocr = mock_ocr_instance  # 直接设置避免初始化

        # 创建测试图像
        image = Image.new("RGB", (100, 100), color="white")
        result = service.recognize_image(image)

        assert "测试文字" in result

    @patch("src.services.ocr_service.PaddleOCR")
    def test_recognize_image_empty_result(self, mock_paddle_ocr):
        """测试空识别结果"""
        mock_ocr_instance = Mock()
        mock_ocr_instance.ocr.return_value = [[]]
        mock_paddle_ocr.return_value = mock_ocr_instance

        service = OCRService()
        service._ocr = mock_ocr_instance

        image = Image.new("RGB", (100, 100), color="white")
        result = service.recognize_image(image)

        assert result == ""
```

- [ ] **Step 3: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_ocr_service.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add src/services/ocr_service.py tests/test_ocr_service.py
git commit -m "feat: 添加OCR处理服务"
```

---

### Task 8: 索引服务（Whoosh + jieba）

**Files:**
- Create: `src/services/index_service.py`
- Create: `tests/test_index_service.py`

- [ ] **Step 1: 创建索引服务**

```python
# src/services/index_service.py
"""全文搜索索引服务"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import Schema, ID, STORED, TEXT
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import highlight
import jieba
from jieba.analyse import ChineseAnalyzer

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class SearchResult:
    """搜索结果"""
    page_id: str
    pdf_id: int
    page_number: int
    folder_id: Optional[int]
    filename: str
    score: float
    snippet: str


class IndexService:
    """Whoosh索引服务"""

    # 定义索引Schema
    SCHEMA = Schema(
        page_id=ID(stored=True, unique=True),
        pdf_id=STORED,
        page_number=STORED,
        folder_id=STORED,
        filename=TEXT(stored=True, analyzer=ChineseAnalyzer()),
        content=TEXT(stored=True, analyzer=ChineseAnalyzer()),
    )

    def __init__(self, index_path: Path):
        """
        初始化索引服务

        Args:
            index_path: 索引存储路径
        """
        self.index_path = index_path
        self._index = None

    @property
    def index(self):
        """获取或创建索引"""
        if self._index is None:
            self.index_path.mkdir(parents=True, exist_ok=True)
            if exists_in(str(self.index_path)):
                self._index = open_dir(str(self.index_path))
            else:
                self._index = create_in(str(self.index_path), self.SCHEMA)
        return self._index

    def add_page(
        self,
        page_id: int,
        pdf_id: int,
        page_number: int,
        folder_id: Optional[int],
        filename: str,
        content: str,
    ) -> bool:
        """
        添加页面到索引

        Args:
            page_id: 页面ID
            pdf_id: PDF ID
            page_number: 页码
            folder_id: 文件夹ID
            filename: 文件名
            content: 页面内容

        Returns:
            是否成功
        """
        try:
            writer = self.index.writer()
            writer.update_document(
                page_id=str(page_id),
                pdf_id=pdf_id,
                page_number=page_number,
                folder_id=folder_id,
                filename=filename,
                content=content,
            )
            writer.commit()
            return True
        except Exception as e:
            logger.error(f"添加索引失败: {e}")
            return False

    def delete_page(self, page_id: int) -> bool:
        """
        从索引删除页面

        Args:
            page_id: 页面ID

        Returns:
            是否成功
        """
        try:
            writer = self.index.writer()
            writer.delete_by_term("page_id", str(page_id))
            writer.commit()
            return True
        except Exception as e:
            logger.error(f"删除索引失败: {e}")
            return False

    def delete_pdf(self, pdf_id: int) -> int:
        """
        删除PDF的所有页面索引

        Args:
            pdf_id: PDF ID

        Returns:
            删除的文档数量
        """
        try:
            count = 0
            writer = self.index.writer()
            # 遍历所有文档，删除匹配的
            with self.index.searcher() as searcher:
                for doc in searcher.all_stored_fields():
                    if doc.get("pdf_id") == pdf_id:
                        writer.delete_by_term("page_id", doc["page_id"])
                        count += 1
            writer.commit()
            return count
        except Exception as e:
            logger.error(f"删除PDF索引失败: {e}")
            return 0

    def search(
        self,
        query_text: str,
        limit: int = 50,
        folder_id: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        搜索

        Args:
            query_text: 搜索词
            limit: 结果数量限制
            folder_id: 限定文件夹ID

        Returns:
            搜索结果列表
        """
        results = []

        try:
            # 使用jieba分词
            query_text = " ".join(jieba.cut(query_text))

            with self.index.searcher() as searcher:
                # 多字段搜索
                parser = MultifieldParser(
                    ["content", "filename"],
                    self.index.schema
                )
                query = parser.parse(query_text)

                # 执行搜索
                hits = searcher.search(query, limit=limit)

                for hit in hits:
                    # 生成高亮片段
                    snippet = self._generate_snippet(hit, "content", query_text)

                    result = SearchResult(
                        page_id=hit["page_id"],
                        pdf_id=hit["pdf_id"],
                        page_number=hit["page_number"],
                        folder_id=hit.get("folder_id"),
                        filename=hit["filename"],
                        score=hit.score,
                        snippet=snippet,
                    )

                    # 文件夹过滤
                    if folder_id is not None and result.folder_id != folder_id:
                        continue

                    results.append(result)

        except Exception as e:
            logger.error(f"搜索失败: {e}")

        return results

    def _generate_snippet(
        self, hit, field_name: str, query_text: str, max_length: int = 150
    ) -> str:
        """
        生成高亮片段

        Args:
            hit: 搜索结果
            field_name: 字段名
            query_text: 查询文本
            max_length: 最大长度

        Returns:
            片段文本
        """
        content = hit.get(field_name, "")
        if not content:
            return ""

        # 使用Whoosh高亮功能
        fragmenter = highlight.ContextFragmenter(maxchars=max_length)
        formatter = highlight.HtmlFormatter(tagname="mark")

        # 简单截取
        if len(content) <= max_length:
            return content

        return content[:max_length] + "..."

    def get_page_count(self) -> int:
        """获取索引中的页面数量"""
        with self.index.searcher() as searcher:
            return searcher.doc_count()

    def clear(self) -> bool:
        """清空索引"""
        try:
            writer = self.index.writer()
            writer.commit(mergetype="clear")
            return True
        except Exception as e:
            logger.error(f"清空索引失败: {e}")
            return False
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_index_service.py
"""索引服务测试"""

import pytest
import tempfile
from pathlib import Path

from src.services.index_service import IndexService, SearchResult


@pytest.fixture
def index_service():
    """创建索引服务实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = Path(tmpdir) / "index"
        yield IndexService(index_path)


class TestIndexService:
    """索引服务测试"""

    def test_add_page(self, index_service):
        """测试添加页面"""
        result = index_service.add_page(
            page_id=1,
            pdf_id=1,
            page_number=1,
            folder_id=None,
            filename="test.pdf",
            content="这是一段测试文本，用于测试搜索功能。"
        )
        assert result is True
        assert index_service.get_page_count() == 1

    def test_search(self, index_service):
        """测试搜索"""
        # 添加测试数据
        index_service.add_page(
            page_id=1,
            pdf_id=1,
            page_number=1,
            folder_id=None,
            filename="报告.pdf",
            content="这是一份年度工作报告，包含业绩数据和分析。"
        )
        index_service.add_page(
            page_id=2,
            pdf_id=1,
            page_number=2,
            folder_id=None,
            filename="报告.pdf",
            content="第二页是技术文档的内容。"
        )

        # 搜索
        results = index_service.search("报告")
        assert len(results) >= 1

    def test_search_chinese(self, index_service):
        """测试中文搜索"""
        index_service.add_page(
            page_id=1,
            pdf_id=1,
            page_number=1,
            folder_id=None,
            filename="测试.pdf",
            content="我们正在进行中文分词测试，验证搜索引擎的准确性。"
        )

        results = index_service.search("中文分词")
        assert len(results) >= 1

    def test_delete_page(self, index_service):
        """测试删除页面"""
        index_service.add_page(
            page_id=1,
            pdf_id=1,
            page_number=1,
            folder_id=None,
            filename="test.pdf",
            content="测试内容"
        )

        assert index_service.get_page_count() == 1
        index_service.delete_page(1)
        assert index_service.get_page_count() == 0

    def test_delete_pdf(self, index_service):
        """测试删除PDF的所有页面"""
        index_service.add_page(1, 1, 1, None, "test.pdf", "内容1")
        index_service.add_page(2, 1, 2, None, "test.pdf", "内容2")
        index_service.add_page(3, 2, 1, None, "other.pdf", "内容3")

        count = index_service.delete_pdf(1)
        assert count == 2
        assert index_service.get_page_count() == 1

    def test_folder_filter(self, index_service):
        """测试文件夹过滤"""
        index_service.add_page(1, 1, 1, 1, "test.pdf", "测试内容")
        index_service.add_page(2, 2, 1, 2, "test.pdf", "测试内容")

        results = index_service.search("测试", folder_id=1)
        assert len(results) == 1
        assert results[0].folder_id == 1

    def test_clear(self, index_service):
        """测试清空索引"""
        index_service.add_page(1, 1, 1, None, "test.pdf", "内容")
        assert index_service.get_page_count() == 1

        index_service.clear()
        assert index_service.get_page_count() == 0
```

- [ ] **Step 3: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_index_service.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add src/services/index_service.py tests/test_index_service.py
git commit -m "feat: 添加全文搜索索引服务"
```

---

## Chunk 3: Business Logic Layer

### Task 9: 文件夹管理服务

**Files:**
- Create: `src/core/__init__.py`
- Create: `src/core/folder_manager.py`
- Create: `tests/test_folder_manager.py`

- [ ] **Step 1: 创建 core/__init__.py**

```python
"""业务逻辑层模块"""
from .folder_manager import FolderManager
from .pdf_manager import PDFManager
from .search_service import SearchService

__all__ = ["FolderManager", "PDFManager", "SearchService"]
```

- [ ] **Step 2: 创建文件夹管理服务**

```python
# src/core/folder_manager.py
"""文件夹管理服务"""

from typing import List, Optional
from pathlib import Path

from src.models.database import Database
from src.models.schemas import Folder
from src.utils.logger import get_logger

logger = get_logger()


class FolderManager:
    """文件夹管理服务类"""

    def __init__(self, database: Database):
        """
        初始化文件夹管理服务

        Args:
            database: 数据库实例
        """
        self.db = database

    def create_folder(self, name: str, parent_id: Optional[int] = None) -> Folder:
        """
        创建文件夹

        Args:
            name: 文件夹名称
            parent_id: 父文件夹ID

        Returns:
            创建的文件夹对象
        """
        folder = Folder(name=name, parent_id=parent_id)
        folder.id = self.db.create_folder(folder)
        logger.info(f"创建文件夹: {name}, ID: {folder.id}")
        return folder

    def get_folder(self, folder_id: int) -> Optional[Folder]:
        """获取文件夹"""
        return self.db.get_folder(folder_id)

    def get_root_folders(self) -> List[Folder]:
        """获取根文件夹列表"""
        return self.db.get_folders_by_parent(None)

    def get_child_folders(self, parent_id: int) -> List[Folder]:
        """获取子文件夹列表"""
        return self.db.get_folders_by_parent(parent_id)

    def get_all_folders(self) -> List[Folder]:
        """获取所有文件夹"""
        return self.db.get_all_folders()

    def rename_folder(self, folder_id: int, new_name: str) -> bool:
        """
        重命名文件夹

        Args:
            folder_id: 文件夹ID
            new_name: 新名称

        Returns:
            是否成功
        """
        folder = self.db.get_folder(folder_id)
        if folder is None:
            logger.warning(f"文件夹不存在: {folder_id}")
            return False

        folder.name = new_name
        result = self.db.update_folder(folder)
        if result:
            logger.info(f"重命名文件夹: {folder_id} -> {new_name}")
        return result

    def move_folder(self, folder_id: int, new_parent_id: Optional[int]) -> bool:
        """
        移动文件夹

        Args:
            folder_id: 文件夹ID
            new_parent_id: 新父文件夹ID

        Returns:
            是否成功
        """
        # 检查是否会导致循环引用
        if new_parent_id is not None:
            if self._would_create_cycle(folder_id, new_parent_id):
                logger.warning(f"移动文件夹会导致循环引用: {folder_id} -> {new_parent_id}")
                return False

        folder = self.db.get_folder(folder_id)
        if folder is None:
            return False

        folder.parent_id = new_parent_id
        result = self.db.update_folder(folder)
        if result:
            logger.info(f"移动文件夹: {folder_id} 到 {new_parent_id}")
        return result

    def delete_folder(self, folder_id: int, delete_contents: bool = False) -> bool:
        """
        删除文件夹

        Args:
            folder_id: 文件夹ID
            delete_contents: 是否删除文件夹内的内容

        Returns:
            是否成功
        """
        # 检查是否有子文件夹
        children = self.db.get_folders_by_parent(folder_id)
        if children and not delete_contents:
            logger.warning(f"文件夹 {folder_id} 有子文件夹，无法删除")
            return False

        # TODO: 检查是否有PDF文件

        result = self.db.delete_folder(folder_id)
        if result:
            logger.info(f"删除文件夹: {folder_id}")
        return result

    def get_folder_path(self, folder_id: int) -> List[Folder]:
        """
        获取文件夹路径（从根到当前文件夹）

        Args:
            folder_id: 文件夹ID

        Returns:
            文件夹路径列表
        """
        path = []
        current = self.db.get_folder(folder_id)
        while current:
            path.insert(0, current)
            if current.parent_id:
                current = self.db.get_folder(current.parent_id)
            else:
                break
        return path

    def _would_create_cycle(self, folder_id: int, target_parent_id: int) -> bool:
        """检查是否会导致循环引用"""
        current_id = target_parent_id
        while current_id:
            if current_id == folder_id:
                return True
            folder = self.db.get_folder(current_id)
            if folder:
                current_id = folder.parent_id
            else:
                break
        return False
```

- [ ] **Step 3: 创建测试**

```python
# tests/test_folder_manager.py
"""文件夹管理服务测试"""

import pytest
import tempfile
from pathlib import Path

from src.models.database import Database
from src.models.schemas import Folder
from src.core.folder_manager import FolderManager


@pytest.fixture
def folder_manager():
    """创建文件夹管理器实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path)
        yield FolderManager(db)


class TestFolderManager:
    """文件夹管理器测试"""

    def test_create_folder(self, folder_manager):
        """测试创建文件夹"""
        folder = folder_manager.create_folder("测试文件夹")
        assert folder.id is not None
        assert folder.name == "测试文件夹"

    def test_create_nested_folder(self, folder_manager):
        """测试创建嵌套文件夹"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        assert child.parent_id == parent.id

    def test_get_root_folders(self, folder_manager):
        """测试获取根文件夹"""
        folder_manager.create_folder("文件夹1")
        folder_manager.create_folder("文件夹2")

        roots = folder_manager.get_root_folders()
        assert len(roots) == 2

    def test_get_child_folders(self, folder_manager):
        """测试获取子文件夹"""
        parent = folder_manager.create_folder("父文件夹")
        folder_manager.create_folder("子文件夹1", parent_id=parent.id)
        folder_manager.create_folder("子文件夹2", parent_id=parent.id)

        children = folder_manager.get_child_folders(parent.id)
        assert len(children) == 2

    def test_rename_folder(self, folder_manager):
        """测试重命名文件夹"""
        folder = folder_manager.create_folder("原名称")
        result = folder_manager.rename_folder(folder.id, "新名称")

        assert result
        updated = folder_manager.get_folder(folder.id)
        assert updated.name == "新名称"

    def test_move_folder(self, folder_manager):
        """测试移动文件夹"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹")

        result = folder_manager.move_folder(child.id, parent.id)
        assert result

        moved = folder_manager.get_folder(child.id)
        assert moved.parent_id == parent.id

    def test_prevent_cycle(self, folder_manager):
        """测试防止循环引用"""
        parent = folder_manager.create_folder("父文件夹")
        child = folder_manager.create_folder("子文件夹", parent_id=parent.id)

        # 尝试将父文件夹移动到子文件夹下
        result = folder_manager.move_folder(parent.id, child.id)
        assert not result  # 应该失败

    def test_get_folder_path(self, folder_manager):
        """测试获取文件夹路径"""
        f1 = folder_manager.create_folder("文件夹1")
        f2 = folder_manager.create_folder("文件夹2", parent_id=f1.id)
        f3 = folder_manager.create_folder("文件夹3", parent_id=f2.id)

        path = folder_manager.get_folder_path(f3.id)
        assert len(path) == 3
        assert path[0].id == f1.id
        assert path[1].id == f2.id
        assert path[2].id == f3.id
```

- [ ] **Step 4: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_folder_manager.py -v
```

Expected: 所有测试通过

- [ ] **Step 5: 提交**

```bash
git add src/core/ tests/test_folder_manager.py
git commit -m "feat: 添加文件夹管理服务"
```

---

### Task 10: PDF管理服务

**Files:**
- Create: `src/core/pdf_manager.py`
- Create: `tests/test_pdf_manager.py`

- [ ] **Step 1: 创建PDF管理服务**

```python
# src/core/pdf_manager.py
"""PDF管理服务"""

import shutil
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from src.models.database import Database
from src.models.schemas import PDF, PDFPage, PDFType, PDFStatus, OCRStatus
from src.services.pdf_service import PDFService
from src.services.ocr_service import OCRService
from src.services.index_service import IndexService
from src.utils.logger import get_logger

logger = get_logger()


class ImportResult(Enum):
    """导入结果"""
    SUCCESS = "success"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class ImportStatus:
    """导入状态"""
    result: ImportResult
    pdf_id: Optional[int] = None
    message: str = ""


class PDFManager:
    """PDF管理服务类"""

    def __init__(
        self,
        database: Database,
        pdf_service: PDFService,
        ocr_service: OCRService,
        index_service: IndexService,
        storage_path: Path,
    ):
        """
        初始化PDF管理服务

        Args:
            database: 数据库实例
            pdf_service: PDF服务实例
            ocr_service: OCR服务实例
            index_service: 索引服务实例
            storage_path: 存储路径
        """
        self.db = database
        self.pdf_service = pdf_service
        self.ocr_service = ocr_service
        self.index_service = index_service
        self.storage_path = storage_path
        self.pdfs_path = storage_path / "pdfs"
        self.thumbnails_path = storage_path / "thumbnails"

        # 确保目录存在
        self.pdfs_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)

    def import_pdf(
        self,
        source_path: Path,
        folder_id: Optional[int] = None,
        process_ocr: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> ImportStatus:
        """
        导入PDF文件

        Args:
            source_path: 源PDF文件路径
            folder_id: 目标文件夹ID
            process_ocr: 是否处理OCR
            progress_callback: 进度回调函数

        Returns:
            导入状态
        """
        # 验证文件
        if not source_path.exists():
            return ImportStatus(ImportResult.ERROR, message="文件不存在")

        if not self.pdf_service.validate_pdf(source_path):
            return ImportStatus(ImportResult.INVALID, message="无效的PDF文件")

        # 检查重复（基于文件名和大小）
        if self._is_duplicate(source_path, folder_id):
            return ImportStatus(ImportResult.DUPLICATE, message="文件已存在")

        try:
            # 获取PDF信息
            page_count = self.pdf_service.get_page_count(source_path)
            file_size = self.pdf_service.get_file_size(source_path)
            pdf_type = self.pdf_service.detect_pdf_type(source_path)

            # 复制文件到存储目录
            stored_filename = self._generate_stored_filename(source_path)
            stored_path = self.pdfs_path / stored_filename
            shutil.copy2(source_path, stored_path)

            # 创建数据库记录
            pdf = PDF(
                filename=source_path.name,
                file_path=str(stored_path),
                folder_id=folder_id,
                file_size=file_size,
                page_count=page_count,
                pdf_type=pdf_type,
                status=PDFStatus.PENDING,
            )
            pdf.id = self.db.create_pdf(pdf)

            # 创建页面记录
            for i in range(page_count):
                page = PDFPage(pdf_id=pdf.id, page_number=i + 1)
                page.id = self.db.create_page(page)

            # 处理OCR
            if process_ocr:
                self._process_pdf_ocr(pdf, progress_callback)

            logger.info(f"导入PDF: {source_path.name}, ID: {pdf.id}")
            return ImportStatus(ImportResult.SUCCESS, pdf_id=pdf.id)

        except Exception as e:
            logger.error(f"导入PDF失败: {e}")
            return ImportStatus(ImportResult.ERROR, message=str(e))

    def _process_pdf_ocr(
        self,
        pdf: PDF,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """处理PDF的OCR"""
        self.db.update_pdf_status(pdf.id, PDFStatus.PROCESSING)
        pages = self.db.get_pages_by_pdf(pdf.id)
        pdf_path = Path(pdf.file_path)

        for i, page in enumerate(pages):
            try:
                # 根据PDF类型选择处理方式
                if pdf.pdf_type == PDFType.TEXT:
                    # 直接提取文字
                    text = self.pdf_service.extract_text_from_page(pdf_path, i)
                else:
                    # OCR识别
                    text = self.ocr_service.recognize_pdf_page(
                        self.pdf_service, pdf_path, i
                    )

                # 更新页面
                self.db.update_page_ocr(page.id, text, OCRStatus.DONE)

                # 添加到索引
                self.index_service.add_page(
                    page_id=page.id,
                    pdf_id=pdf.id,
                    page_number=page.page_number,
                    folder_id=pdf.folder_id,
                    filename=pdf.filename,
                    content=text,
                )

                # 生成缩略图
                thumbnail_path = self.thumbnails_path / f"{pdf.id}_{page.page_number}.png"
                self.pdf_service.save_thumbnail(pdf_path, i, thumbnail_path)
                page.thumbnail_path = str(thumbnail_path)
                self.db.update_page(page)

                # 进度回调
                if progress_callback:
                    progress_callback(i + 1, len(pages))

            except Exception as e:
                logger.error(f"处理页面 {page.page_number} 失败: {e}")
                self.db.update_page_ocr(page.id, "", OCRStatus.ERROR)

        self.db.update_pdf_status(pdf.id, PDFStatus.DONE)

    def delete_pdf(self, pdf_id: int) -> bool:
        """
        删除PDF及所有相关数据

        Args:
            pdf_id: PDF ID

        Returns:
            是否成功
        """
        pdf = self.db.get_pdf(pdf_id)
        if pdf is None:
            return False

        try:
            # 删除存储的PDF文件
            pdf_path = Path(pdf.file_path)
            if pdf_path.exists():
                pdf_path.unlink()

            # 删除缩略图
            pages = self.db.get_pages_by_pdf(pdf_id)
            for page in pages:
                if page.thumbnail_path:
                    thumb_path = Path(page.thumbnail_path)
                    if thumb_path.exists():
                        thumb_path.unlink()

            # 删除索引
            self.index_service.delete_pdf(pdf_id)

            # 删除数据库记录（级联删除页面）
            self.db.delete_pdf(pdf_id)

            logger.info(f"删除PDF: {pdf.filename}, ID: {pdf_id}")
            return True

        except Exception as e:
            logger.error(f"删除PDF失败: {e}")
            return False

    def get_pdf(self, pdf_id: int) -> Optional[PDF]:
        """获取PDF"""
        return self.db.get_pdf(pdf_id)

    def get_pdfs_by_folder(self, folder_id: Optional[int] = None) -> List[PDF]:
        """获取文件夹下的PDF列表"""
        return self.db.get_pdfs_by_folder(folder_id)

    def get_all_pdfs(self) -> List[PDF]:
        """获取所有PDF"""
        return self.db.get_all_pdfs()

    def get_page(self, page_id: int) -> Optional[PDFPage]:
        """获取页面"""
        return self.db.get_page(page_id)

    def get_pages_by_pdf(self, pdf_id: int) -> List[PDFPage]:
        """获取PDF的所有页面"""
        return self.db.get_pages_by_pdf(pdf_id)

    def move_pdf(self, pdf_id: int, folder_id: Optional[int]) -> bool:
        """移动PDF到其他文件夹"""
        pdf = self.db.get_pdf(pdf_id)
        if pdf is None:
            return False

        pdf.folder_id = folder_id
        result = self.db.update_pdf(pdf)

        # 更新索引
        pages = self.db.get_pages_by_pdf(pdf_id)
        for page in pages:
            self.index_service.add_page(
                page_id=page.id,
                pdf_id=pdf.id,
                page_number=page.page_number,
                folder_id=folder_id,
                filename=pdf.filename,
                content=page.ocr_text,
            )

        return result

    def reprocess_pdf(self, pdf_id: int) -> bool:
        """重新处理PDF的OCR"""
        pdf = self.db.get_pdf(pdf_id)
        if pdf is None:
            return False

        # 重置状态
        self.db.update_pdf_status(pdf_id, PDFStatus.PENDING)
        pages = self.db.get_pages_by_pdf(pdf_id)
        for page in pages:
            self.db.update_page_ocr(page.id, "", OCRStatus.PENDING)

        # 重新处理
        self._process_pdf_ocr(pdf)
        return True

    def _is_duplicate(self, source_path: Path, folder_id: Optional[int]) -> bool:
        """检查是否重复"""
        file_size = source_path.stat().st_size
        pdfs = self.db.get_pdfs_by_folder(folder_id)

        for pdf in pdfs:
            if pdf.filename == source_path.name and pdf.file_size == file_size:
                return True
        return False

    def _generate_stored_filename(self, source_path: Path) -> str:
        """生成存储文件名（避免冲突）"""
        import uuid
        stem = source_path.stem
        suffix = source_path.suffix
        unique_id = uuid.uuid4().hex[:8]
        return f"{stem}_{unique_id}{suffix}"

    def get_statistics(self) -> dict:
        """获取统计信息"""
        return {
            "total": self.db.get_pdf_count(),
            "status_counts": self.db.get_status_counts(),
        }
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_pdf_manager.py
"""PDF管理服务测试"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.models.database import Database
from src.models.schemas import PDFType, PDFStatus
from src.services.pdf_service import PDFService
from src.services.ocr_service import OCRService
from src.services.index_service import IndexService
from src.core.pdf_manager import PDFManager, ImportResult


@pytest.fixture
def pdf_manager():
    """创建PDF管理器实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        db_path = storage_path / "test.db"
        index_path = storage_path / "index"

        db = Database(db_path)
        pdf_service = PDFService()
        ocr_service = OCRService()
        index_service = IndexService(index_path)

        yield PDFManager(
            database=db,
            pdf_service=pdf_service,
            ocr_service=ocr_service,
            index_service=index_service,
            storage_path=storage_path,
        )


class TestPDFManager:
    """PDF管理器测试"""

    def test_import_nonexistent_file(self, pdf_manager):
        """测试导入不存在的文件"""
        result = pdf_manager.import_pdf(Path("/nonexistent/file.pdf"))
        assert result.result == ImportResult.ERROR

    def test_get_all_pdfs_empty(self, pdf_manager):
        """测试获取空PDF列表"""
        pdfs = pdf_manager.get_all_pdfs()
        assert len(pdfs) == 0

    def test_delete_nonexistent_pdf(self, pdf_manager):
        """测试删除不存在的PDF"""
        result = pdf_manager.delete_pdf(999)
        assert result is False

    def test_get_statistics(self, pdf_manager):
        """测试获取统计信息"""
        stats = pdf_manager.get_statistics()
        assert "total" in stats
        assert "status_counts" in stats
        assert stats["total"] == 0
```

- [ ] **Step 3: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_pdf_manager.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add src/core/pdf_manager.py tests/test_pdf_manager.py
git commit -m "feat: 添加PDF管理服务"
```

---

### Task 11: 搜索服务

**Files:**
- Create: `src/core/search_service.py`
- Create: `tests/test_search_service.py`

- [ ] **Step 1: 创建搜索服务**

```python
# src/core/search_service.py
"""搜索服务"""

from typing import List, Optional
from dataclasses import dataclass

from src.models.database import Database
from src.services.index_service import IndexService, SearchResult
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class GroupedSearchResult:
    """分组搜索结果"""
    pdf_id: int
    filename: str
    folder_id: Optional[int]
    match_count: int
    best_score: float
    pages: List[SearchResult]


class SearchService:
    """搜索服务类"""

    def __init__(self, database: Database, index_service: IndexService):
        """
        初始化搜索服务

        Args:
            database: 数据库实例
            index_service: 索引服务实例
        """
        self.db = database
        self.index_service = index_service

    def search(
        self,
        query: str,
        folder_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[SearchResult]:
        """
        搜索

        Args:
            query: 搜索词
            folder_id: 限定文件夹ID
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        if not query.strip():
            return []

        results = self.index_service.search(query, limit=limit, folder_id=folder_id)
        logger.info(f"搜索 '{query}' 返回 {len(results)} 条结果")
        return results

    def search_grouped(
        self,
        query: str,
        folder_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[GroupedSearchResult]:
        """
        分组搜索（按PDF文件分组）

        Args:
            query: 搜索词
            folder_id: 限定文件夹ID
            limit: 结果数量限制

        Returns:
            分组后的搜索结果
        """
        results = self.search(query, folder_id, limit)

        # 按PDF分组
        groups = {}
        for result in results:
            if result.pdf_id not in groups:
                pdf = self.db.get_pdf(result.pdf_id)
                groups[result.pdf_id] = GroupedSearchResult(
                    pdf_id=result.pdf_id,
                    filename=result.filename,
                    folder_id=result.folder_id,
                    match_count=0,
                    best_score=0,
                    pages=[],
                )

            group = groups[result.pdf_id]
            group.match_count += 1
            group.pages.append(result)
            if result.score > group.best_score:
                group.best_score = result.score

        # 按最佳分数排序
        grouped_results = list(groups.values())
        grouped_results.sort(key=lambda x: x.best_score, reverse=True)

        return grouped_results

    def get_page_content(self, page_id: int) -> Optional[str]:
        """
        获取页面内容

        Args:
            page_id: 页面ID

        Returns:
            页面内容
        """
        page = self.db.get_page(page_id)
        if page:
            return page.ocr_text
        return None

    def highlight_text(self, text: str, query: str, context_length: int = 100) -> str:
        """
        高亮搜索词

        Args:
            text: 原始文本
            query: 搜索词
            context_length: 上下文长度

        Returns:
            高亮后的文本片段
        """
        if not text or not query:
            return text

        import re
        # 简单的关键词高亮
        keywords = query.split()
        pattern = "|".join(re.escape(kw) for kw in keywords)

        # 找到第一个匹配位置
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return text[:context_length] + "..." if len(text) > context_length else text

        # 提取上下文
        start = max(0, match.start() - context_length // 2)
        end = min(len(text), match.end() + context_length // 2)

        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet
```

- [ ] **Step 2: 创建测试**

```python
# tests/test_search_service.py
"""搜索服务测试"""

import pytest
import tempfile
from pathlib import Path

from src.models.database import Database
from src.services.index_service import IndexService
from src.core.search_service import SearchService


@pytest.fixture
def search_service():
    """创建搜索服务实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        db_path = storage_path / "test.db"
        index_path = storage_path / "index"

        db = Database(db_path)
        index_service = IndexService(index_path)

        yield SearchService(db, index_service)


class TestSearchService:
    """搜索服务测试"""

    def test_search_empty_query(self, search_service):
        """测试空搜索"""
        results = search_service.search("")
        assert len(results) == 0

    def test_search_whitespace(self, search_service):
        """测试空白搜索"""
        results = search_service.search("   ")
        assert len(results) == 0

    def test_search_no_results(self, search_service):
        """测试无结果搜索"""
        results = search_service.search("不存在的关键词")
        assert len(results) == 0

    def test_highlight_text(self, search_service):
        """测试文本高亮"""
        text = "这是一段测试文本，用于测试高亮功能。"
        query = "测试"

        result = search_service.highlight_text(text, query)
        assert "测试" in result

    def test_highlight_text_not_found(self, search_service):
        """测试关键词未找到"""
        text = "这是一段普通文本。"
        query = "不存在"

        result = search_service.highlight_text(text, query)
        assert result == text
```

- [ ] **Step 3: 运行测试**

```bash
cd /root/PdfOCR && python -m pytest tests/test_search_service.py -v
```

Expected: 所有测试通过

- [ ] **Step 4: 提交**

```bash
git add src/core/search_service.py tests/test_search_service.py
git commit -m "feat: 添加搜索服务"
```

---

## Chunk 4: UI Layer

### Task 12: UI基础结构和主窗口

**Files:**
- Create: `src/ui/__init__.py`
- Create: `src/ui/main_window.py`

- [ ] **Step 1: 创建 ui/__init__.py**

```python
"""UI模块"""
```

- [ ] **Step 2: 创建主窗口**

```python
# src/ui/main_window.py
"""主窗口"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QFileDialog,
    QApplication, QProgressBar, QLabel,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

from src.models.schemas import PDF, Folder
from src.ui.widgets.folder_tree import FolderTreeWidget
from src.ui.widgets.pdf_list import PDFListWidget
from src.ui.widgets.pdf_viewer import PDFViewerWidget
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.utils.logger import get_logger

logger = get_logger()


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self, app_context):
        """
        初始化主窗口

        Args:
            app_context: 应用上下文对象，包含所有服务
        """
        super().__init__()
        self.app_context = app_context
        self.current_folder_id: Optional[int] = None
        self.current_pdf: Optional[PDF] = None

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()
        self._load_initial_data()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("PDF Manager")
        self.setMinimumSize(1200, 800)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板 - 文件夹树
        self.folder_tree = FolderTreeWidget()
        self.folder_tree.setMinimumWidth(200)
        self.folder_tree.setMaximumWidth(400)
        splitter.addWidget(self.folder_tree)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 创建右侧分割器
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # PDF列表
        self.pdf_list = PDFListWidget()
        right_splitter.addWidget(self.pdf_list)

        # PDF预览
        self.pdf_viewer = PDFViewerWidget()
        right_splitter.addWidget(self.pdf_viewer)

        # 设置分割比例
        right_splitter.setSizes([300, 500])

        right_layout.addWidget(right_splitter)
        splitter.addWidget(right_panel)

        # 设置分割比例
        splitter.setSizes([250, 950])

        main_layout.addWidget(splitter)

    def _setup_menu(self):
        """设置菜单"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        add_pdf_action = QAction("添加PDF(&A)", self)
        add_pdf_action.setShortcut(QKeySequence.StandardKey.Open)
        add_pdf_action.triggered.connect(self._on_add_pdf)
        file_menu.addAction(add_pdf_action)

        add_folder_action = QAction("添加文件夹(&F)", self)
        add_folder_action.triggered.connect(self._on_add_folder)
        file_menu.addAction(add_folder_action)

        file_menu.addSeparator()

        export_action = QAction("导出数据(&E)", self)
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        import_action = QAction("导入数据(&I)", self)
        import_action.triggered.connect(self._on_import)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        delete_action = QAction("删除(&D)", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self._on_delete)
        edit_menu.addAction(delete_action)

        # 设置菜单
        settings_menu = menubar.addMenu("设置(&S)")

        settings_action = QAction("偏好设置(&P)", self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.triggered.connect(self._on_settings)
        settings_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("就绪")
        self.statusbar.addPermanentWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def _connect_signals(self):
        """连接信号"""
        # 文件夹树信号
        self.folder_tree.folder_selected.connect(self._on_folder_selected)
        self.folder_tree.folder_created.connect(self._on_folder_created)

        # PDF列表信号
        self.pdf_list.pdf_selected.connect(self._on_pdf_selected)
        self.pdf_list.pdf_double_clicked.connect(self._on_pdf_double_clicked)
        self.pdf_list.add_pdf_clicked.connect(self._on_add_pdf)
        self.pdf_list.delete_pdf_clicked.connect(self._on_delete_pdf)

        # PDF预览信号
        self.pdf_viewer.open_external_clicked.connect(self._on_open_external)
        self.pdf_viewer.show_in_folder_clicked.connect(self._on_show_in_folder)

    def _load_initial_data(self):
        """加载初始数据"""
        # 加载文件夹
        self.folder_tree.load_folders(self.app_context.folder_manager.get_all_folders())
        self._update_status()

    def _update_status(self):
        """更新状态栏"""
        stats = self.app_context.pdf_manager.get_statistics()
        total = stats["total"]
        status_counts = stats["status_counts"]
        done = status_counts.get("done", 0)
        processing = status_counts.get("processing", 0)

        status_text = f"共 {total} 个PDF"
        if processing > 0:
            status_text += f" | 处理中 {processing} 个"
        status_text += f" | 已完成 {done} 个"

        self.status_label.setText(status_text)

    # ==================== 事件处理 ====================

    def _on_folder_selected(self, folder_id: Optional[int]):
        """文件夹选中事件"""
        self.current_folder_id = folder_id
        pdfs = self.app_context.pdf_manager.get_pdfs_by_folder(folder_id)
        self.pdf_list.load_pdfs(pdfs)

    def _on_folder_created(self, name: str, parent_id: Optional[int]):
        """创建文件夹"""
        folder = self.app_context.folder_manager.create_folder(name, parent_id)
        self.folder_tree.add_folder(folder)
        logger.info(f"创建文件夹: {name}")

    def _on_pdf_selected(self, pdf_id: int):
        """PDF选中事件"""
        pdf = self.app_context.pdf_manager.get_pdf(pdf_id)
        if pdf:
            self.current_pdf = pdf
            self.pdf_viewer.load_pdf(pdf)

    def _on_pdf_double_clicked(self, pdf_id: int):
        """PDF双击事件"""
        self._on_open_external()

    def _on_add_pdf(self):
        """添加PDF"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*)"
        )
        if files:
            self._import_pdfs([Path(f) for f in files])

    def _on_add_folder(self):
        """添加文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            pdf_files = list(Path(folder_path).glob("*.pdf"))
            if pdf_files:
                self._import_pdfs(pdf_files)

    def _import_pdfs(self, pdf_paths: list):
        """导入PDF文件"""
        from src.ui.dialogs.import_dialog import ImportDialog
        dialog = ImportDialog(self, self.app_context, pdf_paths, self.current_folder_id)
        dialog.exec()
        self._refresh_pdf_list()
        self._update_status()

    def _on_delete(self):
        """删除"""
        if self.current_pdf:
            self._on_delete_pdf(self.current_pdf.id)

    def _on_delete_pdf(self, pdf_id: int):
        """删除PDF"""
        pdf = self.app_context.pdf_manager.get_pdf(pdf_id)
        if not pdf:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 '{pdf.filename}' 吗？\n删除后将无法恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.app_context.pdf_manager.delete_pdf(pdf_id)
            self._refresh_pdf_list()
            self._update_status()
            logger.info(f"删除PDF: {pdf.filename}")

    def _refresh_pdf_list(self):
        """刷新PDF列表"""
        pdfs = self.app_context.pdf_manager.get_pdfs_by_folder(self.current_folder_id)
        self.pdf_list.load_pdfs(pdfs)

    def _on_open_external(self):
        """用外部程序打开"""
        if self.current_pdf:
            import subprocess
            import platform
            path = Path(self.current_pdf.file_path)
            if platform.system() == "Windows":
                subprocess.run(["start", "", str(path)], shell=True)
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])

    def _on_show_in_folder(self):
        """在文件夹中显示"""
        if self.current_pdf:
            import subprocess
            import platform
            path = Path(self.current_pdf.file_path)
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", str(path)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", str(path)])
            else:
                subprocess.run(["xdg-open", str(path.parent)])

    def _on_settings(self):
        """打开设置"""
        dialog = SettingsDialog(self, self.app_context)
        dialog.exec()

    def _on_export(self):
        """导出数据"""
        # TODO: 实现导出功能
        QMessageBox.information(self, "提示", "导出功能开发中")

    def _on_import(self):
        """导入数据"""
        # TODO: 实现导入功能
        QMessageBox.information(self, "提示", "导入功能开发中")

    def _on_about(self):
        """关于"""
        QMessageBox.about(
            self,
            "关于 PDF Manager",
            "PDF Manager v0.1.0\n\n"
            "本地PDF管理工具\n"
            "支持扫描版PDF的OCR识别和全文搜索"
        )

    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
```

- [ ] **Step 3: 提交**

```bash
git add src/ui/__init__.py src/ui/main_window.py
git commit -m "feat: 添加主窗口"
```

---

### Task 13: 文件夹树组件

**Files:**
- Create: `src/ui/widgets/__init__.py`
- Create: `src/ui/widgets/folder_tree.py`

- [ ] **Step 1: 创建 widgets/__init__.py**

```python
"""UI组件模块"""
```

- [ ] **Step 2: 创建文件夹树组件**

```python
# src/ui/widgets/folder_tree.py
"""文件夹树组件"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QDialog,
    QDialogButtonBox, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.models.schemas import Folder


class FolderTreeWidget(QWidget):
    """文件夹树组件"""

    folder_selected = pyqtSignal(object)  # folder_id or None
    folder_created = pyqtSignal(str, object)  # name, parent_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 标题栏
        header_layout = QHBoxLayout()
        header_label = QLabel("文件夹")
        header_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # 新建文件夹按钮
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(24, 24)
        self.add_button.setToolTip("新建文件夹")
        header_layout.addWidget(self.add_button)

        layout.addLayout(header_layout)

        # 树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.tree)

        # 添加"全部"项
        self.all_item = QTreeWidgetItem(self.tree, ["全部"])
        self.all_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self.tree.expandItem(self.all_item)

    def _connect_signals(self):
        """连接信号"""
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.add_button.clicked.connect(self._on_add_clicked)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

    def load_folders(self, folders: List[Folder]):
        """加载文件夹"""
        # 清除现有项（保留"全部"）
        self.tree.clear()
        self.all_item = QTreeWidgetItem(self.tree, ["全部"])
        self.all_item.setData(0, Qt.ItemDataRole.UserRole, None)

        # 构建文件夹树
        folder_map = {}
        for folder in folders:
            item = QTreeWidgetItem([folder.name])
            item.setData(0, Qt.ItemDataRole.UserRole, folder.id)
            folder_map[folder.id] = item

        # 设置父子关系
        for folder in folders:
            item = folder_map[folder.id]
            if folder.parent_id and folder.parent_id in folder_map:
                parent_item = folder_map[folder.parent_id]
                parent_item.addChild(item)
            else:
                self.all_item.addChild(item)

        self.tree.expandAll()

    def add_folder(self, folder: Folder):
        """添加文件夹项"""
        item = QTreeWidgetItem([folder.name])
        item.setData(0, Qt.ItemDataRole.UserRole, folder.id)

        if folder.parent_id:
            # 查找父项
            parent_item = self._find_item_by_id(folder.parent_id)
            if parent_item:
                parent_item.addChild(item)
        else:
            self.all_item.addChild(item)

        self.tree.expandAll()

    def _find_item_by_id(self, folder_id: int) -> Optional[QTreeWidgetItem]:
        """根据ID查找项"""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            result = self._find_item_recursive(item, folder_id)
            if result:
                return result
        return None

    def _find_item_recursive(self, parent: QTreeWidgetItem, folder_id: int) -> Optional[QTreeWidgetItem]:
        """递归查找项"""
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == folder_id:
                return child
            result = self._find_item_recursive(child, folder_id)
            if result:
                return result
        return None

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """项点击事件"""
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.folder_selected.emit(folder_id)

    def _on_add_clicked(self):
        """添加按钮点击"""
        # 获取当前选中的文件夹作为父文件夹
        current = self.tree.currentItem()
        parent_id = None
        if current and current != self.all_item:
            parent_id = current.data(0, Qt.ItemDataRole.UserRole)

        # 显示新建对话框
        dialog = NewFolderDialog(self, parent_id)
        if dialog.exec():
            name = dialog.get_name()
            self.folder_created.emit(name, parent_id)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        from PyQt6.QtWidgets import QMenu

        item = self.tree.itemAt(pos)
        if not item or item == self.all_item:
            return

        menu = QMenu(self)
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")

        action = menu.exec(self.tree.mapToGlobal(pos))

        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        if action == rename_action:
            self._rename_folder(item, folder_id)
        elif action == delete_action:
            self._delete_folder(folder_id)

    def _rename_folder(self, item: QTreeWidgetItem, folder_id: int):
        """重命名文件夹"""
        dialog = NewFolderDialog(self, None, initial_name=item.text(0), title="重命名文件夹")
        if dialog.exec():
            new_name = dialog.get_name()
            # TODO: 调用文件夹管理器重命名
            item.setText(0, new_name)

    def _delete_folder(self, folder_id: int):
        """删除文件夹"""
        # TODO: 实现删除逻辑
        pass


class NewFolderDialog(QDialog):
    """新建文件夹对话框"""

    def __init__(self, parent=None, parent_id: Optional[int] = None,
                 initial_name: str = "", title: str = "新建文件夹"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # 名称输入
        layout.addWidget(QLabel("文件夹名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setText(initial_name)
        self.name_edit.selectAll()
        layout.addWidget(self.name_edit)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_name(self) -> str:
        """获取文件夹名称"""
        return self.name_edit.text().strip()
```

- [ ] **Step 3: 提交**

```bash
git add src/ui/widgets/ src/ui/widgets/folder_tree.py
git commit -m "feat: 添加文件夹树组件"
```

---

### Task 14: PDF列表组件

**Files:**
- Create: `src/ui/widgets/pdf_list.py`

- [ ] **Step 1: 创建PDF列表组件**

```python
# src/ui/widgets/pdf_list.py
"""PDF列表组件"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QProgressBar, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from src.models.schemas import PDF, PDFStatus


class PDFListWidget(QWidget):
    """PDF列表组件"""

    pdf_selected = pyqtSignal(int)  # pdf_id
    pdf_double_clicked = pyqtSignal(int)  # pdf_id
    add_pdf_clicked = pyqtSignal()
    delete_pdf_clicked = pyqtSignal(int)  # pdf_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdfs: List[PDF] = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 搜索栏和操作按钮
        toolbar_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索PDF...")
        self.search_input.setMaximumWidth(300)
        toolbar_layout.addWidget(self.search_input)

        toolbar_layout.addStretch()

        self.add_button = QPushButton("添加PDF")
        toolbar_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("删除")
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)

        layout.addLayout(toolbar_layout)

        # PDF表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["文件名", "页数", "状态", "大小"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

    def _connect_signals(self):
        """连接信号"""
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        self.add_button.clicked.connect(lambda: self.add_pdf_clicked.emit())
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.search_input.textChanged.connect(self._on_search)

    def load_pdfs(self, pdfs: List[PDF]):
        """加载PDF列表"""
        self.pdfs = pdfs
        self._refresh_table(pdfs)

    def _refresh_table(self, pdfs: List[PDF]):
        """刷新表格"""
        self.table.setRowCount(len(pdfs))

        for row, pdf in enumerate(pdfs):
            # 文件名
            name_item = QTableWidgetItem(pdf.filename)
            name_item.setData(Qt.ItemDataRole.UserRole, pdf.id)
            self.table.setItem(row, 0, name_item)

            # 页数
            pages_item = QTableWidgetItem(f"{pdf.page_count}页")
            self.table.setItem(row, 1, pages_item)

            # 状态
            status_text = self._get_status_text(pdf)
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 2, status_item)

            # 大小
            size_text = self._format_size(pdf.file_size)
            size_item = QTableWidgetItem(size_text)
            self.table.setItem(row, 3, size_item)

    def _get_status_text(self, pdf: PDF) -> str:
        """获取状态文本"""
        if pdf.status == PDFStatus.DONE:
            return "✓ 已完成"
        elif pdf.status == PDFStatus.PROCESSING:
            return "处理中..."
        elif pdf.status == PDFStatus.ERROR:
            return "✗ 错误"
        else:
            return "等待处理"

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / 1024 / 1024:.1f} MB"
        else:
            return f"{size / 1024 / 1024 / 1024:.1f} GB"

    def _on_selection_changed(self):
        """选择变化事件"""
        selected = self.table.selectedItems()
        self.delete_button.setEnabled(len(selected) > 0)

        if selected:
            row = selected[0].row()
            pdf_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.pdf_selected.emit(pdf_id)

    def _on_double_click(self, row: int, column: int):
        """双击事件"""
        pdf_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.pdf_double_clicked.emit(pdf_id)

    def _on_delete_clicked(self):
        """删除按钮点击"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            pdf_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.delete_pdf_clicked.emit(pdf_id)

    def _on_search(self, text: str):
        """搜索事件"""
        if not text:
            self._refresh_table(self.pdfs)
            return

        # 过滤PDF
        filtered = [p for p in self.pdfs if text.lower() in p.filename.lower()]
        self._refresh_table(filtered)
```

- [ ] **Step 2: 提交**

```bash
git add src/ui/widgets/pdf_list.py
git commit -m "feat: 添加PDF列表组件"
```

---

### Task 15: PDF预览组件

**Files:**
- Create: `src/ui/widgets/pdf_viewer.py`

- [ ] **Step 1: 创建PDF预览组件**

```python
# src/ui/widgets/pdf_viewer.py
"""PDF预览组件"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QPainter

from src.models.schemas import PDF
from src.services.pdf_service import PDFService


class PDFViewerWidget(QWidget):
    """PDF预览组件"""

    open_external_clicked = pyqtSignal()
    show_in_folder_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf: Optional[PDF] = None
        self.pdf_service = PDFService()
        self.current_page = 0
        self.total_pages = 0

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 工具栏
        toolbar = QHBoxLayout()

        # 导航按钮
        self.prev_button = QPushButton("◀ 上一页")
        self.prev_button.setEnabled(False)
        toolbar.addWidget(self.prev_button)

        # 页码
        self.page_label = QLabel("0 / 0")
        toolbar.addWidget(self.page_label)

        self.next_button = QPushButton("下一页 ▶")
        self.next_button.setEnabled(False)
        toolbar.addWidget(self.next_button)

        toolbar.addStretch()

        # 操作按钮
        self.external_button = QPushButton("外部打开")
        toolbar.addWidget(self.external_button)

        self.folder_button = QPushButton("在文件夹中显示")
        toolbar.addWidget(self.folder_button)

        layout.addLayout(toolbar)

        # 预览区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        self.image_label.setMinimumSize(400, 500)
        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(self.scroll_area)

        # 连接信号
        self.prev_button.clicked.connect(self._prev_page)
        self.next_button.clicked.connect(self._next_page)
        self.external_button.clicked.connect(lambda: self.open_external_clicked.emit())
        self.folder_button.clicked.connect(lambda: self.show_in_folder_clicked.emit())

    def load_pdf(self, pdf: PDF):
        """加载PDF"""
        self.pdf = pdf
        self.current_page = 0
        self.total_pages = pdf.page_count

        self._update_navigation()
        self._render_current_page()

    def _render_current_page(self):
        """渲染当前页"""
        if not self.pdf:
            return

        pdf_path = Path(self.pdf.file_path)
        image = self.pdf_service.render_page_to_image(pdf_path, self.current_page, dpi=100)

        if image:
            # 转换为QPixmap
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            # 缩放以适应预览区域
            available_size = self.scroll_area.viewport().size()
            scaled_pixmap = pixmap.scaled(
                available_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("无法渲染页面")

    def _update_navigation(self):
        """更新导航状态"""
        self.page_label.setText(f"{self.current_page + 1} / {self.total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def _prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_navigation()
            self._render_current_page()

    def _next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_navigation()
            self._render_current_page()

    def go_to_page(self, page_number: int):
        """跳转到指定页"""
        if 0 <= page_number < self.total_pages:
            self.current_page = page_number
            self._update_navigation()
            self._render_current_page()

    def clear(self):
        """清除预览"""
        self.pdf = None
        self.current_page = 0
        self.total_pages = 0
        self.image_label.clear()
        self._update_navigation()
```

- [ ] **Step 2: 提交**

```bash
git add src/ui/widgets/pdf_viewer.py
git commit -m "feat: 添加PDF预览组件"
```

---

### Task 16: 对话框组件

**Files:**
- Create: `src/ui/dialogs/__init__.py`
- Create: `src/ui/dialogs/settings_dialog.py`
- Create: `src/ui/dialogs/import_dialog.py`

- [ ] **Step 1: 创建 dialogs/__init__.py**

```python
"""对话框模块"""
```

- [ ] **Step 2: 创建设置对话框**

```python
# src/ui/dialogs/settings_dialog.py
"""设置对话框"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QGroupBox,
    QDialogButtonBox, QFileDialog,
)


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None, app_context=None):
        super().__init__(parent)
        self.app_context = app_context
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 存储路径
        storage_group = QGroupBox("存储设置")
        storage_layout = QHBoxLayout(storage_group)

        storage_layout.addWidget(QLabel("存储路径:"))
        self.storage_path_edit = QLineEdit()
        storage_layout.addWidget(self.storage_path_edit)

        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self._browse_storage_path)
        storage_layout.addWidget(self.browse_button)

        layout.addWidget(storage_group)

        # OCR设置
        ocr_group = QGroupBox("OCR设置")
        ocr_layout = QHBoxLayout(ocr_group)

        ocr_layout.addWidget(QLabel("并发数:"))
        self.ocr_workers_spin = QSpinBox()
        self.ocr_workers_spin.setRange(1, 8)
        ocr_layout.addWidget(self.ocr_workers_spin)

        ocr_layout.addStretch()

        layout.addWidget(ocr_group)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_settings(self):
        """加载设置"""
        if self.app_context:
            config = self.app_context.config
            self.storage_path_edit.setText(str(config.storage_path))
            self.ocr_workers_spin.setValue(config.get("ocr_workers", 2))

    def _browse_storage_path(self):
        """浏览存储路径"""
        path = QFileDialog.getExistingDirectory(self, "选择存储路径")
        if path:
            self.storage_path_edit.setText(path)

    def _save_and_accept(self):
        """保存并接受"""
        if self.app_context:
            config = self.app_context.config
            config.storage_path = Path(self.storage_path_edit.text())
            config.set("ocr_workers", self.ocr_workers_spin.value())
            config.save()
            config.ensure_directories()

        self.accept()
```

- [ ] **Step 3: 创建导入对话框**

```python
# src/ui/dialogs/import_dialog.py
"""导入对话框"""

from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.models.schemas import PDFStatus


class ImportWorker(QThread):
    """导入工作线程"""

    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(int, int)  # success_count, error_count

    def __init__(self, pdf_manager, pdf_paths, folder_id):
        super().__init__()
        self.pdf_manager = pdf_manager
        self.pdf_paths = pdf_paths
        self.folder_id = folder_id

    def run(self):
        success = 0
        error = 0

        for i, path in enumerate(self.pdf_paths):
            self.progress.emit(i + 1, len(self.pdf_paths), path.name)

            from src.core.pdf_manager import ImportResult
            result = self.pdf_manager.import_pdf(path, self.folder_id)

            if result.result == ImportResult.SUCCESS:
                success += 1
            else:
                error += 1

        self.finished.emit(success, error)


class ImportDialog(QDialog):
    """导入对话框"""

    def __init__(self, parent=None, app_context=None, pdf_paths: List[Path] = None, folder_id=None):
        super().__init__(parent)
        self.app_context = app_context
        self.pdf_paths = pdf_paths or []
        self.folder_id = folder_id
        self.worker = None

        self.setWindowTitle("导入PDF")
        self.setMinimumSize(600, 400)

        self._setup_ui()

        # 开始导入
        self._start_import()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # 进度信息
        self.status_label = QLabel("准备导入...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 文件列表
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["文件名", "状态", "说明"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # 初始化表格
        self.table.setRowCount(len(self.pdf_paths))
        for i, path in enumerate(self.pdf_paths):
            self.table.setItem(i, 0, QTableWidgetItem(path.name))
            self.table.setItem(i, 1, QTableWidgetItem("等待"))
            self.table.setItem(i, 2, QTableWidgetItem(""))

        # 按钮
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()

        self.close_button = QPushButton("关闭")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.close_button)

        layout.addLayout(self.button_layout)

    def _start_import(self):
        """开始导入"""
        if not self.pdf_paths:
            self.status_label.setText("没有文件需要导入")
            self.close_button.setEnabled(True)
            return

        self.progress_bar.setMaximum(len(self.pdf_paths))
        self.progress_bar.setValue(0)

        self.worker = ImportWorker(
            self.app_context.pdf_manager,
            self.pdf_paths,
            self.folder_id
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current: int, total: int, filename: str):
        """进度更新"""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"正在处理: {filename} ({current}/{total})")
        self.table.setItem(current - 1, 1, QTableWidgetItem("处理中"))

    def _on_finished(self, success: int, error: int):
        """导入完成"""
        self.status_label.setText(f"导入完成: 成功 {success} 个，失败 {error} 个")
        self.close_button.setEnabled(True)

        # 更新表格状态
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 1)
            if item.text() == "处理中":
                item.setText("完成")

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.wait()
        event.accept()
```

- [ ] **Step 4: 提交**

```bash
git add src/ui/dialogs/
git commit -m "feat: 添加对话框组件"
```

---

## Chunk 5: Integration & Application Entry

### Task 17: 应用上下文和主入口

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: 创建主入口文件**

```python
# src/main.py
"""PDF Manager 主入口"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.models.database import Database
from src.services.pdf_service import PDFService
from src.services.ocr_service import OCRService
from src.services.index_service import IndexService
from src.core.folder_manager import FolderManager
from src.core.pdf_manager import PDFManager
from src.core.search_service import SearchService
from src.ui.main_window import MainWindow


class ApplicationContext:
    """应用上下文，管理所有服务"""

    def __init__(self, config_path: Path | None = None):
        # 配置
        self.config = Config(config_path)
        self.config.ensure_directories()

        # 设置日志
        self.logger = setup_logger(
            log_file=self.config.storage_path / "pdf_manager.log"
        )

        # 数据库
        self.database = Database(self.config.database_path)

        # 服务层
        self.pdf_service = PDFService(thumbnail_size=self.config.get("thumbnail_size", 200))
        self.ocr_service = OCRService(
            lang=self.config.get("ocr_language", "ch"),
            use_gpu=False
        )
        self.index_service = IndexService(self.config.index_path)

        # 业务逻辑层
        self.folder_manager = FolderManager(self.database)
        self.pdf_manager = PDFManager(
            database=self.database,
            pdf_service=self.pdf_service,
            ocr_service=self.ocr_service,
            index_service=self.index_service,
            storage_path=self.config.storage_path,
        )
        self.search_service = SearchService(self.database, self.index_service)


def main():
    """主函数"""
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PDF Manager")
    app.setApplicationVersion("0.1.0")

    # 创建应用上下文
    config_path = Path("config.json")
    context = ApplicationContext(config_path)

    # 创建主窗口
    window = MainWindow(context)
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 提交**

```bash
git add src/main.py
git commit -m "feat: 添加应用主入口"
```

---

### Task 18: 最终集成和验证

- [ ] **Step 1: 运行所有测试**

```bash
cd /root/PdfOCR && python -m pytest tests/ -v
```

Expected: 所有测试通过

- [ ] **Step 2: 验证应用启动**

```bash
cd /root/PdfOCR && python -m src.main
```

Expected: 应用窗口正常显示

- [ ] **Step 3: 最终提交**

```bash
git add -A
git commit -m "feat: PDF Manager v0.1.0 完成"
```

---

## 完整实施计划总结

### 已创建模块清单

**数据层 (src/models/)**
- `schemas.py` - 数据结构定义
- `database.py` - SQLite数据库操作

**服务层 (src/services/)**
- `pdf_service.py` - PDF处理服务
- `ocr_service.py` - OCR识别服务
- `index_service.py` - 全文搜索索引服务

**业务逻辑层 (src/core/)**
- `folder_manager.py` - 文件夹管理
- `pdf_manager.py` - PDF管理
- `search_service.py` - 搜索服务

**UI层 (src/ui/)**
- `main_window.py` - 主窗口
- `widgets/folder_tree.py` - 文件夹树组件
- `widgets/pdf_list.py` - PDF列表组件
- `widgets/pdf_viewer.py` - PDF预览组件
- `dialogs/settings_dialog.py` - 设置对话框
- `dialogs/import_dialog.py` - 导入对话框

**工具层 (src/utils/)**
- `config.py` - 配置管理
- `logger.py` - 日志工具

**入口文件**
- `main.py` - 应用主入口

---

## 后续优化建议（P1功能）

1. **断点续传** - 记录OCR处理进度，支持中断后继续
2. **数据导出/导入** - 支持数据备份和迁移
3. **搜索结果定位高亮** - 在预览中高亮显示搜索词
4. **模糊搜索** - 支持拼音搜索和模糊匹配
5. **性能优化** - 大文件分块处理，内存优化