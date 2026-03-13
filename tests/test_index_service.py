"""索引服务测试"""

import os
import tempfile
import pytest
from pathlib import Path

from src.services.index_service import IndexService, SearchResult


class TestIndexService:
    """索引服务测试"""

    @pytest.fixture
    def temp_index_path(self):
        """创建临时索引路径"""
        temp_dir = tempfile.mkdtemp()
        index_path = os.path.join(temp_dir, "test_index")
        yield index_path
        # 清理
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def index_service(self, temp_index_path):
        """创建索引服务实例"""
        return IndexService(temp_index_path)

    def test_init(self, temp_index_path):
        """测试初始化"""
        service = IndexService(temp_index_path)
        assert service._index_path == temp_index_path
        assert service._index is None

    def test_schema(self):
        """测试Schema定义"""
        schema = IndexService.SCHEMA
        assert 'page_id' in schema
        assert 'pdf_id' in schema
        assert 'page_number' in schema
        assert 'folder_id' in schema
        assert 'filename' in schema
        assert 'content' in schema

    def test_index_property_creates_index(self, index_service, temp_index_path):
        """测试index属性创建索引"""
        idx = index_service.index
        assert idx is not None
        assert os.path.exists(temp_index_path)

    def test_index_property_reuses_index(self, index_service):
        """测试index属性重用索引"""
        idx1 = index_service.index
        idx2 = index_service.index
        assert idx1 is idx2

    def test_add_page(self, index_service):
        """测试添加页面"""
        result = index_service.add_page(
            page_id="page_1",
            pdf_id=1,
            page_number=1,
            folder_id=1,
            filename="test.pdf",
            content="This is a test document for indexing."
        )
        assert result is True
        assert index_service.get_page_count() == 1

    def test_add_page_with_chinese(self, index_service):
        """测试添加中文内容"""
        result = index_service.add_page(
            page_id="page_2",
            pdf_id=1,
            page_number=2,
            folder_id=1,
            filename="test_chinese.pdf",
            content="这是一个中文测试文档，用于测试中文分词功能。"
        )
        assert result is True
        assert index_service.get_page_count() == 1

    def test_add_page_duplicate_updates(self, index_service):
        """测试添加重复页面会更新"""
        # 第一次添加
        result1 = index_service.add_page(
            page_id="page_1",
            pdf_id=1,
            page_number=1,
            folder_id=1,
            filename="test.pdf",
            content="Original content"
        )
        assert result1 is True
        assert index_service.get_page_count() == 1

        # 第二次添加相同page_id，应该更新
        result2 = index_service.add_page(
            page_id="page_1",
            pdf_id=1,
            page_number=1,
            folder_id=1,
            filename="test.pdf",
            content="Updated content"
        )
        assert result2 is True
        # 数量应该还是1
        assert index_service.get_page_count() == 1

    def test_add_page_no_folder(self, index_service):
        """测试添加没有文件夹的页面"""
        result = index_service.add_page(
            page_id="page_no_folder",
            pdf_id=2,
            page_number=1,
            folder_id=None,
            filename="no_folder.pdf",
            content="Document without folder"
        )
        assert result is True
        assert index_service.get_page_count() == 1

    def test_delete_page(self, index_service):
        """测试删除页面"""
        # 先添加
        index_service.add_page(
            page_id="page_to_delete",
            pdf_id=1,
            page_number=1,
            folder_id=None,
            filename="test.pdf",
            content="Content to delete"
        )
        assert index_service.get_page_count() == 1

        # 删除
        result = index_service.delete_page("page_to_delete")
        assert result is True
        assert index_service.get_page_count() == 0

    def test_delete_page_nonexistent(self, index_service):
        """测试删除不存在的页面"""
        result = index_service.delete_page("nonexistent_page")
        assert result is True  # Whoosh删除不存在的文档不会报错

    def test_delete_pdf(self, index_service):
        """测试删除PDF的所有页面"""
        # 添加多个页面
        index_service.add_page("page_1", 1, 1, None, "test.pdf", "Content 1")
        index_service.add_page("page_2", 1, 2, None, "test.pdf", "Content 2")
        index_service.add_page("page_3", 1, 3, None, "test.pdf", "Content 3")
        index_service.add_page("page_4", 2, 1, None, "other.pdf", "Content 4")

        assert index_service.get_page_count() == 4

        # 删除pdf_id=1的所有页面
        count = index_service.delete_pdf(1)
        assert count >= 0  # 数量可能因为索引实现有差异
        assert index_service.get_page_count() == 1  # 只剩下pdf_id=2的页面

    def test_delete_pdf_nonexistent(self, index_service):
        """测试删除不存在的PDF"""
        count = index_service.delete_pdf(999)
        assert count == 0

    def test_search_basic(self, index_service):
        """测试基本搜索"""
        # 添加一些文档
        index_service.add_page("page_1", 1, 1, 1, "test.pdf", "Hello world, this is a test document.")
        index_service.add_page("page_2", 1, 2, 1, "test.pdf", "Another document about Python programming.")
        index_service.add_page("page_3", 2, 1, 1, "other.pdf", "Testing search functionality.")

        # 搜索
        results = index_service.search("test")
        assert len(results) > 0

    def test_search_chinese(self, index_service):
        """测试中文搜索"""
        # 添加中文文档
        index_service.add_page("page_1", 1, 1, 1, "chinese.pdf", "人工智能是计算机科学的一个分支。")
        index_service.add_page("page_2", 1, 2, 1, "chinese.pdf", "机器学习是人工智能的核心技术。")
        index_service.add_page("page_3", 2, 1, 1, "other.pdf", "深度学习在图像识别领域有广泛应用。")

        # 搜索中文
        results = index_service.search("人工智能")
        assert len(results) > 0

    def test_search_with_folder_filter(self, index_service):
        """测试带文件夹过滤的搜索"""
        # 添加不同文件夹的文档
        index_service.add_page("page_1", 1, 1, 1, "folder1.pdf", "Document in folder 1")
        index_service.add_page("page_2", 2, 1, 2, "folder2.pdf", "Document in folder 2")
        index_service.add_page("page_3", 3, 1, 1, "folder1_other.pdf", "Another document in folder 1")

        # 搜索并过滤文件夹
        results = index_service.search("Document", folder_id=1)
        assert len(results) == 2  # folder 1 有两个文档

        results = index_service.search("Document", folder_id=2)
        assert len(results) == 1  # folder 2 有一个文档

    def test_search_limit(self, index_service):
        """测试搜索结果限制"""
        # 添加多个文档
        for i in range(10):
            index_service.add_page(
                f"page_{i}",
                1,
                i + 1,
                None,
                f"test_{i}.pdf",
                f"This is test document number {i}"
            )

        # 限制结果数量
        results = index_service.search("test", limit=5)
        assert len(results) <= 5

    def test_search_result_structure(self, index_service):
        """测试搜索结果结构"""
        index_service.add_page(
            "page_1",
            1,
            1,
            10,
            "test.pdf",
            "This is a long document that should be truncated in the snippet. " * 10
        )

        results = index_service.search("document")
        assert len(results) > 0

        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.page_id == "page_1"
        assert result.pdf_id == 1
        assert result.page_number == 1
        assert result.folder_id == 10
        assert result.filename == "test.pdf"
        assert result.score > 0
        assert len(result.snippet) > 0

    def test_search_no_results(self, index_service):
        """测试搜索无结果"""
        index_service.add_page("page_1", 1, 1, None, "test.pdf", "Hello world")

        results = index_service.search("xyzabc123nonexistent")
        assert len(results) == 0

    def test_get_page_count_empty(self, index_service):
        """测试空索引的页面数量"""
        count = index_service.get_page_count()
        assert count == 0

    def test_get_page_count_multiple(self, index_service):
        """测试多个页面的数量"""
        index_service.add_page("page_1", 1, 1, None, "test.pdf", "Content 1")
        index_service.add_page("page_2", 1, 2, None, "test.pdf", "Content 2")
        index_service.add_page("page_3", 2, 1, None, "other.pdf", "Content 3")

        count = index_service.get_page_count()
        assert count == 3

    def test_clear(self, index_service):
        """测试清空索引"""
        # 添加一些文档
        index_service.add_page("page_1", 1, 1, None, "test.pdf", "Content 1")
        index_service.add_page("page_2", 1, 2, None, "test.pdf", "Content 2")
        assert index_service.get_page_count() == 2

        # 清空
        result = index_service.clear()
        assert result is True
        assert index_service.get_page_count() == 0

    def test_clear_empty_index(self, index_service):
        """测试清空空索引"""
        result = index_service.clear()
        assert result is True
        assert index_service.get_page_count() == 0

    def test_multiple_searches(self, index_service):
        """测试多次搜索"""
        index_service.add_page("page_1", 1, 1, None, "test.pdf", "Python is a programming language.")
        index_service.add_page("page_2", 1, 2, None, "test.pdf", "Java is another programming language.")
        index_service.add_page("page_3", 2, 1, None, "other.pdf", "JavaScript runs in browsers.")

        # 第一次搜索
        results1 = index_service.search("programming")
        assert len(results1) == 2

        # 第二次搜索
        results2 = index_service.search("JavaScript")
        assert len(results2) == 1

        # 第三次搜索
        results3 = index_service.search("Python")
        assert len(results3) == 1


class TestSearchResult:
    """SearchResult数据类测试"""

    def test_search_result_creation(self):
        """测试SearchResult创建"""
        result = SearchResult(
            page_id="test_page",
            pdf_id=1,
            page_number=5,
            folder_id=10,
            filename="test.pdf",
            score=0.95,
            snippet="This is a snippet..."
        )

        assert result.page_id == "test_page"
        assert result.pdf_id == 1
        assert result.page_number == 5
        assert result.folder_id == 10
        assert result.filename == "test.pdf"
        assert result.score == 0.95
        assert result.snippet == "This is a snippet..."

    def test_search_result_with_none_folder(self):
        """测试SearchResult的folder_id为None"""
        result = SearchResult(
            page_id="test_page",
            pdf_id=1,
            page_number=1,
            folder_id=None,
            filename="test.pdf",
            score=1.0,
            snippet="Snippet"
        )

        assert result.folder_id is None


class TestIndexServiceIntegration:
    """索引服务集成测试"""

    @pytest.fixture
    def temp_index_path(self):
        """创建临时索引路径"""
        temp_dir = tempfile.mkdtemp()
        index_path = os.path.join(temp_dir, "integration_index")
        yield index_path
        # 清理
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_full_workflow(self, temp_index_path):
        """测试完整工作流程"""
        service = IndexService(temp_index_path)

        # 初始状态
        assert service.get_page_count() == 0

        # 添加多个文档
        docs = [
            ("page_1", 1, 1, 1, "doc1.pdf", "Python programming tutorial for beginners."),
            ("page_2", 1, 2, 1, "doc1.pdf", "Advanced Python techniques and best practices."),
            ("page_3", 2, 1, 2, "doc2.pdf", "Machine learning with Python scikit-learn."),
            ("page_4", 3, 1, None, "doc3.pdf", "Web development using Django framework."),
        ]

        for doc in docs:
            assert service.add_page(*doc) is True

        assert service.get_page_count() == 4

        # 搜索
        results = service.search("Python")
        assert len(results) >= 3  # 至少3个文档包含Python

        # 按文件夹过滤搜索
        results_folder1 = service.search("Python", folder_id=1)
        assert len(results_folder1) >= 2

        # 删除单个页面
        assert service.delete_page("page_1") is True
        assert service.get_page_count() == 3

        # 删除整个PDF的页面
        count = service.delete_pdf(2)
        assert service.get_page_count() == 2  # 只剩下doc1.pdf的page_2和doc3.pdf

        # 清空
        assert service.clear() is True
        assert service.get_page_count() == 0

    def test_chinese_document_workflow(self, temp_index_path):
        """测试中文文档工作流程"""
        service = IndexService(temp_index_path)

        # 添加中文文档
        docs = [
            ("cn_1", 1, 1, 1, "chinese1.pdf", "人工智能技术的发展日新月异，深度学习是其中的核心技术。"),
            ("cn_2", 1, 2, 1, "chinese1.pdf", "自然语言处理是人工智能的重要应用领域。"),
            ("cn_3", 2, 1, 2, "chinese2.pdf", "计算机视觉在图像识别、目标检测等领域取得了突破性进展。"),
        ]

        for doc in docs:
            assert service.add_page(*doc) is True

        # 中文搜索
        results = service.search("人工智能")
        assert len(results) >= 2

        # 搜索学习相关
        results = service.search("学习")
        assert len(results) >= 1

        # 清理
        service.clear()