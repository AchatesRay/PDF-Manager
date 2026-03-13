"""工具模块"""
from .config import Config

# logger模块在Task 3中创建，这里使用延迟导入
try:
    from .logger import setup_logger
except ImportError:
    setup_logger = None  # type: ignore

__all__ = ["Config", "setup_logger"]