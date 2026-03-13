"""数据库操作测试"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.models.database import Database
from src.models.schemas import (
    Folder, PDF, PDFPage,
    PDFType, PDFStatus, OCRStatus
)


@pytest.fixture
def temp_db_path():
    """创建临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def db(temp_db_path):
    """创建数据库实例"""
    return Database(temp_db_path)


class TestDatabaseInit:
    """数据库初始化测试"""

    def test_init_creates_database_file(self, temp_db_path):
        """测试初始化创建数据库文件"""
        db = Database(temp_db_path)
        assert temp_db_path.exists()

    def test_init_creates_tables(self, temp_db_path):
        """测试初始化创建表"""
        db = Database(temp_db_path)
        # 验证表存在
        import sqlite3
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        # 检查 folders 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='folders'")
        assert cursor.fetchone() is not None

        # 检查 pdfs 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdfs'")
        assert cursor.fetchone() is not None

        # 检查 pdf_pages 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_pages'")
        assert cursor.fetchone() is not None

        conn.close()


class TestFolderOperations:
    """文件夹操作测试"""

    def test_create_folder(self, db):
        """测试创建文件夹"""
        folder = Folder(name="测试文件夹")
        folder_id = db.create_folder(folder)
        assert folder_id is not None
        assert folder_id > 0

    def test_create_nested_folder(self, db):
        """测试创建嵌套文件夹"""
        parent = Folder(name="父文件夹")
        parent_id = db.create_folder(parent)

        child = Folder(name="子文件夹", parent_id=parent_id)
        child_id = db.create_folder(child)

        assert child_id is not None
        saved_child = db.get_folder(child_id)
        assert saved_child.parent_id == parent_id

    def test_get_folder(self, db):
        """测试获取文件夹"""
        folder = Folder(name="测试文件夹")
        folder_id = db.create_folder(folder)

        result = db.get_folder(folder_id)
        assert result is not None
        assert result.id == folder_id
        assert result.name == "测试文件夹"
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_get_folder_not_found(self, db):
        """测试获取不存在的文件夹"""
        result = db.get_folder(999)
        assert result is None

    def test_get_folders_by_parent_root(self, db):
        """测试获取根目录文件夹"""
        folder1 = Folder(name="文件夹A")
        folder2 = Folder(name="文件夹B")
        db.create_folder(folder1)
        db.create_folder(folder2)

        result = db.get_folders_by_parent(None)
        assert len(result) == 2
        names = [f.name for f in result]
        assert "文件夹A" in names
        assert "文件夹B" in names

    def test_get_folders_by_parent_nested(self, db):
        """测试获取子文件夹"""
        parent = Folder(name="父文件夹")
        parent_id = db.create_folder(parent)

        child1 = Folder(name="子文件夹A", parent_id=parent_id)
        child2 = Folder(name="子文件夹B", parent_id=parent_id)
        db.create_folder(child1)
        db.create_folder(child2)

        # 创建一个不属于此父文件夹的文件夹
        other = Folder(name="其他文件夹")
        db.create_folder(other)

        result = db.get_folders_by_parent(parent_id)
        assert len(result) == 2
        names = [f.name for f in result]
        assert "子文件夹A" in names
        assert "子文件夹B" in names
        assert "其他文件夹" not in names

    def test_get_all_folders(self, db):
        """测试获取所有文件夹"""
        folder1 = Folder(name="文件夹A")
        parent = Folder(name="父文件夹")
        parent_id = db.create_folder(parent)
        child = Folder(name="子文件夹", parent_id=parent_id)
        db.create_folder(folder1)
        db.create_folder(child)

        result = db.get_all_folders()
        assert len(result) == 3

    def test_update_folder(self, db):
        """测试更新文件夹"""
        folder = Folder(name="原名称")
        folder_id = db.create_folder(folder)

        folder.id = folder_id
        folder.name = "新名称"
        result = db.update_folder(folder)

        assert result is True
        updated = db.get_folder(folder_id)
        assert updated.name == "新名称"

    def test_update_folder_without_id(self, db):
        """测试更新没有ID的文件夹"""
        folder = Folder(name="测试")
        result = db.update_folder(folder)
        assert result is False

    def test_delete_folder(self, db):
        """测试删除文件夹"""
        folder = Folder(name="待删除文件夹")
        folder_id = db.create_folder(folder)

        result = db.delete_folder(folder_id)
        assert result is True
        assert db.get_folder(folder_id) is None

    def test_delete_folder_not_found(self, db):
        """测试删除不存在的文件夹"""
        result = db.delete_folder(999)
        assert result is False


class TestPDFOperations:
    """PDF操作测试"""

    def test_create_pdf(self, db):
        """测试创建PDF"""
        pdf = PDF(filename="test.pdf", file_path="/path/to/test.pdf")
        pdf_id = db.create_pdf(pdf)
        assert pdf_id is not None
        assert pdf_id > 0

    def test_create_pdf_with_folder(self, db):
        """测试创建带文件夹的PDF"""
        folder = Folder(name="文件夹")
        folder_id = db.create_folder(folder)

        pdf = PDF(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            folder_id=folder_id,
            page_count=10,
            file_size=1024
        )
        pdf_id = db.create_pdf(pdf)

        saved_pdf = db.get_pdf(pdf_id)
        assert saved_pdf.folder_id == folder_id
        assert saved_pdf.page_count == 10
        assert saved_pdf.file_size == 1024

    def test_get_pdf(self, db):
        """测试获取PDF"""
        pdf = PDF(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            pdf_type=PDFType.SCANNED,
            status=PDFStatus.PENDING
        )
        pdf_id = db.create_pdf(pdf)

        result = db.get_pdf(pdf_id)
        assert result is not None
        assert result.id == pdf_id
        assert result.filename == "test.pdf"
        assert result.file_path == "/path/to/test.pdf"
        assert result.pdf_type == PDFType.SCANNED
        assert result.status == PDFStatus.PENDING

    def test_get_pdf_not_found(self, db):
        """测试获取不存在的PDF"""
        result = db.get_pdf(999)
        assert result is None

    def test_get_pdfs_by_folder(self, db):
        """测试获取文件夹下的PDF"""
        folder = Folder(name="文件夹")
        folder_id = db.create_folder(folder)

        pdf1 = PDF(filename="a.pdf", file_path="/a.pdf", folder_id=folder_id)
        pdf2 = PDF(filename="b.pdf", file_path="/b.pdf", folder_id=folder_id)
        pdf3 = PDF(filename="c.pdf", file_path="/c.pdf")  # 无文件夹

        db.create_pdf(pdf1)
        db.create_pdf(pdf2)
        db.create_pdf(pdf3)

        result = db.get_pdfs_by_folder(folder_id)
        assert len(result) == 2
        filenames = [p.filename for p in result]
        assert "a.pdf" in filenames
        assert "b.pdf" in filenames
        assert "c.pdf" not in filenames

    def test_get_pdfs_by_folder_root(self, db):
        """测试获取根目录的PDF"""
        pdf1 = PDF(filename="a.pdf", file_path="/a.pdf")
        pdf2 = PDF(filename="b.pdf", file_path="/b.pdf")

        db.create_pdf(pdf1)
        db.create_pdf(pdf2)

        result = db.get_pdfs_by_folder(None)
        assert len(result) == 2

    def test_get_all_pdfs(self, db):
        """测试获取所有PDF"""
        pdf1 = PDF(filename="a.pdf", file_path="/a.pdf")
        pdf2 = PDF(filename="b.pdf", file_path="/b.pdf")

        db.create_pdf(pdf1)
        db.create_pdf(pdf2)

        result = db.get_all_pdfs()
        assert len(result) == 2

    def test_update_pdf(self, db):
        """测试更新PDF"""
        pdf = PDF(filename="original.pdf", file_path="/original.pdf")
        pdf_id = db.create_pdf(pdf)

        pdf.id = pdf_id
        pdf.filename = "updated.pdf"
        pdf.page_count = 20
        pdf.status = PDFStatus.DONE

        result = db.update_pdf(pdf)
        assert result is True

        updated = db.get_pdf(pdf_id)
        assert updated.filename == "updated.pdf"
        assert updated.page_count == 20
        assert updated.status == PDFStatus.DONE

    def test_update_pdf_without_id(self, db):
        """测试更新没有ID的PDF"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf")
        result = db.update_pdf(pdf)
        assert result is False

    def test_update_pdf_status(self, db):
        """测试更新PDF状态"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf", status=PDFStatus.PENDING)
        pdf_id = db.create_pdf(pdf)

        result = db.update_pdf_status(pdf_id, PDFStatus.PROCESSING)
        assert result is True

        updated = db.get_pdf(pdf_id)
        assert updated.status == PDFStatus.PROCESSING

    def test_update_pdf_status_to_done(self, db):
        """测试更新PDF状态为完成"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf")
        pdf_id = db.create_pdf(pdf)

        db.update_pdf_status(pdf_id, PDFStatus.DONE)
        updated = db.get_pdf(pdf_id)
        assert updated.status == PDFStatus.DONE

    def test_update_pdf_status_to_error(self, db):
        """测试更新PDF状态为错误"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf")
        pdf_id = db.create_pdf(pdf)

        db.update_pdf_status(pdf_id, PDFStatus.ERROR)
        updated = db.get_pdf(pdf_id)
        assert updated.status == PDFStatus.ERROR

    def test_delete_pdf(self, db):
        """测试删除PDF"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf")
        pdf_id = db.create_pdf(pdf)

        result = db.delete_pdf(pdf_id)
        assert result is True
        assert db.get_pdf(pdf_id) is None

    def test_delete_pdf_not_found(self, db):
        """测试删除不存在的PDF"""
        result = db.delete_pdf(999)
        assert result is False


class TestPageOperations:
    """页面操作测试"""

    @pytest.fixture
    def pdf_with_id(self, db):
        """创建并返回一个PDF ID"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf")
        return db.create_pdf(pdf)

    def test_create_page(self, db, pdf_with_id):
        """测试创建页面"""
        page = PDFPage(pdf_id=pdf_with_id, page_number=1)
        page_id = db.create_page(page)
        assert page_id is not None
        assert page_id > 0

    def test_create_page_with_text(self, db, pdf_with_id):
        """测试创建带OCR文本的页面"""
        page = PDFPage(
            pdf_id=pdf_with_id,
            page_number=1,
            ocr_text="这是OCR识别的文本",
            ocr_status=OCRStatus.DONE
        )
        page_id = db.create_page(page)

        saved_page = db.get_page(page_id)
        assert saved_page.ocr_text == "这是OCR识别的文本"
        assert saved_page.ocr_status == OCRStatus.DONE

    def test_get_page(self, db, pdf_with_id):
        """测试获取页面"""
        page = PDFPage(pdf_id=pdf_with_id, page_number=1, thumbnail_path="/thumb/1.png")
        page_id = db.create_page(page)

        result = db.get_page(page_id)
        assert result is not None
        assert result.id == page_id
        assert result.pdf_id == pdf_with_id
        assert result.page_number == 1
        assert result.thumbnail_path == "/thumb/1.png"
        assert result.ocr_status == OCRStatus.PENDING

    def test_get_page_not_found(self, db):
        """测试获取不存在的页面"""
        result = db.get_page(999)
        assert result is None

    def test_get_pages_by_pdf(self, db, pdf_with_id):
        """测试获取PDF的所有页面"""
        page1 = PDFPage(pdf_id=pdf_with_id, page_number=1)
        page2 = PDFPage(pdf_id=pdf_with_id, page_number=2)
        page3 = PDFPage(pdf_id=pdf_with_id, page_number=3)

        db.create_page(page1)
        db.create_page(page2)
        db.create_page(page3)

        result = db.get_pages_by_pdf(pdf_with_id)
        assert len(result) == 3
        # 验证按页码排序
        assert result[0].page_number == 1
        assert result[1].page_number == 2
        assert result[2].page_number == 3

    def test_update_page(self, db, pdf_with_id):
        """测试更新页面"""
        page = PDFPage(pdf_id=pdf_with_id, page_number=1)
        page_id = db.create_page(page)

        page.id = page_id
        page.ocr_text = "更新后的文本"
        page.ocr_status = OCRStatus.DONE

        result = db.update_page(page)
        assert result is True

        updated = db.get_page(page_id)
        assert updated.ocr_text == "更新后的文本"
        assert updated.ocr_status == OCRStatus.DONE

    def test_update_page_without_id(self, db, pdf_with_id):
        """测试更新没有ID的页面"""
        page = PDFPage(pdf_id=pdf_with_id, page_number=1)
        result = db.update_page(page)
        assert result is False

    def test_update_page_ocr(self, db, pdf_with_id):
        """测试更新页面OCR结果"""
        page = PDFPage(pdf_id=pdf_with_id, page_number=1)
        page_id = db.create_page(page)

        result = db.update_page_ocr(page_id, "OCR识别结果", OCRStatus.DONE)
        assert result is True

        updated = db.get_page(page_id)
        assert updated.ocr_text == "OCR识别结果"
        assert updated.ocr_status == OCRStatus.DONE

    def test_update_page_ocr_error(self, db, pdf_with_id):
        """测试更新页面OCR状态为错误"""
        page = PDFPage(pdf_id=pdf_with_id, page_number=1)
        page_id = db.create_page(page)

        db.update_page_ocr(page_id, "", OCRStatus.ERROR)
        updated = db.get_page(page_id)
        assert updated.ocr_status == OCRStatus.ERROR

    def test_delete_pages_by_pdf(self, db, pdf_with_id):
        """测试删除PDF的所有页面"""
        page1 = PDFPage(pdf_id=pdf_with_id, page_number=1)
        page2 = PDFPage(pdf_id=pdf_with_id, page_number=2)
        db.create_page(page1)
        db.create_page(page2)

        count = db.delete_pages_by_pdf(pdf_with_id)
        assert count == 2
        assert len(db.get_pages_by_pdf(pdf_with_id)) == 0

    def test_delete_pages_by_pdf_empty(self, db, pdf_with_id):
        """测试删除没有页面的PDF"""
        count = db.delete_pages_by_pdf(pdf_with_id)
        assert count == 0


class TestCascadeDelete:
    """级联删除测试"""

    def test_delete_pdf_cascades_to_pages(self, db):
        """测试删除PDF时级联删除页面"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf")
        pdf_id = db.create_pdf(pdf)

        page1 = PDFPage(pdf_id=pdf_id, page_number=1)
        page2 = PDFPage(pdf_id=pdf_id, page_number=2)
        db.create_page(page1)
        db.create_page(page2)

        # 删除PDF
        db.delete_pdf(pdf_id)

        # 验证页面也被删除
        pages = db.get_pages_by_pdf(pdf_id)
        assert len(pages) == 0


class TestStatistics:
    """统计操作测试"""

    def test_get_pdf_count_all(self, db):
        """测试获取所有PDF数量"""
        pdf1 = PDF(filename="a.pdf", file_path="/a.pdf")
        pdf2 = PDF(filename="b.pdf", file_path="/b.pdf")
        pdf3 = PDF(filename="c.pdf", file_path="/c.pdf")
        db.create_pdf(pdf1)
        db.create_pdf(pdf2)
        db.create_pdf(pdf3)

        count = db.get_pdf_count()
        assert count == 3

    def test_get_pdf_count_by_folder(self, db):
        """测试获取文件夹下的PDF数量"""
        folder = Folder(name="文件夹")
        folder_id = db.create_folder(folder)

        pdf1 = PDF(filename="a.pdf", file_path="/a.pdf", folder_id=folder_id)
        pdf2 = PDF(filename="b.pdf", file_path="/b.pdf", folder_id=folder_id)
        pdf3 = PDF(filename="c.pdf", file_path="/c.pdf")

        db.create_pdf(pdf1)
        db.create_pdf(pdf2)
        db.create_pdf(pdf3)

        count = db.get_pdf_count(folder_id)
        assert count == 2

    def test_get_pdf_count_empty_folder(self, db):
        """测试获取空文件夹的PDF数量"""
        folder = Folder(name="空文件夹")
        folder_id = db.create_folder(folder)

        count = db.get_pdf_count(folder_id)
        assert count == 0

    def test_get_status_counts(self, db):
        """测试获取状态统计"""
        pdf1 = PDF(filename="a.pdf", file_path="/a.pdf", status=PDFStatus.PENDING)
        pdf2 = PDF(filename="b.pdf", file_path="/b.pdf", status=PDFStatus.PENDING)
        pdf3 = PDF(filename="c.pdf", file_path="/c.pdf", status=PDFStatus.PROCESSING)
        pdf4 = PDF(filename="d.pdf", file_path="/d.pdf", status=PDFStatus.DONE)
        pdf5 = PDF(filename="e.pdf", file_path="/e.pdf", status=PDFStatus.ERROR)

        db.create_pdf(pdf1)
        db.create_pdf(pdf2)
        db.create_pdf(pdf3)
        db.create_pdf(pdf4)
        db.create_pdf(pdf5)

        counts = db.get_status_counts()
        assert counts[PDFStatus.PENDING.value] == 2
        assert counts[PDFStatus.PROCESSING.value] == 1
        assert counts[PDFStatus.DONE.value] == 1
        assert counts[PDFStatus.ERROR.value] == 1

    def test_get_status_counts_empty(self, db):
        """测试空数据库的状态统计"""
        counts = db.get_status_counts()
        assert counts[PDFStatus.PENDING.value] == 0
        assert counts[PDFStatus.PROCESSING.value] == 0
        assert counts[PDFStatus.DONE.value] == 0
        assert counts[PDFStatus.ERROR.value] == 0


class TestPDFTypes:
    """PDF类型测试"""

    def test_pdf_type_text(self, db):
        """测试TEXT类型PDF"""
        pdf = PDF(filename="text.pdf", file_path="/text.pdf", pdf_type=PDFType.TEXT)
        pdf_id = db.create_pdf(pdf)

        result = db.get_pdf(pdf_id)
        assert result.pdf_type == PDFType.TEXT

    def test_pdf_type_scanned(self, db):
        """测试SCANNED类型PDF"""
        pdf = PDF(filename="scanned.pdf", file_path="/scanned.pdf", pdf_type=PDFType.SCANNED)
        pdf_id = db.create_pdf(pdf)

        result = db.get_pdf(pdf_id)
        assert result.pdf_type == PDFType.SCANNED

    def test_pdf_type_mixed(self, db):
        """测试MIXED类型PDF"""
        pdf = PDF(filename="mixed.pdf", file_path="/mixed.pdf", pdf_type=PDFType.MIXED)
        pdf_id = db.create_pdf(pdf)

        result = db.get_pdf(pdf_id)
        assert result.pdf_type == PDFType.MIXED

    def test_update_pdf_type(self, db):
        """测试更新PDF类型"""
        pdf = PDF(filename="test.pdf", file_path="/test.pdf", pdf_type=PDFType.SCANNED)
        pdf_id = db.create_pdf(pdf)

        pdf.id = pdf_id
        pdf.pdf_type = PDFType.MIXED
        db.update_pdf(pdf)

        result = db.get_pdf(pdf_id)
        assert result.pdf_type == PDFType.MIXED


class TestDatabaseConnection:
    """数据库连接测试"""

    def test_multiple_connections(self, temp_db_path):
        """测试多次连接"""
        db1 = Database(temp_db_path)
        folder = Folder(name="测试文件夹")
        folder_id = db1.create_folder(folder)

        db2 = Database(temp_db_path)
        result = db2.get_folder(folder_id)
        assert result is not None
        assert result.name == "测试文件夹"

    def test_context_manager(self, db):
        """测试上下文管理器"""
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1


class TestForeignKeys:
    """外键约束测试"""

    def test_folder_set_null_on_delete(self, db):
        """测试删除文件夹时PDF的folder_id设为NULL"""
        folder = Folder(name="文件夹")
        folder_id = db.create_folder(folder)

        pdf = PDF(filename="test.pdf", file_path="/test.pdf", folder_id=folder_id)
        pdf_id = db.create_pdf(pdf)

        # 删除文件夹
        db.delete_folder(folder_id)

        # 验证PDF仍然存在，但folder_id为NULL
        saved_pdf = db.get_pdf(pdf_id)
        assert saved_pdf is not None
        assert saved_pdf.folder_id is None

    def test_parent_folder_set_null_on_delete(self, db):
        """测试删除父文件夹时子文件夹的parent_id设为NULL"""
        parent = Folder(name="父文件夹")
        parent_id = db.create_folder(parent)

        child = Folder(name="子文件夹", parent_id=parent_id)
        child_id = db.create_folder(child)

        # 删除父文件夹
        db.delete_folder(parent_id)

        # 验证子文件夹仍然存在，但parent_id为NULL
        saved_child = db.get_folder(child_id)
        assert saved_child is not None
        assert saved_child.parent_id is None