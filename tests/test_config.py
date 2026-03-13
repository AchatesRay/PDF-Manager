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