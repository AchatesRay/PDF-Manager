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