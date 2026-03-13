"""OCR处理服务测试"""

import os
import sys
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from src.services.ocr_service import OCRService


class TestOCRService:
    """OCR服务测试"""

    def test_init_default(self):
        """测试默认初始化"""
        service = OCRService()
        assert service._lang == "ch"
        assert service._use_gpu is False
        assert service._ocr_engine is None

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        service = OCRService(lang="en", use_gpu=True)
        assert service._lang == "en"
        assert service._use_gpu is True
        assert service._ocr_engine is None

    def test_ocr_property_lazy_loading(self):
        """测试OCR引擎延迟加载"""
        service = OCRService()
        assert service._ocr_engine is None

        # 模拟PaddleOCR模块
        mock_ocr_instance = Mock()
        with patch.dict('sys.modules', {'paddleocr': MagicMock(PaddleOCR=Mock(return_value=mock_ocr_instance))}):
            engine = service.ocr
            assert engine is not None

    def test_ocr_property_cached(self):
        """测试OCR引擎缓存"""
        service = OCRService()
        mock_ocr_instance = Mock()
        with patch.dict('sys.modules', {'paddleocr': MagicMock(PaddleOCR=Mock(return_value=mock_ocr_instance))}):
            engine1 = service.ocr
            engine2 = service.ocr
            assert engine1 is engine2

    def test_ocr_property_import_error(self):
        """测试PaddleOCR导入失败"""
        service = OCRService()
        with patch.dict('sys.modules', {}, clear=False):
            service._ocr_engine = None
            service._available = None
            engine = service.ocr
            assert engine is None
            assert service._available is False

    def test_is_available_when_loaded(self):
        """测试OCR服务可用性 - 成功加载"""
        service = OCRService()
        mock_ocr_instance = Mock()
        with patch.dict('sys.modules', {'paddleocr': MagicMock(PaddleOCR=Mock(return_value=mock_ocr_instance))}):
            assert service.is_available() is True

    def test_is_available_when_failed(self):
        """测试OCR服务可用性 - 加载失败"""
        service = OCRService()
        with patch.dict('sys.modules', {}, clear=False):
            service._ocr_engine = None
            service._available = None
            assert service.is_available() is False

    def test_recognize_image_none_input(self):
        """测试识别None图像"""
        service = OCRService()
        result = service.recognize_image(None)
        assert result == ""

    def test_recognize_image_success(self):
        """测试识别图像成功"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Hello World", 0.95)],
                [[[0, 30], [100, 30], [100, 50], [0, 50]], ("Test Text", 0.90)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        mock_image = Image.new('RGB', (100, 100), color='white')
        result = service.recognize_image(mock_image)

        assert "Hello World" in result
        assert "Test Text" in result

    def test_recognize_image_empty_result(self):
        """测试识别图像 - 空结果"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = None
        service._ocr_engine = mock_engine
        service._available = True

        mock_image = Image.new('RGB', (100, 100), color='white')
        result = service.recognize_image(mock_image)

        assert result == ""

    def test_recognize_image_no_ocr_engine(self):
        """测试识别图像 - OCR引擎不可用"""
        service = OCRService()
        service._ocr_engine = None
        service._available = False

        mock_image = Image.new('RGB', (100, 100), color='white')
        result = service.recognize_image(mock_image)

        assert result == ""

    def test_recognize_image_exception(self):
        """测试识别图像 - 异常处理"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.side_effect = Exception("OCR Error")
        service._ocr_engine = mock_engine
        service._available = True

        mock_image = Image.new('RGB', (100, 100), color='white')
        result = service.recognize_image(mock_image)

        assert result == ""

    def test_recognize_image_file_not_exists(self):
        """测试识别不存在的图像文件"""
        service = OCRService()
        result = service.recognize_image_file("/nonexistent/path.png")
        assert result == ""

    def test_recognize_image_file_directory(self):
        """测试识别目录路径"""
        service = OCRService()
        temp_dir = tempfile.mkdtemp()
        try:
            result = service.recognize_image_file(temp_dir)
            assert result == ""
        finally:
            os.rmdir(temp_dir)

    def test_recognize_image_file_success(self):
        """测试识别图像文件成功"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("File Text", 0.95)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, "test.png")

        try:
            image = Image.new('RGB', (100, 100), color='white')
            image.save(image_path)

            result = service.recognize_image_file(image_path)
            assert "File Text" in result

        finally:
            if os.path.exists(image_path):
                os.remove(image_path)
            os.rmdir(temp_dir)

    def test_recognize_image_file_grayscale(self):
        """测试识别灰度图像文件"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Gray Text", 0.95)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, "test_gray.png")

        try:
            image = Image.new('L', (100, 100), color='white')
            image.save(image_path)

            result = service.recognize_image_file(image_path)
            assert "Gray Text" in result

        finally:
            if os.path.exists(image_path):
                os.remove(image_path)
            os.rmdir(temp_dir)

    def test_recognize_pdf_page_no_service(self):
        """测试识别PDF页面 - 无PDF服务"""
        service = OCRService()
        result = service.recognize_pdf_page(None, "/path/to/pdf", 0)
        assert result == ""

    def test_recognize_pdf_page_render_failed(self):
        """测试识别PDF页面 - 渲染失败"""
        service = OCRService()
        mock_pdf_service = Mock()
        mock_pdf_service.render_page_to_image.return_value = None

        result = service.recognize_pdf_page(mock_pdf_service, "/path/to/pdf", 0)

        assert result == ""
        mock_pdf_service.render_page_to_image.assert_called_once_with(
            "/path/to/pdf", 0, dpi=200
        )

    def test_recognize_pdf_page_success(self):
        """测试识别PDF页面成功"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("PDF Text", 0.95)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        mock_image = Image.new('RGB', (100, 100), color='white')
        mock_pdf_service = Mock()
        mock_pdf_service.render_page_to_image.return_value = mock_image

        result = service.recognize_pdf_page(
            mock_pdf_service, "/path/to/pdf", 0
        )

        assert "PDF Text" in result

    def test_recognize_pdf_page_custom_dpi(self):
        """测试识别PDF页面 - 自定义DPI"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("High DPI Text", 0.95)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        mock_image = Image.new('RGB', (100, 100), color='white')
        mock_pdf_service = Mock()
        mock_pdf_service.render_page_to_image.return_value = mock_image

        result = service.recognize_pdf_page(
            mock_pdf_service, "/path/to/pdf", 0, dpi=300
        )

        assert "High DPI Text" in result
        mock_pdf_service.render_page_to_image.assert_called_once_with(
            "/path/to/pdf", 0, dpi=300
        )

    def test_recognize_pdf_page_with_real_pdf_service(self):
        """测试识别PDF页面 - 使用真实PDF服务（但渲染返回None）"""
        from src.services.pdf_service import PDFService

        service = OCRService()
        pdf_service = PDFService()

        result = service.recognize_pdf_page(pdf_service, "/nonexistent/path.pdf", 0)

        assert result == ""


class TestOCRServiceIntegration:
    """OCR服务集成测试"""

    def test_full_ocr_workflow_with_mock(self):
        """测试完整OCR工作流程（使用mock）"""
        service = OCRService(lang="ch", use_gpu=False)
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[10, 10], [190, 10], [190, 40], [10, 40]], ("OCR Service Test", 0.98)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        test_image = Image.new('RGB', (200, 100), color='white')
        result = service.recognize_image(test_image)

        assert "OCR Service Test" in result

    def test_multiple_recognitions_same_engine(self):
        """测试多次识别使用同一个引擎"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.side_effect = [
            [[[[[0, 0], [50, 0], [50, 20], [0, 20]], ("First", 0.95)]]],
            [[[[[0, 0], [50, 0], [50, 20], [0, 20]], ("Second", 0.95)]]],
        ]
        service._ocr_engine = mock_engine
        service._available = True

        image1 = Image.new('RGB', (50, 20), color='white')
        result1 = service.recognize_image(image1)

        image2 = Image.new('RGB', (50, 20), color='white')
        result2 = service.recognize_image(image2)

        assert "First" in result1
        assert "Second" in result2

    def test_multiline_ocr_result(self):
        """测试多行OCR结果"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Line 1", 0.95)],
                [[[0, 30], [100, 30], [100, 50], [0, 50]], ("Line 2", 0.90)],
                [[[0, 60], [100, 60], [100, 80], [0, 80]], ("Line 3", 0.88)]
            ]
        ]
        service._ocr_engine = mock_engine
        service._available = True

        test_image = Image.new('RGB', (200, 200), color='white')
        result = service.recognize_image(test_image)

        lines = result.split('\n')
        assert len(lines) == 3
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_ocr_result_with_empty_lines(self):
        """测试OCR结果包含空行"""
        service = OCRService()
        mock_engine = Mock()
        mock_engine.ocr.return_value = [
            [
                [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Text 1", 0.95)],
            ],
            None,
        ]
        service._ocr_engine = mock_engine
        service._available = True

        test_image = Image.new('RGB', (200, 200), color='white')
        result = service.recognize_image(test_image)

        assert "Text 1" in result

    def test_different_languages(self):
        """测试不同语言配置"""
        # 测试中文
        service_ch = OCRService(lang="ch", use_gpu=False)
        mock_engine_ch = Mock()
        mock_engine_ch.ocr.return_value = [
            [[[[0, 0], [100, 0], [100, 20], [0, 20]], ("中文测试", 0.95)]]
        ]
        service_ch._ocr_engine = mock_engine_ch
        service_ch._available = True

        result = service_ch.recognize_image(Image.new('RGB', (100, 20)))
        assert "中文测试" in result

        # 测试英文
        service_en = OCRService(lang="en", use_gpu=True)
        mock_engine_en = Mock()
        mock_engine_en.ocr.return_value = [
            [[[[0, 0], [100, 0], [100, 20], [0, 20]], ("English", 0.95)]]
        ]
        service_en._ocr_engine = mock_engine_en
        service_en._available = True

        result = service_en.recognize_image(Image.new('RGB', (100, 20)))
        assert "English" in result