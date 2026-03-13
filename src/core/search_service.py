"""搜索服务模块"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from src.models.database import Database
from src.services.index_service import IndexService, SearchResult


@dataclass
class GroupedSearchResult:
    """分组搜索结果数据类，按PDF文件分组"""
    pdf_id: int
    filename: str
    folder_id: Optional[int]
    match_count: int
    best_score: float
    pages: List[SearchResult] = field(default_factory=list)


class SearchService:
    """搜索服务类，提供全文搜索和结果分组功能"""

    def __init__(self, database: Database, index_service: IndexService):
        """
        初始化搜索服务

        Args:
            database: 数据库操作实例
            index_service: 索引服务实例
        """
        self._database = database
        self._index_service = index_service

    def search(
        self,
        query: str,
        folder_id: Optional[int] = None,
        limit: int = 100
    ) -> List[SearchResult]:
        """
        执行全文搜索

        Args:
            query: 搜索关键词
            folder_id: 限定文件夹ID（可选），None表示搜索全部
            limit: 返回结果数量限制

        Returns:
            List[SearchResult]: 搜索结果列表，按相关性排序
        """
        if not query or not query.strip():
            return []

        return self._index_service.search(query, limit=limit, folder_id=folder_id)

    def search_grouped(
        self,
        query: str,
        folder_id: Optional[int] = None,
        limit: int = 100
    ) -> List[GroupedSearchResult]:
        """
        执行分组搜索，结果按PDF文件分组

        Args:
            query: 搜索关键词
            folder_id: 限定文件夹ID（可选），None表示搜索全部
            limit: 返回结果数量限制（按PDF文件数量限制）

        Returns:
            List[GroupedSearchResult]: 分组搜索结果列表，按最佳相关性排序
        """
        if not query or not query.strip():
            return []

        # 执行基础搜索，获取更多结果以便分组
        search_results = self._index_service.search(
            query,
            limit=limit * 10,  # 获取更多结果用于分组
            folder_id=folder_id
        )

        if not search_results:
            return []

        # 按pdf_id分组
        grouped: dict[int, GroupedSearchResult] = {}

        for result in search_results:
            pdf_id = result.pdf_id

            if pdf_id not in grouped:
                grouped[pdf_id] = GroupedSearchResult(
                    pdf_id=pdf_id,
                    filename=result.filename,
                    folder_id=result.folder_id,
                    match_count=0,
                    best_score=0.0,
                    pages=[]
                )

            grouped[pdf_id].pages.append(result)
            grouped[pdf_id].match_count += 1

            # 更新最佳分数
            if result.score > grouped[pdf_id].best_score:
                grouped[pdf_id].best_score = result.score

        # 转换为列表并按最佳相关性排序
        results = list(grouped.values())
        results.sort(key=lambda x: x.best_score, reverse=True)

        # 应用limit限制
        return results[:limit]

    def get_page_content(self, page_id: int) -> str:
        """
        获取页面内容

        Args:
            page_id: 页面ID

        Returns:
            str: 页面OCR文本内容，如果页面不存在则返回空字符串
        """
        page = self._database.get_page(page_id)

        if page is None:
            return ""

        return page.ocr_text or ""

    def highlight_text(
        self,
        text: str,
        query: str,
        context_length: int = 100
    ) -> str:
        """
        高亮搜索词并提取上下文

        Args:
            text: 原始文本
            query: 搜索关键词
            context_length: 上下文长度（字符数）

        Returns:
            str: 带有高亮标记的上下文文本，使用 ** 标记高亮
        """
        if not text or not query:
            return text or ""

        # 清理查询词
        query = query.strip()
        if not query:
            return text

        # 构建正则表达式模式，匹配查询词（忽略大小写）
        # 使用re.escape处理特殊字符
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        # 查找第一个匹配
        match = pattern.search(text)

        if not match:
            # 如果没有匹配，返回文本开头部分
            return text[:context_length] + "..." if len(text) > context_length else text

        # 计算上下文范围
        match_start = match.start()
        match_end = match.end()

        # 计算上下文的起始和结束位置
        context_start = max(0, match_start - context_length // 2)
        context_end = min(len(text), match_end + context_length // 2)

        # 提取上下文
        context = text[context_start:context_end]

        # 添加省略号
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."

        # 在上下文中高亮匹配词
        highlighted = pattern.sub(lambda m: f"**{m.group()}**", context)

        return highlighted