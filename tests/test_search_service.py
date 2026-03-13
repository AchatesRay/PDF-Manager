"""搜索服务测试"""

import pytest
import tempfile
from pathlib import Path

from src.models.database import Database
from src.models.schemas import Folder, PDF, PDFPage, OCRStatus
from src.services.index_service import IndexService
from src.core.search_service import SearchService, GroupedSearchResult


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db(temp_dir):
    """创建数据库实例"""
    db_path = temp_dir / "test.db"
    return Database(db_path)


@pytest.fixture
def index_service(temp_dir):
    """创建索引服务实例"""
    index_path = temp_dir / "index"
    return IndexService(str(index_path))


@pytest.fixture
def search_service(db, index_service):
    """创建搜索服务实例"""
    return SearchService(db, index_service)


@pytest.fixture
def sample_data(db, index_service):
    """创建测试数据"""
    # 创建文件夹
    folder = Folder(name="测试文件夹")
    folder_id = db.create_folder(folder)

    # 创建PDF文件
    pdf1 = PDF(filename="document1.pdf", file_path="/path/to/document1.pdf", folder_id=folder_id)
    pdf1_id = db.create_pdf(pdf1)

    pdf2 = PDF(filename="document2.pdf", file_path="/path/to/document2.pdf", folder_id=None)
    pdf2_id = db.create_pdf(pdf2)

    # 创建页面并添加到索引
    # PDF1 的页面
    page1 = PDFPage(pdf_id=pdf1_id, page_number=1, ocr_text="这是一个测试文档，包含Python编程相关内容。", ocr_status=OCRStatus.DONE)
    page1_id = db.create_page(page1)
    index_service.add_page(
        page_id=f"page_{page1_id}",
        pdf_id=pdf1_id,
        page_number=1,
        folder_id=folder_id,
        filename="document1.pdf",
        content=page1.ocr_text
    )

    page2 = PDFPage(pdf_id=pdf1_id, page_number=2, ocr_text="Python是一种流行的编程语言，广泛用于数据科学和Web开发。", ocr_status=OCRStatus.DONE)
    page2_id = db.create_page(page2)
    index_service.add_page(
        page_id=f"page_{page2_id}",
        pdf_id=pdf1_id,
        page_number=2,
        folder_id=folder_id,
        filename="document1.pdf",
        content=page2.ocr_text
    )

    # PDF2 的页面
    page3 = PDFPage(pdf_id=pdf2_id, page_number=1, ocr_text="机器学习是人工智能的一个重要分支，Python是常用的工具。", ocr_status=OCRStatus.DONE)
    page3_id = db.create_page(page3)
    index_service.add_page(
        page_id=f"page_{page3_id}",
        pdf_id=pdf2_id,
        page_number=1,
        folder_id=None,
        filename="document2.pdf",
        content=page3.ocr_text
    )

    return {
        "folder_id": folder_id,
        "pdf1_id": pdf1_id,
        "pdf2_id": pdf2_id,
        "page1_id": page1_id,
        "page2_id": page2_id,
        "page3_id": page3_id
    }


class TestSearchServiceInit:
    """搜索服务初始化测试"""

    def test_init(self, db, index_service):
        """测试初始化"""
        service = SearchService(db, index_service)
        assert service._database is db
        assert service._index_service is index_service


class TestSearch:
    """搜索功能测试"""

    def test_search_basic(self, search_service, sample_data):
        """测试基本搜索"""
        results = search_service.search("Python")

        assert len(results) > 0
        # 验证结果包含搜索词
        for result in results:
            assert result.filename in ["document1.pdf", "document2.pdf"]

    def test_search_with_folder_filter(self, search_service, sample_data):
        """测试带文件夹过滤的搜索"""
        folder_id = sample_data["folder_id"]
        results = search_service.search("Python", folder_id=folder_id)

        # 所有结果应该属于指定文件夹
        for result in results:
            assert result.folder_id == folder_id

    def test_search_empty_query(self, search_service):
        """测试空查询"""
        results = search_service.search("")
        assert results == []

        results = search_service.search("   ")
        assert results == []

    def test_search_no_results(self, search_service):
        """测试无结果的搜索"""
        results = search_service.search("不存在的关键词xyz123")
        assert results == []

    def test_search_with_limit(self, search_service, sample_data):
        """测试限制结果数量"""
        results = search_service.search("Python", limit=1)
        assert len(results) <= 1

    def test_search_chinese(self, search_service, sample_data):
        """测试中文搜索"""
        results = search_service.search("编程")

        assert len(results) > 0
        # 验证找到的文档
        filenames = [r.filename for r in results]
        assert "document1.pdf" in filenames


class TestSearchGrouped:
    """分组搜索功能测试"""

    def test_search_grouped_basic(self, search_service, sample_data):
        """测试基本分组搜索"""
        results = search_service.search_grouped("Python")

        assert len(results) > 0

        # 验证结果类型
        for result in results:
            assert isinstance(result, GroupedSearchResult)
            assert result.match_count > 0
            assert result.best_score > 0
            assert len(result.pages) > 0

    def test_search_grouped_by_pdf(self, search_service, sample_data):
        """测试按PDF分组"""
        results = search_service.search_grouped("Python")

        # 验证每个PDF只出现一次
        pdf_ids = [r.pdf_id for r in results]
        assert len(pdf_ids) == len(set(pdf_ids))

        # 验证match_count等于pages数量
        for result in results:
            assert result.match_count == len(result.pages)

    def test_search_grouped_sorted_by_score(self, search_service, sample_data):
        """测试分组结果按相关性排序"""
        results = search_service.search_grouped("Python")

        # 验证按best_score降序排序
        scores = [r.best_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_grouped_with_folder_filter(self, search_service, sample_data):
        """测试带文件夹过滤的分组搜索"""
        folder_id = sample_data["folder_id"]
        results = search_service.search_grouped("Python", folder_id=folder_id)

        # 所有结果应该属于指定文件夹
        for result in results:
            assert result.folder_id == folder_id

    def test_search_grouped_empty_query(self, search_service):
        """测试空查询的分组搜索"""
        results = search_service.search_grouped("")
        assert results == []

    def test_search_grouped_with_limit(self, search_service, sample_data):
        """测试限制分组结果数量"""
        results = search_service.search_grouped("Python", limit=1)
        assert len(results) <= 1

    def test_search_grouped_contains_correct_pages(self, search_service, sample_data):
        """测试分组结果包含正确的页面"""
        results = search_service.search_grouped("Python")

        # 找到document1.pdf的分组结果
        doc1_result = None
        for result in results:
            if result.filename == "document1.pdf":
                doc1_result = result
                break

        assert doc1_result is not None
        assert doc1_result.pdf_id == sample_data["pdf1_id"]
        # 验证所有页面都属于这个PDF
        for page in doc1_result.pages:
            assert page.pdf_id == sample_data["pdf1_id"]


class TestGetPageContent:
    """获取页面内容测试"""

    def test_get_page_content_existing(self, search_service, sample_data):
        """测试获取存在的页面内容"""
        content = search_service.get_page_content(sample_data["page1_id"])

        assert content == "这是一个测试文档，包含Python编程相关内容。"

    def test_get_page_content_not_found(self, search_service):
        """测试获取不存在的页面"""
        content = search_service.get_page_content(99999)

        assert content == ""

    def test_get_page_content_empty(self, db, index_service, search_service):
        """测试获取空内容的页面"""
        # 创建PDF
        pdf = PDF(filename="empty.pdf", file_path="/empty.pdf")
        pdf_id = db.create_pdf(pdf)

        # 创建空页面
        page = PDFPage(pdf_id=pdf_id, page_number=1, ocr_text="", ocr_status=OCRStatus.PENDING)
        page_id = db.create_page(page)

        content = search_service.get_page_content(page_id)
        assert content == ""


class TestHighlightText:
    """高亮文本测试"""

    def test_highlight_text_basic(self, search_service):
        """测试基本高亮功能"""
        text = "这是一个包含Python编程的测试文本"
        result = search_service.highlight_text(text, "Python")

        assert "**Python**" in result

    def test_highlight_text_with_context(self, search_service):
        """测试带上下文的高亮"""
        text = "前面有很多文字" + "x" * 200 + "Python" + "y" * 200 + "后面也有很多文字"
        result = search_service.highlight_text(text, "Python", context_length=50)

        assert "**Python**" in result
        assert "..." in result

    def test_highlight_text_no_match(self, search_service):
        """测试无匹配时的高亮"""
        text = "这是一个测试文本"
        result = search_service.highlight_text(text, "不存在的词")

        # 无匹配时返回原文（或截断）
        assert "测试文本" in result

    def test_highlight_text_empty_query(self, search_service):
        """测试空查询时的高亮"""
        text = "这是一个测试文本"
        result = search_service.highlight_text(text, "")

        assert result == text

    def test_highlight_text_empty_text(self, search_service):
        """测试空文本的高亮"""
        result = search_service.highlight_text("", "Python")
        assert result == ""

    def test_highlight_text_case_insensitive(self, search_service):
        """测试不区分大小写的高亮"""
        text = "Python and python and PYTHON"
        result = search_service.highlight_text(text, "python")

        # 所有变体都应该被高亮
        assert "**Python**" in result or "**python**" in result or "**PYTHON**" in result

    def test_highlight_text_special_chars(self, search_service):
        """测试包含特殊字符的查询"""
        text = "这是一个(test)测试"
        result = search_service.highlight_text(text, "(test)")

        assert "**(test)**" in result

    def test_highlight_text_at_beginning(self, search_service):
        """测试关键词在开头"""
        text = "Python是一种编程语言"
        result = search_service.highlight_text(text, "Python")

        assert "**Python**" in result

    def test_highlight_text_at_end(self, search_service):
        """测试关键词在结尾"""
        text = "我喜欢Python"
        result = search_service.highlight_text(text, "Python")

        assert "**Python**" in result

    def test_highlight_text_short_text(self, search_service):
        """测试短文本的高亮"""
        text = "Python"
        result = search_service.highlight_text(text, "Python")

        assert result == "**Python**"

    def test_highlight_text_context_length(self, search_service):
        """测试上下文长度"""
        text = "a" * 500 + "Python" + "b" * 500
        result = search_service.highlight_text(text, "Python", context_length=100)

        # 结果应该比原文短
        assert len(result) < len(text)
        assert "**Python**" in result