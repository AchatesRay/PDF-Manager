# PDF Manager - 本地PDF管理工具设计文档

## 1. 项目概述

### 1.1 目标
创建一个本地PDF管理工具，支持扫描版PDF的OCR识别、全文搜索和文件管理，所有功能离线运行。

### 1.2 核心需求
- 管理本地扫描版PDF文件
- 自动识别PDF内容（OCR）
- 全文搜索功能
- 文件夹分类管理
- 全部功能本地运行，无需联网
- 运行环境：Windows 11

### 1.3 用户场景
日常工作参考，频繁搜索查阅，需要快速定位信息。

---

## 2. 技术选型

| 组件 | 技术方案 | 说明 |
|------|---------|------|
| GUI框架 | PyQt6 | 成熟稳定，界面专业 |
| OCR引擎 | PaddleOCR | 百度开源，中文识别效果最好 |
| 搜索引擎 | Whoosh + jieba | 纯Python，支持中文分词，性能良好 |
| PDF处理 | PyMuPDF | 高效的PDF渲染和图像提取 |
| 数据库 | SQLite | 轻量级，本地存储 |
| 图像处理 | Pillow | 缩略图生成 |

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      PDF Manager GUI                        │
│                        (PyQt6)                              │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  文件管理模块  │  搜索模块    │  预览模块    │   设置模块      │
├─────────────┴─────────────┴─────────────┴─────────────────┤
│                      业务逻辑层                             │
│  - 文件夹管理  - PDF导入  - OCR处理  - 搜索服务            │
├───────────────────────────────────────────────────────────┤
│                      服务层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ OCR Service │  │Search Engine│  │  PDF Service     │   │
│  │ (PaddleOCR) │  │(Whoosh+jieba)│  │  (PyMuPDF)       │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
├───────────────────────────────────────────────────────────┤
│                      数据存储层                             │
│  ┌─────────────────┐  ┌───────────────────────────────┐   │
│  │ SQLite Database │  │ 文件存储 (PDF + 缩略图缓存)    │   │
│  └─────────────────┘  └───────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

### 3.1 设计原则
- **三层架构**：UI层 → 业务逻辑层 → 服务层 → 数据层
- **离线优先**：所有功能本地运行，无网络依赖
- **增量处理**：OCR结果缓存，避免重复识别
- **响应式UI**：耗时操作在后台线程执行，界面不卡顿

---

## 4. 数据模型

### 4.1 数据库表结构

#### folders (文件夹表)
```sql
CREATE TABLE folders (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INTEGER,           -- 父文件夹ID（支持嵌套）
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (parent_id) REFERENCES folders(id)
);
```

#### pdfs (PDF文件表)
```sql
CREATE TABLE pdfs (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER,           -- 所属文件夹
    filename TEXT NOT NULL,      -- 原始文件名
    file_path TEXT NOT NULL,     -- 存储路径
    file_size INTEGER,           -- 文件大小
    page_count INTEGER,          -- 页数
    pdf_type TEXT,               -- text/scanned/mixed
    status TEXT,                 -- pending/processing/done/error
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (folder_id) REFERENCES folders(id)
);
```

#### pdf_pages (页面表)
```sql
CREATE TABLE pdf_pages (
    id INTEGER PRIMARY KEY,
    pdf_id INTEGER,              -- 所属PDF
    page_number INTEGER,         -- 页码(从1开始)
    ocr_text TEXT,               -- OCR识别的文本
    ocr_status TEXT,             -- pending/done/error
    thumbnail_path TEXT,         -- 缩略图路径
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE
);
```

### 4.2 Whoosh索引Schema

```python
schema = Schema(
    page_id=ID(stored=True, unique=True),
    pdf_id=STORED,
    page_number=STORED,
    folder_id=STORED,
    filename=TEXT(stored=True, analyzer=ChineseAnalyzer()),
    content=TEXT(stored=True, analyzer=ChineseAnalyzer())
)
```

---

## 5. 核心功能设计

### 5.1 PDF导入与OCR处理流程

```
用户添加PDF文件
       │
       ▼
┌──────────────────┐
│  文件验证        │  ← 检查是否为有效PDF，是否重复
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  PDF类型检测     │  ← 检查是否为扫描版或文字版
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
 文字型PDF   扫描型PDF
    │         │
    ▼         ▼
┌────────┐  ┌────────┐
│ 直接提取 │  │ OCR识别 │
│ 文字    │  │ 图像    │
└────┬───┘  └────┬───┘
     │           │
     └─────┬─────┘
           ▼
      复制到存储目录
           │
           ▼
      创建数据库记录
           │
           ▼
      jieba分词处理
           │
           ▼
      写入Whoosh索引
           │
           ▼
    完成，状态更新为done
```

### 5.2 PDF类型检测逻辑

```python
def detect_pdf_type(pdf_path):
    """
    检测PDF类型
    - 遍历前几页，检查是否有可提取文字
    - 如果任一页面有文字，判定为文字型
    - 否则判定为扫描型
    """
    doc = fitz.open(pdf_path)
    sample_pages = min(3, doc.page_count)  # 检查前3页

    for i in range(sample_pages):
        text = doc[i].get_text()
        if len(text.strip()) > 50:  # 有足够文字内容
            return "text"

    return "scanned"
```

### 5.3 搜索功能流程

```
用户输入搜索词
       │
       ▼
┌──────────────────┐
│  jieba分词       │  ← 将搜索词分词
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Whoosh检索      │  ← 全文搜索索引
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  获取匹配结果     │  ← pdf_id, page_number, score, snippet
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  按相关性排序     │  ← Whoosh内置评分算法
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  结果聚合展示     │  ← 高亮片段 + 页码定位
└──────────────────┘
```

### 5.4 PDF删除与数据清理

```
用户选择删除PDF
       │
       ▼
┌──────────────────┐
│  确认对话框       │  ← 提示：删除后将无法恢复
└────────┬─────────┘
         │ 用户确认
         ▼
┌──────────────────┐
│  删除存储文件     │  ← 删除PDF原文
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  删除缩略图       │  ← 删除所有页面预览图
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  清理Whoosh索引   │  ← 删除该PDF所有页面的索引文档
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  清理数据库记录   │  ← 删除pdf_pages记录 → 删除pdfs记录
└────────┬─────────┘
         │
         ▼
    删除完成
```

**清理清单**：

| 数据位置 | 清理内容 |
|---------|---------|
| 文件存储 | PDF原文 |
| 文件存储 | 所有页面缩略图 |
| Whoosh索引 | 所有页面的索引文档 |
| SQLite - pdf_pages表 | 所有页面记录 |
| SQLite - pdfs表 | PDF主记录 |

---

## 6. 界面设计

### 6.1 主界面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  PDF Manager                                    [─] [□] [×]         │
├──────────────────┬──────────────────────────────────────────────────┤
│                  │  🔍 [搜索框________________________] [搜索]       │
│   📁 文件夹       ├──────────────────────────────────────────────────┤
│   ├─ 工作文档     │  📄 PDF列表                    [添加PDF] [删除]  │
│   │  ├─ 合同      │  ┌────────────────────────────────────────────┐ │
│   │  └─ 报告      │  │ 📑 2024年度报告.pdf      50页  ✓已完成      │ │
│   ├─ 个人资料     │  │ 📑 项目合同.pdf          12页  处理中 8/12  │ │
│   └─ 归档文件     │  │ 📑 发票扫描件.pdf        5页   ✓已完成      │ │
│                  │  └────────────────────────────────────────────┘ │
│  [+新建文件夹]    ├──────────────────────────────────────────────────┤
│                  │  📖 PDF预览                                       │
│                  │  ┌────────────────────────────────────────────┐ │
│                  │  │                                            │ │
│                  │  │         [PDF页面渲染区域]                   │ │
│                  │  │                                            │ │
│                  │  │         支持缩放、翻页、搜索高亮            │ │
│                  │  │                                            │ │
│                  │  └────────────────────────────────────────────┘ │
│                  │  [◀ 上一页]  1/50  [下一页 ▶]                    │
│                  │  [外部打开] [在文件夹中显示]                      │
├──────────────────┴──────────────────────────────────────────────────┤
│  状态栏: 共 25 个PDF  |  已完成 23 个  |  处理中 2 个               │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 界面分区说明

| 区域 | 功能 |
|------|------|
| 左侧导航 | 文件夹树形结构，支持新建/重命名/删除/拖拽排序 |
| 右侧上方 | 搜索栏 + PDF列表，显示处理状态 |
| 右侧下方 | PDF预览区，支持缩放、翻页、搜索高亮定位 |
| 底部状态栏 | 统计信息，处理进度 |

### 6.3 预览区操作按钮

| 按钮 | 功能 |
|------|------|
| 上一页/下一页 | 翻页导航 |
| 外部打开 | 调用系统默认PDF阅读器打开 |
| 在文件夹中显示 | 打开PDF所在文件夹并选中文件 |

---

## 7. 项目目录结构

```
pdf-manager/
├── src/
│   ├── main.py                 # 程序入口
│   ├── ui/                     # 界面层
│   │   ├── main_window.py      # 主窗口
│   │   ├── widgets/            # 自定义控件
│   │   │   ├── folder_tree.py  # 文件夹树组件
│   │   │   ├── pdf_list.py     # PDF列表组件
│   │   │   └── pdf_viewer.py   # PDF预览组件
│   │   └── dialogs/            # 对话框
│   │       ├── settings_dialog.py
│   │       └── import_dialog.py
│   │
│   ├── core/                   # 业务逻辑层
│   │   ├── pdf_manager.py      # PDF管理服务
│   │   ├── folder_manager.py   # 文件夹管理服务
│   │   └── search_service.py   # 搜索服务
│   │
│   ├── services/               # 服务层
│   │   ├── ocr_service.py      # OCR处理服务
│   │   ├── index_service.py    # Whoosh索引服务
│   │   └── pdf_service.py      # PDF处理服务
│   │
│   ├── models/                 # 数据模型
│   │   ├── database.py         # SQLite数据库操作
│   │   └── schemas.py          # 数据结构定义
│   │
│   └── utils/                  # 工具函数
│       ├── config.py           # 配置管理
│       └── logger.py           # 日志工具
│
├── assets/                     # 资源文件
│   └── icons/                  # 图标
│
├── data/                       # 默认数据目录（用户可自定义）
│   ├── pdfs/                   # PDF文件存储
│   ├── thumbnails/             # 缩略图缓存
│   ├── index/                  # Whoosh索引
│   └── pdf_manager.db          # SQLite数据库
│
├── requirements.txt            # Python依赖
├── build.spec                  # PyInstaller打包配置
└── README.md
```

### 7.1 模块职责

| 模块 | 职责 |
|------|------|
| ui/ | 所有界面组件，与用户交互 |
| core/ | 业务逻辑，协调各服务 |
| services/ | 底层服务，OCR/索引/PDF处理 |
| models/ | 数据库操作和数据结构 |
| utils/ | 配置、日志等辅助功能 |

---

## 8. 技术实现要点

### 8.1 依赖库清单

```
# requirements.txt
PyQt6>=6.4.0              # GUI框架
paddlepaddle>=2.5.0       # PaddleOCR依赖（CPU版本）
paddleocr>=2.7.0          # OCR引擎
PyMuPDF>=1.23.0           # PDF处理
whoosh>=2.7.4             # 全文搜索引擎
jieba>=0.42.1             # 中文分词
Pillow>=10.0.0            # 图像处理
```

### 8.2 并发处理设计

```python
# OCR处理线程池
class OCRWorker(QThread):
    """后台OCR处理线程"""

    def __init__(self, pdf_queue, max_workers=2):
        self.pdf_queue = pdf_queue
        self.max_workers = max_workers  # 同时处理PDF数量

    def run(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.running:
                pdf_task = self.pdf_queue.get()
                executor.submit(self.process_pdf, pdf_task)
```

**并发策略**：
- 使用QThread保持UI响应
- ThreadPoolExecutor控制并发数（默认2个PDF）
- 每个PDF内部串行处理页面（避免内存爆炸）
- 进度信号实时更新UI

### 8.3 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| PDF文件损坏 | 记录错误状态，跳过该文件，继续处理其他 |
| OCR识别失败 | 标记该页面为error，记录失败原因 |
| 索引写入失败 | 重试3次，仍失败则记录日志 |
| 存储空间不足 | 提示用户，暂停导入 |
| 文件被占用 | 提示用户关闭文件后重试 |

### 8.4 配置管理

```python
# 用户可配置项
DEFAULT_CONFIG = {
    "storage_path": "./data",      # 数据存储路径
    "ocr_language": "ch",          # OCR语言
    "ocr_workers": 2,              # OCR并发数
    "thumbnail_size": 200,         # 缩略图尺寸
}
```

---

## 9. 功能清单与优先级

| 模块 | 功能 | 优先级 |
|------|------|--------|
| **文件夹管理** | 新建/重命名/删除文件夹 | P0 |
| | 文件夹嵌套（多级目录） | P0 |
| **PDF管理** | 添加PDF（单个/批量/文件夹） | P0 |
| | 删除PDF（含数据清理） | P0 |
| | PDF列表显示（状态、页数） | P0 |
| **OCR处理** | 扫描型PDF识别 | P0 |
| | 文字型PDF直接提取 | P0 |
| | 类型自动检测 | P0 |
| | 处理进度显示 | P0 |
| | 断点续传 | P1 |
| **搜索功能** | 全文搜索 | P0 |
| | 搜索结果高亮 | P0 |
| | 点击定位到页码 | P0 |
| **预览功能** | 内置PDF预览 | P0 |
| | 翻页/缩放 | P0 |
| | 搜索结果定位高亮 | P0 |
| | 外部程序打开 | P0 |
| **设置** | 自定义存储路径 | P1 |
| | 调整OCR并发数 | P1 |
| **数据管理** | 数据导出/导入 | P1 |

---

## 10. 验收标准

| 场景 | 预期结果 |
|------|---------|
| 添加扫描版PDF | OCR正确识别中文，可搜索到内容 |
| 添加文字型PDF | 直接提取文字，无需OCR |
| 批量添加100个PDF | 界面不卡顿，后台逐个处理 |
| 搜索关键词 | 返回匹配的PDF，高亮显示片段 |
| 点击搜索结果 | 打开预览并定位到对应页面 |
| 删除PDF | 文件、索引、数据库记录全部清理 |
| 导出数据 | 可在另一台电脑导入恢复 |

---

## 11. 约束条件

- **运行环境**：Windows 11
- **网络要求**：完全离线运行
- **硬件配置**：普通配置（无独立显卡，内存8GB或以下）
- **数据规模**：5GB以内的PDF文件
- **语言支持**：主要是中文