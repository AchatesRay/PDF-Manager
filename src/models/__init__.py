"""数据模型模块"""
from .schemas import Folder, PDF, PDFPage

# Database 将在 Task 5 中实现
try:
    from .database import Database
except ImportError:
    Database = None  # type: ignore

__all__ = ["Folder", "PDF", "PDFPage", "Database"]