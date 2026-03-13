"""全文索引服务"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from whoosh.index import create_in, exists_in, open_dir
from whoosh.fields import ID, NUMERIC, TEXT, Schema
from whoosh.qparser import QueryParser
from whoosh.analysis import RegexAnalyzer

from jieba.analyse import ChineseAnalyzer


@dataclass
class SearchResult:
    """搜索结果数据类"""
    page_id: str
    pdf_id: int
    page_number: int
    folder_id: Optional[int]
    filename: str
    score: float
    snippet: str


class IndexService:
    """全文索引服务类，使用Whoosh和jieba进行中文分词搜索"""

    # 用于表示null文件夹的特殊值
    NULL_FOLDER_ID = -1

    # 定义索引Schema
    SCHEMA = Schema(
        page_id=ID(stored=True, unique=True),
        pdf_id=NUMERIC(stored=True, numtype=int),
        page_number=NUMERIC(stored=True, numtype=int),
        folder_id=NUMERIC(stored=True, numtype=int),
        filename=TEXT(stored=True),
        content=TEXT(analyzer=ChineseAnalyzer(), stored=True)
    )

    def __init__(self, index_path: str):
        """
        初始化索引服务

        Args:
            index_path: 索引存储路径
        """
        self._index_path = index_path
        self._index = None

    @property
    def index(self):
        """
        获取或创建索引

        Returns:
            whoosh.index.Index: 索引对象
        """
        if self._index is None:
            index_dir = Path(self._index_path)

            # 确保索引目录存在
            if not index_dir.exists():
                index_dir.mkdir(parents=True, exist_ok=True)
                self._index = create_in(str(index_dir), self.SCHEMA)
            elif exists_in(str(index_dir)):
                self._index = open_dir(str(index_dir))
            else:
                self._index = create_in(str(index_dir), self.SCHEMA)

        return self._index

    def add_page(
        self,
        page_id: str,
        pdf_id: int,
        page_number: int,
        folder_id: Optional[int],
        filename: str,
        content: str
    ) -> bool:
        """
        添加页面到索引

        Args:
            page_id: 页面唯一标识符
            pdf_id: PDF文件ID
            page_number: 页码
            folder_id: 文件夹ID（可选）
            filename: 文件名
            content: 页面文本内容

        Returns:
            bool: 是否添加成功
        """
        try:
            writer = self.index.writer()

            # 先尝试删除已存在的记录（避免重复）
            writer.delete_by_term('page_id', page_id)

            # 处理folder_id为None的情况
            stored_folder_id = self.NULL_FOLDER_ID if folder_id is None else folder_id

            # 添加新记录
            writer.add_document(
                page_id=page_id,
                pdf_id=pdf_id,
                page_number=page_number,
                folder_id=stored_folder_id,
                filename=filename,
                content=content
            )

            writer.commit()
            return True

        except Exception:
            return False

    def delete_page(self, page_id: str) -> bool:
        """
        从索引删除页面

        Args:
            page_id: 页面唯一标识符

        Returns:
            bool: 是否删除成功
        """
        try:
            writer = self.index.writer()
            writer.delete_by_term('page_id', page_id)
            writer.commit()
            return True

        except Exception:
            return False

    def delete_pdf(self, pdf_id: int) -> int:
        """
        删除PDF的所有页面索引

        Args:
            pdf_id: PDF文件ID

        Returns:
            int: 删除的页面数量
        """
        try:
            # 先统计要删除的数量
            count = 0
            with self.index.searcher() as searcher:
                # 使用TermQuery查找所有匹配的文档
                from whoosh.query import Term
                query = Term('pdf_id', pdf_id)
                count = searcher.search(query, limit=None).estimated_length()

            # 删除所有匹配的文档
            if count > 0:
                writer = self.index.writer()
                writer.delete_by_term('pdf_id', pdf_id)
                writer.commit()

            return count

        except Exception:
            return 0

    def search(
        self,
        query_text: str,
        limit: int = 50,
        folder_id: Optional[int] = None
    ) -> List[SearchResult]:
        """
        搜索索引

        Args:
            query_text: 搜索关键词
            limit: 返回结果数量限制
            folder_id: 限定文件夹ID（可选）

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        results = []

        try:
            with self.index.searcher() as searcher:
                # 构建查询
                parser = QueryParser('content', self.index.schema)

                # 对搜索词进行中文分词处理
                # 将查询文本分词后组合
                analyzer = ChineseAnalyzer()
                tokens = [token.text for token in analyzer(query_text)]

                if not tokens:
                    return results

                # 构建OR查询，匹配任意分词结果
                query_str = ' OR '.join(tokens)
                query = parser.parse(query_str)

                # 如果指定了文件夹，添加过滤条件
                if folder_id is not None:
                    from whoosh.query import And, Term
                    folder_query = Term('folder_id', folder_id)
                    query = And([query, folder_query])

                # 执行搜索
                search_results = searcher.search(query, limit=limit)

                # 转换结果
                for hit in search_results:
                    # 生成摘要（取内容的前200个字符）
                    content = hit.get('content', '')
                    snippet = content[:200] + '...' if len(content) > 200 else content

                    # 处理folder_id的null值转换
                    stored_folder_id = hit.get('folder_id')
                    result_folder_id = None if stored_folder_id == self.NULL_FOLDER_ID else stored_folder_id

                    result = SearchResult(
                        page_id=hit.get('page_id'),
                        pdf_id=hit.get('pdf_id'),
                        page_number=hit.get('page_number'),
                        folder_id=result_folder_id,
                        filename=hit.get('filename', ''),
                        score=hit.score,
                        snippet=snippet
                    )
                    results.append(result)

        except Exception:
            pass

        return results

    def get_page_count(self) -> int:
        """
        获取索引中的页面数量

        Returns:
            int: 页面数量
        """
        try:
            with self.index.searcher() as searcher:
                return searcher.doc_count()
        except Exception:
            return 0

    def clear(self) -> bool:
        """
        清空索引

        Returns:
            bool: 是否清空成功
        """
        try:
            # 关闭当前索引
            if self._index is not None:
                self._index.close()
                self._index = None

            # 删除索引目录中的所有文件
            index_dir = Path(self._index_path)
            if index_dir.exists():
                import shutil
                shutil.rmtree(index_dir)

            # 确保目录存在
            index_dir.mkdir(parents=True, exist_ok=True)

            # 重新创建索引
            self._index = create_in(str(index_dir), self.SCHEMA)

            return True

        except Exception:
            return False