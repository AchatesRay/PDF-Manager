"""OCR处理服务"""

import os
from typing import Optional, TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from src.services.pdf_service import PDFService


class OCRService:
    """OCR处理服务类，使用PaddleOCR进行文字识别"""

    def __init__(self, lang: str = "ch", use_gpu: bool = False):
        """
        初始化OCR服务

        Args:
            lang: OCR语言，默认为中文("ch")
            use_gpu: 是否使用GPU加速
        """
        self._lang = lang
        self._use_gpu = use_gpu
        self._ocr_engine = None
        self._available = None

    @property
    def ocr(self):
        """
        延迟加载OCR引擎

        Returns:
            PaddleOCR实例，如果加载失败返回None
        """
        if self._ocr_engine is None:
            try:
                from paddleocr import PaddleOCR

                self._ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self._lang,
                    use_gpu=self._use_gpu,
                    show_log=False
                )
                self._available = True
            except ImportError:
                self._available = False
                return None
            except Exception:
                self._available = False
                return None

        return self._ocr_engine

    def is_available(self) -> bool:
        """
        检查OCR服务是否可用

        Returns:
            bool: OCR服务是否可用
        """
        if self._available is None:
            # 尝试加载OCR引擎来检查可用性
            _ = self.ocr
        return self._available is True

    def recognize_image(self, image: Image.Image) -> str:
        """
        识别图像中的文字

        Args:
            image: PIL Image对象

        Returns:
            str: 识别出的文字，失败返回空字符串
        """
        if image is None:
            return ""

        try:
            ocr_engine = self.ocr
            if ocr_engine is None:
                return ""

            # 将PIL Image转换为numpy数组
            import numpy as np
            img_array = np.array(image)

            # 执行OCR识别
            result = ocr_engine.ocr(img_array, cls=True)

            # 解析结果
            if result is None or len(result) == 0:
                return ""

            # 提取所有识别的文字
            texts = []
            for line in result:
                if line:
                    for item in line:
                        if item and len(item) >= 2:
                            text = item[1][0]  # 获取识别的文字
                            texts.append(text)

            return "\n".join(texts)

        except Exception:
            return ""

    def recognize_image_file(self, image_path: str) -> str:
        """
        识别图像文件中的文字

        Args:
            image_path: 图像文件路径

        Returns:
            str: 识别出的文字，失败返回空字符串
        """
        if not os.path.exists(image_path):
            return ""

        if not os.path.isfile(image_path):
            return ""

        try:
            image = Image.open(image_path)

            # 转换为RGB模式（如果需要）
            if image.mode != "RGB":
                image = image.convert("RGB")

            return self.recognize_image(image)

        except Exception:
            return ""

    def recognize_pdf_page(
        self,
        pdf_service: "PDFService",
        pdf_path: str,
        page_number: int,
        dpi: int = 200
    ) -> str:
        """
        识别PDF页面的文字

        Args:
            pdf_service: PDF服务实例，用于渲染PDF页面
            pdf_path: PDF文件路径
            page_number: 页码（从0开始）
            dpi: 渲染DPI，默认200（更高的DPI可以获得更好的OCR效果）

        Returns:
            str: 识别出的文字，失败返回空字符串
        """
        if pdf_service is None:
            return ""

        # 使用PDF服务渲染页面为图像
        image = pdf_service.render_page_to_image(pdf_path, page_number, dpi=dpi)

        if image is None:
            return ""

        return self.recognize_image(image)