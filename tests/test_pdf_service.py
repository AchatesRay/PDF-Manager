"""PDF处理服务测试"""

import os
import tempfile
import pytest
from pathlib import Path

from src.services.pdf_service import PDFService
from src.models.schemas import PDFType


class TestPDFService:
    """PDF服务测试"""

    @pytest.fixture
    def pdf_service(self):
        """创建PDF服务实例"""
        return PDFService(thumbnail_size=200)

    @pytest.fixture
    def sample_pdf_path(self):
        """获取测试PDF文件路径"""
        # 查找测试PDF文件
        test_dir = Path(__file__).parent / "fixtures"
        pdf_path = test_dir / "sample.pdf"

        if pdf_path.exists():
            return str(pdf_path)

        # 如果没有测试文件，创建一个简单的PDF
        return self._create_test_pdf()

    def _create_test_pdf(self):
        """创建测试PDF文件"""
        import fitz

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test_sample.pdf")

        # 创建一个简单的PDF
        doc = fitz.open()
        page = doc.new_page()

        # 添加一些文字
        text_insert = page.insert_text(
            (72, 72),
            "This is a test PDF document.",
            fontsize=12
        )

        doc.save(pdf_path)
        doc.close()

        return pdf_path

    @pytest.fixture
    def text_pdf_path(self):
        """创建文字型PDF"""
        import fitz

        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "text_pdf.pdf")

        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            # 添加足够多的文字
            text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
            page.insert_text((72, 72), text, fontsize=10)
        doc.save(pdf_path)
        doc.close()

        return pdf_path

    @pytest.fixture
    def empty_pdf_path(self):
        """创建空白PDF（扫描型）"""
        import fitz

        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "empty_pdf.pdf")

        doc = fitz.open()
        # 创建空白页面（无文字）
        doc.new_page()
        doc.new_page()
        doc.new_page()
        doc.save(pdf_path)
        doc.close()

        return pdf_path

    @pytest.fixture
    def mixed_pdf_path(self):
        """创建混合型PDF"""
        import fitz

        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "mixed_pdf.pdf")

        doc = fitz.open()
        # 第一页有文字
        page1 = doc.new_page()
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
        page1.insert_text((72, 72), text, fontsize=10)
        # 第二页空白
        doc.new_page()
        doc.save(pdf_path)
        doc.close()

        return pdf_path

    def test_init_default(self):
        """测试默认初始化"""
        service = PDFService()
        assert service.thumbnail_size == 200

    def test_init_custom_size(self):
        """测试自定义缩略图尺寸"""
        service = PDFService(thumbnail_size=300)
        assert service.thumbnail_size == 300

    def test_validate_pdf_valid(self, pdf_service, text_pdf_path):
        """测试验证有效PDF"""
        assert pdf_service.validate_pdf(text_pdf_path) is True

    def test_validate_pdf_invalid_path(self, pdf_service):
        """测试验证不存在的路径"""
        assert pdf_service.validate_pdf("/nonexistent/path.pdf") is False

    def test_validate_pdf_non_file(self, pdf_service):
        """测试验证非文件路径"""
        temp_dir = tempfile.mkdtemp()
        assert pdf_service.validate_pdf(temp_dir) is False
        os.rmdir(temp_dir)

    def test_get_page_count(self, pdf_service, text_pdf_path):
        """测试获取页数"""
        count = pdf_service.get_page_count(text_pdf_path)
        assert count == 3

    def test_get_page_count_invalid(self, pdf_service):
        """测试获取无效文件的页数"""
        count = pdf_service.get_page_count("/nonexistent/path.pdf")
        assert count == 0

    def test_get_file_size(self, pdf_service, text_pdf_path):
        """测试获取文件大小"""
        size = pdf_service.get_file_size(text_pdf_path)
        assert size > 0

    def test_get_file_size_invalid(self, pdf_service):
        """测试获取无效文件大小"""
        size = pdf_service.get_file_size("/nonexistent/path.pdf")
        assert size == 0

    def test_detect_pdf_type_text(self, pdf_service, text_pdf_path):
        """测试检测文字型PDF"""
        pdf_type = pdf_service.detect_pdf_type(text_pdf_path)
        assert pdf_type == PDFType.TEXT

    def test_detect_pdf_type_scanned(self, pdf_service, empty_pdf_path):
        """测试检测扫描型PDF"""
        pdf_type = pdf_service.detect_pdf_type(empty_pdf_path)
        assert pdf_type == PDFType.SCANNED

    def test_detect_pdf_type_mixed(self, pdf_service, mixed_pdf_path):
        """测试检测混合型PDF"""
        pdf_type = pdf_service.detect_pdf_type(mixed_pdf_path)
        assert pdf_type == PDFType.MIXED

    def test_detect_pdf_type_invalid(self, pdf_service):
        """测试检测无效文件类型"""
        pdf_type = pdf_service.detect_pdf_type("/nonexistent/path.pdf")
        assert pdf_type == PDFType.SCANNED

    def test_extract_text_from_page(self, pdf_service, text_pdf_path):
        """测试从页面提取文本"""
        text = pdf_service.extract_text_from_page(text_pdf_path, 0)
        assert len(text) > 0
        assert "Lorem ipsum" in text

    def test_extract_text_from_invalid_page(self, pdf_service, text_pdf_path):
        """测试从无效页码提取文本"""
        # 负数页码
        text = pdf_service.extract_text_from_page(text_pdf_path, -1)
        assert text == ""

        # 超出范围页码
        text = pdf_service.extract_text_from_page(text_pdf_path, 100)
        assert text == ""

    def test_extract_all_text(self, pdf_service, text_pdf_path):
        """测试提取所有文本"""
        text = pdf_service.extract_all_text(text_pdf_path)
        assert len(text) > 0
        assert "Lorem ipsum" in text

    def test_extract_all_text_invalid(self, pdf_service):
        """测试从无效文件提取文本"""
        text = pdf_service.extract_all_text("/nonexistent/path.pdf")
        assert text == ""

    def test_render_page_to_image(self, pdf_service, text_pdf_path):
        """测试渲染页面为图像"""
        from PIL import Image

        img = pdf_service.render_page_to_image(text_pdf_path, 0, dpi=150)
        assert img is not None
        assert isinstance(img, Image.Image)
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_render_page_to_image_invalid_page(self, pdf_service, text_pdf_path):
        """测试渲染无效页码"""
        img = pdf_service.render_page_to_image(text_pdf_path, 100)
        assert img is None

    def test_render_page_to_image_invalid_file(self, pdf_service):
        """测试渲染无效文件"""
        img = pdf_service.render_page_to_image("/nonexistent/path.pdf", 0)
        assert img is None

    def test_generate_thumbnail(self, pdf_service, text_pdf_path):
        """测试生成缩略图"""
        from PIL import Image

        thumbnail = pdf_service.generate_thumbnail(text_pdf_path, 0)
        assert thumbnail is not None
        assert isinstance(thumbnail, Image.Image)
        # 缩略图尺寸应该不超过设定值
        max_dim = max(thumbnail.size)
        assert max_dim <= pdf_service.thumbnail_size

    def test_generate_thumbnail_invalid(self, pdf_service):
        """测试生成无效文件的缩略图"""
        thumbnail = pdf_service.generate_thumbnail("/nonexistent/path.pdf", 0)
        assert thumbnail is None

    def test_save_thumbnail_png(self, pdf_service, text_pdf_path):
        """测试保存PNG缩略图"""
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "thumbnail.png")

        result = pdf_service.save_thumbnail(text_pdf_path, 0, output_path)
        assert result is True
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

        # 清理
        os.remove(output_path)
        os.rmdir(temp_dir)

    def test_save_thumbnail_jpg(self, pdf_service, text_pdf_path):
        """测试保存JPG缩略图"""
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "thumbnail.jpg")

        result = pdf_service.save_thumbnail(text_pdf_path, 0, output_path)
        assert result is True
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

        # 清理
        os.remove(output_path)
        os.rmdir(temp_dir)

    def test_save_thumbnail_creates_directory(self, pdf_service, text_pdf_path):
        """测试保存缩略图时创建目录"""
        temp_dir = tempfile.mkdtemp()
        nested_dir = os.path.join(temp_dir, "nested", "dir")
        output_path = os.path.join(nested_dir, "thumbnail.png")

        result = pdf_service.save_thumbnail(text_pdf_path, 0, output_path)
        assert result is True
        assert os.path.exists(output_path)

        # 清理
        os.remove(output_path)
        os.rmdir(nested_dir)
        os.rmdir(os.path.dirname(nested_dir))
        os.rmdir(temp_dir)

    def test_save_thumbnail_invalid_pdf(self, pdf_service):
        """测试保存无效PDF的缩略图"""
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "thumbnail.png")

        result = pdf_service.save_thumbnail("/nonexistent/path.pdf", 0, output_path)
        assert result is False

        os.rmdir(temp_dir)


class TestPDFServiceIntegration:
    """PDF服务集成测试"""

    @pytest.fixture
    def pdf_service(self):
        """创建PDF服务实例"""
        return PDFService(thumbnail_size=150)

    def test_full_workflow(self, pdf_service):
        """测试完整工作流程"""
        import fitz
        from PIL import Image

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "workflow_test.pdf")

        # 创建测试PDF
        doc = fitz.open()
        for i in range(5):
            page = doc.new_page()
            text = f"Page {i + 1}: " + "Test content " * 20
            page.insert_text((72, 72), text, fontsize=10)
        doc.save(pdf_path)
        doc.close()

        try:
            # 验证PDF
            assert pdf_service.validate_pdf(pdf_path) is True

            # 获取页数
            page_count = pdf_service.get_page_count(pdf_path)
            assert page_count == 5

            # 获取文件大小
            file_size = pdf_service.get_file_size(pdf_path)
            assert file_size > 0

            # 检测类型
            pdf_type = pdf_service.detect_pdf_type(pdf_path)
            assert pdf_type == PDFType.TEXT

            # 提取文本
            text = pdf_service.extract_all_text(pdf_path)
            assert len(text) > 0
            assert "Page 1" in text

            # 渲染页面
            img = pdf_service.render_page_to_image(pdf_path, 0, dpi=100)
            assert img is not None
            assert isinstance(img, Image.Image)

            # 生成并保存缩略图
            thumbnail_path = os.path.join(temp_dir, "thumb.png")
            result = pdf_service.save_thumbnail(pdf_path, 0, thumbnail_path)
            assert result is True
            assert os.path.exists(thumbnail_path)

        finally:
            # 清理
            import shutil
            shutil.rmtree(temp_dir)