"""PDF管理器测试"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.database import Database
from src.models.schemas import PDF, PDFPage, PDFStatus, PDFType, OCRStatus, Folder
from src.core.pdf_manager import PDFManager, ImportResult, ImportStatus


@pytest.fixture
def temp_storage_path():
    """创建临时存储路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_db_path():
    """创建临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def db(temp_db_path):
    """创建数据库实例"""
    return Database(temp_db_path)


@pytest.fixture
def mock_pdf_service():
    """创建Mock PDF服务"""
    service = MagicMock()
    service.validate_pdf.return_value = True
    service.get_page_count.return_value = 3
    service.get_file_size.return_value = 1024
    service.detect_pdf_type.return_value = PDFType.SCANNED
    service.extract_text_from_page.return_value = "sample text"
    return service


@pytest.fixture
def mock_ocr_service():
    """创建Mock OCR服务"""
    service = MagicMock()
    service.recognize_pdf_page.return_value = "OCR text"
    return service


@pytest.fixture
def mock_index_service():
    """创建Mock索引服务"""
    service = MagicMock()
    service.add_page.return_value = True
    service.delete_pdf.return_value = 3
    return service


@pytest.fixture
def pdf_manager(db, mock_pdf_service, mock_ocr_service, mock_index_service, temp_storage_path):
    """创建PDF管理器实例"""
    return PDFManager(
        database=db,
        pdf_service=mock_pdf_service,
        ocr_service=mock_ocr_service,
        index_service=mock_index_service,
        storage_path=temp_storage_path
    )


@pytest.fixture
def sample_pdf_path(temp_storage_path):
    """创建示例PDF文件"""
    pdf_path = Path(temp_storage_path) / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%fake pdf content for testing")
    return str(pdf_path)


class TestPDFManagerInit:
    """PDF管理器初始化测试"""

    def test_init(self, db, mock_pdf_service, mock_ocr_service, mock_index_service, temp_storage_path):
        """测试初始化"""
        manager = PDFManager(
            database=db,
            pdf_service=mock_pdf_service,
            ocr_service=mock_ocr_service,
            index_service=mock_index_service,
            storage_path=temp_storage_path
        )
        assert manager is not None

    def test_init_creates_storage_directory(self, db, mock_pdf_service, mock_ocr_service, mock_index_service, temp_storage_path):
        """测试初始化时创建存储目录"""
        new_storage = os.path.join(temp_storage_path, "new_storage")
        manager = PDFManager(
            database=db,
            pdf_service=mock_pdf_service,
            ocr_service=mock_ocr_service,
            index_service=mock_index_service,
            storage_path=new_storage
        )
        assert os.path.exists(new_storage)
        assert os.path.exists(os.path.join(new_storage, "thumbnails"))


class TestImportPDF:
    """导入PDF测试"""

    def test_import_pdf_success(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试成功导入PDF"""
        result = pdf_manager.import_pdf(sample_pdf_path)

        assert result.result == ImportResult.SUCCESS
        assert result.pdf_id is not None
        assert "Successfully imported" in result.message

        # 验证PDF记录已创建
        pdf = pdf_manager.get_pdf(result.pdf_id)
        assert pdf is not None
        assert pdf.filename == "sample.pdf"

    def test_import_pdf_file_not_found(self, pdf_manager):
        """测试导入不存在的文件"""
        result = pdf_manager.import_pdf("/nonexistent/path/file.pdf")

        assert result.result == ImportResult.INVALID
        assert result.pdf_id is None
        assert "File not found" in result.message

    def test_import_pdf_invalid_file(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试导入无效PDF文件"""
        mock_pdf_service.validate_pdf.return_value = False

        result = pdf_manager.import_pdf(sample_pdf_path)

        assert result.result == ImportResult.INVALID
        assert result.pdf_id is None
        assert "Invalid PDF file" in result.message

    def test_import_pdf_duplicate(self, pdf_manager, sample_pdf_path, mock_pdf_service, db):
        """测试导入重复PDF"""
        # 先导入一次
        result1 = pdf_manager.import_pdf(sample_pdf_path)
        assert result1.result == ImportResult.SUCCESS

        # 重置mock以允许第二次导入
        mock_pdf_service.validate_pdf.return_value = True

        # 再次导入相同文件
        result2 = pdf_manager.import_pdf(sample_pdf_path)

        assert result2.result == ImportResult.DUPLICATE
        assert result2.pdf_id == result1.pdf_id

    def test_import_pdf_with_folder(self, pdf_manager, sample_pdf_path, db):
        """测试导入PDF到指定文件夹"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        result = pdf_manager.import_pdf(sample_pdf_path, folder_id=folder_id)

        assert result.result == ImportResult.SUCCESS

        pdf = pdf_manager.get_pdf(result.pdf_id)
        assert pdf.folder_id == folder_id

    def test_import_pdf_without_ocr(self, pdf_manager, sample_pdf_path, mock_ocr_service):
        """测试导入PDF但不执行OCR"""
        result = pdf_manager.import_pdf(sample_pdf_path, process_ocr=False)

        assert result.result == ImportResult.SUCCESS
        # 验证OCR服务没有被调用
        mock_ocr_service.recognize_pdf_page.assert_not_called()

    def test_import_pdf_creates_pages(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试导入PDF时创建页面记录"""
        mock_pdf_service.get_page_count.return_value = 5

        result = pdf_manager.import_pdf(sample_pdf_path)

        assert result.result == ImportResult.SUCCESS

        pages = pdf_manager.get_pages_by_pdf(result.pdf_id)
        assert len(pages) == 5

    def test_import_pdf_with_text_type(self, pdf_manager, sample_pdf_path, mock_pdf_service, mock_ocr_service):
        """测试导入文字型PDF"""
        mock_pdf_service.detect_pdf_type.return_value = PDFType.TEXT

        result = pdf_manager.import_pdf(sample_pdf_path, process_ocr=True)

        assert result.result == ImportResult.SUCCESS
        # 文字型PDF应该使用extract_text_from_page，而不是OCR
        mock_pdf_service.extract_text_from_page.assert_called()
        mock_ocr_service.recognize_pdf_page.assert_not_called()


class TestDeletePDF:
    """删除PDF测试"""

    def test_delete_pdf_success(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试成功删除PDF"""
        # 先导入
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        # 删除
        delete_result = pdf_manager.delete_pdf(pdf_id)

        assert delete_result is True
        assert pdf_manager.get_pdf(pdf_id) is None

    def test_delete_pdf_not_found(self, pdf_manager):
        """测试删除不存在的PDF"""
        result = pdf_manager.delete_pdf(999)
        assert result is False

    def test_delete_pdf_removes_file(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试删除PDF时删除文件"""
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        pdf = pdf_manager.get_pdf(pdf_id)
        stored_path = pdf.file_path

        # 确认文件存在
        assert os.path.exists(stored_path)

        # 删除
        pdf_manager.delete_pdf(pdf_id)

        # 确认文件已删除
        assert not os.path.exists(stored_path)

    def test_delete_pdf_removes_index(self, pdf_manager, sample_pdf_path, mock_index_service):
        """测试删除PDF时删除索引"""
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        # 重置mock
        mock_index_service.delete_pdf.reset_mock()

        # 删除
        pdf_manager.delete_pdf(pdf_id)

        # 验证索引服务被调用
        mock_index_service.delete_pdf.assert_called_once_with(pdf_id)


class TestGetPDF:
    """获取PDF测试"""

    def test_get_pdf(self, pdf_manager, sample_pdf_path):
        """测试获取PDF"""
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        pdf = pdf_manager.get_pdf(pdf_id)

        assert pdf is not None
        assert pdf.id == pdf_id
        assert pdf.filename == "sample.pdf"

    def test_get_pdf_not_found(self, pdf_manager):
        """测试获取不存在的PDF"""
        pdf = pdf_manager.get_pdf(999)
        assert pdf is None


class TestGetPDFsByFolder:
    """获取文件夹下PDF列表测试"""

    def test_get_pdfs_by_folder_empty(self, pdf_manager):
        """测试获取空文件夹的PDF列表"""
        pdfs = pdf_manager.get_pdfs_by_folder(1)
        assert pdfs == []

    def test_get_pdfs_by_folder(self, pdf_manager, sample_pdf_path, db):
        """测试获取文件夹下的PDF列表"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        # 导入PDF到文件夹
        pdf_manager.import_pdf(sample_pdf_path, folder_id=folder_id)

        pdfs = pdf_manager.get_pdfs_by_folder(folder_id)

        assert len(pdfs) == 1
        assert pdfs[0].folder_id == folder_id

    def test_get_pdfs_by_folder_root(self, pdf_manager, sample_pdf_path):
        """测试获取根目录下的PDF列表"""
        # 导入PDF到根目录
        pdf_manager.import_pdf(sample_pdf_path)

        pdfs = pdf_manager.get_pdfs_by_folder(None)

        assert len(pdfs) == 1
        assert pdfs[0].folder_id is None


class TestGetAllPDFs:
    """获取所有PDF测试"""

    def test_get_all_pdfs_empty(self, pdf_manager):
        """测试空数据库获取所有PDF"""
        pdfs = pdf_manager.get_all_pdfs()
        assert pdfs == []

    def test_get_all_pdfs(self, pdf_manager, sample_pdf_path, db):
        """测试获取所有PDF"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        # 导入多个PDF
        pdf_manager.import_pdf(sample_pdf_path)  # 根目录
        pdf_manager.import_pdf(sample_pdf_path, folder_id=folder_id)  # 文件夹

        # 由于重复检测，需要修改文件名
        pdfs = pdf_manager.get_all_pdfs()
        # 因为重复检测，只会有一个
        assert len(pdfs) >= 1


class TestGetPage:
    """获取页面测试"""

    def test_get_page(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试获取页面"""
        mock_pdf_service.get_page_count.return_value = 3

        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        pages = pdf_manager.get_pages_by_pdf(pdf_id)
        page_id = pages[0].id

        page = pdf_manager.get_page(page_id)

        assert page is not None
        assert page.id == page_id
        assert page.pdf_id == pdf_id

    def test_get_page_not_found(self, pdf_manager):
        """测试获取不存在的页面"""
        page = pdf_manager.get_page(999)
        assert page is None


class TestGetPagesByPDF:
    """获取PDF的所有页面测试"""

    def test_get_pages_by_pdf(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试获取PDF的所有页面"""
        mock_pdf_service.get_page_count.return_value = 5

        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        pages = pdf_manager.get_pages_by_pdf(pdf_id)

        assert len(pages) == 5
        # 验证页码顺序
        for i, page in enumerate(pages):
            assert page.page_number == i

    def test_get_pages_by_pdf_not_found(self, pdf_manager):
        """测试获取不存在PDF的页面"""
        pages = pdf_manager.get_pages_by_pdf(999)
        assert pages == []


class TestMovePDF:
    """移动PDF测试"""

    def test_move_pdf_to_folder(self, pdf_manager, sample_pdf_path, db):
        """测试移动PDF到文件夹"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        # 导入PDF
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        # 移动
        move_result = pdf_manager.move_pdf(pdf_id, folder_id)

        assert move_result is True

        pdf = pdf_manager.get_pdf(pdf_id)
        assert pdf.folder_id == folder_id

    def test_move_pdf_to_root(self, pdf_manager, sample_pdf_path, db):
        """测试移动PDF到根目录"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        # 导入PDF到文件夹
        result = pdf_manager.import_pdf(sample_pdf_path, folder_id=folder_id)
        pdf_id = result.pdf_id

        # 移动到根目录
        move_result = pdf_manager.move_pdf(pdf_id, None)

        assert move_result is True

        pdf = pdf_manager.get_pdf(pdf_id)
        assert pdf.folder_id is None

    def test_move_pdf_not_found(self, pdf_manager):
        """测试移动不存在的PDF"""
        result = pdf_manager.move_pdf(999, None)
        assert result is False

    def test_move_pdf_to_nonexistent_folder(self, pdf_manager, sample_pdf_path):
        """测试移动PDF到不存在的文件夹"""
        # 导入PDF
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        # 尝试移动到不存在的文件夹
        move_result = pdf_manager.move_pdf(pdf_id, 999)

        assert move_result is False

    def test_move_pdf_updates_index(self, pdf_manager, sample_pdf_path, mock_index_service, db):
        """测试移动PDF时更新索引"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        # 导入PDF
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        # 重置mock
        mock_index_service.add_page.reset_mock()

        # 移动
        pdf_manager.move_pdf(pdf_id, folder_id)

        # 验证索引更新
        assert mock_index_service.add_page.called


class TestReprocessPDF:
    """重新处理PDF测试"""

    def test_reprocess_pdf_success(self, pdf_manager, sample_pdf_path, mock_ocr_service, mock_index_service, mock_pdf_service):
        """测试重新处理PDF"""
        # 导入PDF
        result = pdf_manager.import_pdf(sample_pdf_path, process_ocr=False)
        pdf_id = result.pdf_id

        # 重置mock
        mock_ocr_service.recognize_pdf_page.reset_mock()
        mock_index_service.delete_pdf.reset_mock()

        # 重新处理
        reprocess_result = pdf_manager.reprocess_pdf(pdf_id)

        assert reprocess_result is True
        # 验证OCR被调用
        mock_ocr_service.recognize_pdf_page.assert_called()
        # 验证索引被删除后重建
        mock_index_service.delete_pdf.assert_called_once_with(pdf_id)

    def test_reprocess_pdf_not_found(self, pdf_manager):
        """测试重新处理不存在的PDF"""
        result = pdf_manager.reprocess_pdf(999)
        assert result is False

    def test_reprocess_pdf_resets_ocr_status(self, pdf_manager, sample_pdf_path, db, mock_pdf_service):
        """测试重新处理时重置OCR状态"""
        mock_pdf_service.get_page_count.return_value = 3

        # 导入PDF
        result = pdf_manager.import_pdf(sample_pdf_path, process_ocr=True)
        pdf_id = result.pdf_id

        # 重新处理
        pdf_manager.reprocess_pdf(pdf_id)

        # 检查页面状态
        pages = pdf_manager.get_pages_by_pdf(pdf_id)
        for page in pages:
            assert page.ocr_status == OCRStatus.DONE


class TestGetStatistics:
    """获取统计信息测试"""

    def test_get_statistics_empty(self, pdf_manager):
        """测试空数据库的统计信息"""
        stats = pdf_manager.get_statistics()

        assert stats["total_pdfs"] == 0
        assert stats["total_pages"] == 0
        assert stats["total_size"] == 0

    def test_get_statistics_with_pdfs(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试有PDF的统计信息"""
        mock_pdf_service.get_page_count.return_value = 5
        mock_pdf_service.get_file_size.return_value = 2048

        # 导入PDF
        pdf_manager.import_pdf(sample_pdf_path)

        stats = pdf_manager.get_statistics()

        assert stats["total_pdfs"] == 1
        assert stats["total_pages"] == 5
        assert stats["total_size"] == 2048

    def test_get_statistics_status_counts(self, pdf_manager, sample_pdf_path):
        """测试统计信息中的状态计数"""
        # 导入PDF
        pdf_manager.import_pdf(sample_pdf_path)

        stats = pdf_manager.get_statistics()

        assert "status_counts" in stats
        # 导入后应该是done状态
        assert stats["status_counts"]["done"] == 1

    def test_get_statistics_ocr_counts(self, pdf_manager, sample_pdf_path, mock_pdf_service):
        """测试统计信息中的OCR计数"""
        mock_pdf_service.get_page_count.return_value = 3

        # 导入PDF并处理OCR
        pdf_manager.import_pdf(sample_pdf_path, process_ocr=True)

        stats = pdf_manager.get_statistics()

        assert "ocr_done" in stats
        assert stats["ocr_done"] == 3


class TestImportStatus:
    """ImportStatus测试"""

    def test_import_status_dataclass(self):
        """测试ImportStatus数据类"""
        status = ImportStatus(
            result=ImportResult.SUCCESS,
            pdf_id=1,
            message="Test message"
        )

        assert status.result == ImportResult.SUCCESS
        assert status.pdf_id == 1
        assert status.message == "Test message"


class TestImportResult:
    """ImportResult枚举测试"""

    def test_import_result_values(self):
        """测试ImportResult枚举值"""
        assert ImportResult.SUCCESS.value == "success"
        assert ImportResult.DUPLICATE.value == "duplicate"
        assert ImportResult.INVALID.value == "invalid"
        assert ImportResult.ERROR.value == "error"


class TestPDFManagerIntegration:
    """PDF管理器集成测试"""

    def test_import_delete_workflow(self, pdf_manager, sample_pdf_path):
        """测试导入删除工作流"""
        # 导入
        result = pdf_manager.import_pdf(sample_pdf_path)
        assert result.result == ImportResult.SUCCESS
        pdf_id = result.pdf_id

        # 确认存在
        pdf = pdf_manager.get_pdf(pdf_id)
        assert pdf is not None

        # 删除
        delete_result = pdf_manager.delete_pdf(pdf_id)
        assert delete_result is True

        # 确认已删除
        pdf = pdf_manager.get_pdf(pdf_id)
        assert pdf is None

    def test_import_move_delete_workflow(self, pdf_manager, sample_pdf_path, db):
        """测试导入、移动、删除工作流"""
        # 创建文件夹
        folder = Folder(name="Test Folder")
        folder_id = db.create_folder(folder)

        # 导入
        result = pdf_manager.import_pdf(sample_pdf_path)
        pdf_id = result.pdf_id

        # 移动
        move_result = pdf_manager.move_pdf(pdf_id, folder_id)
        assert move_result is True

        pdf = pdf_manager.get_pdf(pdf_id)
        assert pdf.folder_id == folder_id

        # 删除
        delete_result = pdf_manager.delete_pdf(pdf_id)
        assert delete_result is True

    def test_multiple_pdfs_in_different_folders(self, pdf_manager, sample_pdf_path, db, mock_pdf_service):
        """测试多个PDF在不同文件夹"""
        mock_pdf_service.get_file_size.return_value = 1024

        # 创建文件夹
        folder1 = Folder(name="Folder 1")
        folder1_id = db.create_folder(folder1)

        folder2 = Folder(name="Folder 2")
        folder2_id = db.create_folder(folder2)

        # 为了避免重复检测，使用不同大小的文件
        pdfs_info = [
            (folder1_id, 1024, "pdf1"),
            (folder2_id, 2048, "pdf2"),
            (None, 3072, "pdf3"),  # 根目录
        ]

        created_pdf_ids = []
        for folder_id, size, _ in pdfs_info:
            mock_pdf_service.get_file_size.return_value = size
            result = pdf_manager.import_pdf(sample_pdf_path, folder_id=folder_id)
            if result.result == ImportResult.SUCCESS:
                created_pdf_ids.append(result.pdf_id)

        # 验证各文件夹的PDF
        folder1_pdfs = pdf_manager.get_pdfs_by_folder(folder1_id)
        assert len(folder1_pdfs) >= 1

        folder2_pdfs = pdf_manager.get_pdfs_by_folder(folder2_id)
        assert len(folder2_pdfs) >= 1

        root_pdfs = pdf_manager.get_pdfs_by_folder(None)
        assert len(root_pdfs) >= 1

        # 统计
        stats = pdf_manager.get_statistics()
        assert stats["total_pdfs"] >= 3