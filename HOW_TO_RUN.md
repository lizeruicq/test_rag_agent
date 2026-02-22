# 如何运行 RAG 知识库系统

## 🚀 快速开始

### 方式 1：使用 `-m` 标志（推荐）

```bash
cd /Volumes/EAGET/test_agent
python -m rag_knowledge_base.main
```

**优点：**
- ✅ 标准的 Python 包运行方式
- ✅ 正确处理相对导入
- ✅ 易于在不同目录运行

### 方式 2：直接运行文件

```bash
cd /Volumes/EAGET/test_agent/rag_knowledge_base
python main.py
```

**优点：**
- ✅ 简单直接
- ✅ 无需记住包名
- ✅ 适合快速测试

---

## 📋 菜单选项

运行后会看到以下菜单：

```
1. 添加文档  2. 查询  3. 统计  4. 退出
选择:
```

### 选项 1：添加文档

```
选择: 1
文档路径: /path/to/your/document.pdf
✓ 文档添加成功
```

**支持的格式：**
- `.txt` - 纯文本
- `.pdf` - PDF 文件
- `.docx` - Word 文档
- `.xlsx`, `.xls` - Excel 表格

### 选项 2：查询知识库

```
选择: 2
问题: 文档中提到了什么？
回答: [智能体从知识库检索信息并生成回答]
```

### 选项 3：统计信息

```
选择: 3
管理文件: 3 个
存储大小: 125000 字节
```

### 选项 4：退出

```
选择: 4
```

---

## 🐍 Python 编程方式

### 基础使用

```python
from rag_knowledge_base.main import SimpleRAGSystem

# 初始化系统
system = SimpleRAGSystem()

# 添加文档
system.add_documents("/path/to/document.pdf")

# 查询
answer = system.query("您的问题")
print(answer)

# 统计
system.stats()
```

### 高级使用

```python
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.agents.rag_agent import SimpleRAGAgent
from rag_knowledge_base.data.data_loader import DataLoader
from agentscope.message import Msg
import os

# 初始化知识库
kb = RAGKnowledgeBase(
    embedding_model="dashscope",
    model_name="text-embedding-v2",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    persist_path="./data/storage"
)

# 初始化数据加载器
loader = DataLoader(data_dir="./data/documents")

# 初始化智能体
agent = SimpleRAGAgent(
    name="RAG_Agent",
    knowledge_base=kb,
    retrieve_limit=5,
    score_threshold=0.5
)

# 添加文档
success, processed = loader.load_file("document.pdf")
if success and processed:
    kb.add_processed_document_from_dataloader(processed)

# 查询
msg = Msg(name="User", content="您的问题", role="user")
response = agent(msg)
print(response.content)
```

---

## 🔧 环境配置

### 1. 安装依赖

```bash
cd /Volumes/EAGET/test_agent
pip install -r rag_knowledge_base/requirements.txt
```

### 2. 设置 API 密钥

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
```

或在代码中设置：

```python
import os
os.environ["DASHSCOPE_API_KEY"] = "your_api_key"
```

---

## 📁 目录结构

```
/Volumes/EAGET/test_agent/
├── rag_knowledge_base/
│   ├── __init__.py
│   ├── main.py                    # 主程序（可直接运行）
│   ├── rag_knowledge.py           # 知识库类
│   ├── requirements.txt
│   ├── agents/
│   │   ├── __init__.py
│   │   └── rag_agent.py           # RAG 智能体
│   ├── data/
│   │   ├── __init__.py
│   │   └── data_loader.py         # 数据加载器
│   └── utils/
│       ├── __init__.py
│       └── document_readers.py    # 文档读取器
├── data/
│   ├── documents/                 # 文档存储
│   │   ├── original_files/        # 原始文件
│   │   ├── processed_documents/   # 处理后的文件
│   │   └── logs/                  # 日志
│   └── storage/                   # 向量数据库
│       └── vector_store/          # Qdrant 存储
└── ...
```

---

## ✅ 验证安装

### 测试导入

```bash
python3 -c "from rag_knowledge_base.main import SimpleRAGSystem; print('✓ OK')"
```

### 测试运行

```bash
# 方式 1
python -m rag_knowledge_base.main

# 方式 2
cd rag_knowledge_base && python main.py
```

---

## 🐛 常见问题

### Q1: ImportError: attempted relative import with no known parent package

**原因：** 直接运行 `main.py` 时，Python 不知道它是包的一部分

**解决：**
```bash
# 使用 -m 标志
python -m rag_knowledge_base.main

# 或从项目根目录运行
cd /Volumes/EAGET/test_agent
python rag_knowledge_base/main.py
```

### Q2: ModuleNotFoundError: No module named 'rag_knowledge_base'

**原因：** 不在正确的目录

**解决：**
```bash
# 确保在项目根目录
cd /Volumes/EAGET/test_agent
python -m rag_knowledge_base.main
```

### Q3: DASHSCOPE_API_KEY not found

**原因：** 未设置 API 密钥

**解决：**
```bash
export DASHSCOPE_API_KEY="your_api_key"
python -m rag_knowledge_base.main
```

---

## 📚 相关文档

- **快速开始**：`QUICK_START.md`
- **存储架构**：`STORAGE_ARCHITECTURE.md`
- **修复说明**：`IMPORT_AND_AGENTBASE_FIX.md`

---

## 🎯 总结

| 方式 | 命令 | 位置 | 推荐度 |
|------|------|------|--------|
| 使用 `-m` | `python -m rag_knowledge_base.main` | 项目根目录 | ⭐⭐⭐⭐⭐ |
| 直接运行 | `python main.py` | `rag_knowledge_base/` | ⭐⭐⭐ |
| Python 代码 | `from rag_knowledge_base.main import ...` | 任何地方 | ⭐⭐⭐⭐ |

---

**现在您可以开始使用 RAG 知识库系统了！** 🎉

