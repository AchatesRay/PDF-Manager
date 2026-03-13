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