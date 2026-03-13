"""PDF处理服务"""

import os
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image

from src.models.schemas import PDFType


class PDFService:
    """PDF处理服务类"""

    def __init__(self, thumbnail_size: int = 200):
        """
        初始化PDF服务

        Args:
            thumbnail_size: 缩略图尺寸（像素）
        """
        self.thumbnail_size = thumbnail_size

    def validate_pdf(self, file_path: str) -> bool:
        """
        验证PDF文件是否有效

        Args:
            file_path: PDF文件路径

        Returns:
            bool: 文件是否为有效PDF
        """
        if not os.path.exists(file_path):
            return False

        if not os.path.isfile(file_path):
            return False

        try:
            doc = fitz.open(file_path)
            is_valid = not doc.is_closed and doc.page_count > 0
            doc.close()
            return is_valid
        except (fitz.FileDataError, ValueError, OSError):
            return False

    def get_page_count(self, file_path: str) -> int:
        """
        获取PDF页数

        Args:
            file_path: PDF文件路径

        Returns:
            int: 页数，如果文件无效返回0
        """
        try:
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            return page_count
        except (fitz.FileDataError, fitz.FileNotFoundError, ValueError, OSError):
            return 0

    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小

        Args:
            file_path: PDF文件路径

        Returns:
            int: 文件大小（字节），如果文件不存在返回0
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def detect_pdf_type(self, file_path: str, sample_pages: int = 3) -> PDFType:
        """
        检测PDF类型（文字型/扫描型）

        通过检查前几页是否有可提取文字来判断PDF类型。
        - 如果大部分页面有可提取文字，则为文字型
        - 如果大部分页面没有文字，则为扫描型
        - 如果部分有文字部分没有，则为混合型

        Args:
            file_path: PDF文件路径
            sample_pages: 采样页面数量

        Returns:
            PDFType: PDF类型
        """
        try:
            doc = fitz.open(file_path)
            total_pages = doc.page_count

            if total_pages == 0:
                doc.close()
                return PDFType.SCANNED

            # 确定实际检查的页面数
            pages_to_check = min(sample_pages, total_pages)

            pages_with_text = 0
            pages_without_text = 0

            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text()

                # 检查文字内容是否有效（去除空白后仍有足够内容）
                cleaned_text = text.strip()
                if len(cleaned_text) > 50:  # 认为超过50个字符为有效文字
                    pages_with_text += 1
                else:
                    pages_without_text += 1

            doc.close()

            # 判断类型
            if pages_with_text == pages_to_check:
                return PDFType.TEXT
            elif pages_without_text == pages_to_check:
                return PDFType.SCANNED
            else:
                return PDFType.MIXED

        except (fitz.FileDataError, fitz.FileNotFoundError, ValueError, OSError):
            return PDFType.SCANNED

    def extract_text_from_page(self, file_path: str, page_number: int) -> str:
        """
        从指定页面提取文本

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）

        Returns:
            str: 提取的文本，如果失败返回空字符串
        """
        try:
            doc = fitz.open(file_path)

            if page_number < 0 or page_number >= doc.page_count:
                doc.close()
                return ""

            page = doc[page_number]
            text = page.get_text()
            doc.close()
            return text

        except (fitz.FileDataError, fitz.FileNotFoundError, ValueError, OSError, IndexError):
            return ""

    def extract_all_text(self, file_path: str) -> str:
        """
        提取PDF所有文本

        Args:
            file_path: PDF文件路径

        Returns:
            str: 所有页面合并的文本
        """
        try:
            doc = fitz.open(file_path)
            all_text = []

            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                all_text.append(text)

            doc.close()
            return "\n\n".join(all_text)

        except (fitz.FileDataError, fitz.FileNotFoundError, ValueError, OSError):
            return ""

    def render_page_to_image(self, file_path: str, page_number: int, dpi: int = 150) -> Optional[Image.Image]:
        """
        将PDF页面渲染为图像

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）
            dpi: 渲染DPI

        Returns:
            Image.Image: PIL图像对象，失败返回None
        """
        try:
            doc = fitz.open(file_path)

            if page_number < 0 or page_number >= doc.page_count:
                doc.close()
                return None

            page = doc[page_number]

            # 计算缩放因子（DPI / 72，因为PDF默认72DPI）
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            # 渲染页面为图像
            pix = page.get_pixmap(matrix=mat)

            # 转换为PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            doc.close()
            return img

        except (fitz.FileDataError, fitz.FileNotFoundError, ValueError, OSError, IndexError):
            return None

    def generate_thumbnail(self, file_path: str, page_number: int) -> Optional[Image.Image]:
        """
        生成页面缩略图

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）

        Returns:
            Image.Image: 缩略图图像对象，失败返回None
        """
        # 使用较低DPI渲染以获得更好的性能
        img = self.render_page_to_image(file_path, page_number, dpi=72)

        if img is None:
            return None

        # 计算缩略图尺寸（保持宽高比）
        width, height = img.size

        if width > height:
            new_width = self.thumbnail_size
            new_height = int(height * (self.thumbnail_size / width))
        else:
            new_height = self.thumbnail_size
            new_width = int(width * (self.thumbnail_size / height))

        # 缩放图像
        thumbnail = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return thumbnail

    def save_thumbnail(self, file_path: str, page_number: int, output_path: str) -> bool:
        """
        保存页面缩略图

        Args:
            file_path: PDF文件路径
            page_number: 页码（从0开始）
            output_path: 输出文件路径

        Returns:
            bool: 是否保存成功
        """
        thumbnail = self.generate_thumbnail(file_path, page_number)

        if thumbnail is None:
            return False

        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 根据扩展名确定格式
            ext = Path(output_path).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                thumbnail.save(output_path, 'JPEG', quality=85)
            elif ext == '.png':
                thumbnail.save(output_path, 'PNG')
            else:
                # 默认使用PNG格式
                thumbnail.save(output_path, 'PNG')

            return True

        except (OSError, ValueError):
            return False