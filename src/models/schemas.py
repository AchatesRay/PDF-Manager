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