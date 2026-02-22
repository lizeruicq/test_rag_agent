# RAG 知识库系统

这是一个基于 AgentScope 的 RAG（检索增强生成）知识库系统，支持多种文档格式的上传和管理，并集成了智能体来处理用户查询。

## 功能特点

- ✅ **多格式文档支持**：Word (.docx)、PDF (.pdf)、纯文本 (.txt)、Excel (.xlsx, .xls)
- ✅ **智能文档管理**：MD5 去重、自动分块、元数据管理
- ✅ **向量化存储**：基于 Qdrant 的高效向量存储和检索
- ✅ **智能问答**：集成 AgentScope 智能体，从知识库中检索信息并生成回答
- ✅ **持久化存储**：知识库数据和文档元数据持久化
- ✅ **可扩展架构**：易于添加新的文档读取器和功能

## 安装依赖

```bash
pip install -r requirements.txt
```

如果要使用 OpenAI 的嵌入模型，还需要安装：

```bash
pip install openai
```

## 环境变量配置

在运行之前，请设置必要的 API 密钥：

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
# 或者如果使用 OpenAI
export OPENAI_API_KEY="your_openai_api_key_here"
```

## 使用方法

### 快速开始 - 交互式菜单

最简单的使用方式是运行主程序的交互式菜单：

```bash
cd /path/to/rag_knowledge_base
python main.py
```

菜单选项：
```
1. 添加文档  2. 查询  3. 统计  4. 退出
```

**功能说明：**
- **选项 1 - 添加文档**：输入文件或目录路径，系统会自动识别支持的文件类型并添加到知识库
- **选项 2 - 查询**：输入问题，智能体会从知识库中检索相关信息并生成回答
- **选项 3 - 统计**：显示知识库中管理的文件数量和总大小
- **选项 4 - 退出**：退出程序

### 编程方式使用

#### 基础用法 - 管理知识库

```python
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.data.data_loader import DataLoader

# 初始化知识库
kb = RAGKnowledgeBase(
    embedding_model="dashscope",  # 或 "openai"
    model_name="text-embedding-v2",
    api_key="your_api_key_here",
    persist_path="./persist_data"
)

# 初始化数据加载器
loader = DataLoader(data_dir="./data/documents")

# 添加单个文档
success, processed_path = loader.load_file("path/to/document.pdf")
if success and processed_path:
    kb.add_processed_document_from_dataloader(processed_path)

# 添加整个目录的文档
stats = loader.load_directory("./my_documents")
for file_info in stats['loaded_files']:
    kb.add_processed_document_from_dataloader(file_info['processed'])

# 查看统计信息
stats = loader.get_statistics()
print(f"总文件数: {stats['total_files']}")
print(f"按类型统计: {stats['by_extension']}")
print(f"总大小: {stats['total_size']} 字节")
```

#### 高级用法 - 使用智能体进行问答

```python
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.agents.rag_agent import SimpleRAGAgent
from agentscope.message import Msg

# 初始化知识库
kb = RAGKnowledgeBase(
    embedding_model="dashscope",
    model_name="text-embedding-v2",
    api_key="your_api_key_here",
    persist_path="./persist_data"
)

# 创建 RAG 智能体
agent = SimpleRAGAgent(
    name="RAG_Agent",
    knowledge_base=kb,
    model_name="qwen-max",
    retrieve_limit=5,
    score_threshold=0.5
)

# 提问
msg = Msg(name="User", content="你的问题", role="user")
response = agent(msg)
print(f"回答: {response.content}")
```

#### 直接检索文档

```python
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase

kb = RAGKnowledgeBase(
    embedding_model="dashscope",
    model_name="text-embedding-v2",
    api_key="your_api_key_here",
    persist_path="./persist_data"
)

# 检索相关文档
results = kb.retrieve(
    query="你的问题",
    limit=5,
    score_threshold=0.5
)

# 处理结果
for doc in results:
    print(f"来源: {doc['metadata']['source']}")
    print(f"内容: {doc['content'][:200]}...")
```

## 项目结构

```
rag_knowledge_base/
├── README.md                           # 本说明文件
├── requirements.txt                    # 项目依赖
├── __init__.py                         # 包初始化
├── main.py                             # 主程序入口 - 交互式菜单
├── rag_knowledge.py                    # RAG 知识库核心类
├── agents/                             # 智能体模块
│   ├── __init__.py
│   └── rag_agent.py                    # SimpleRAGAgent - 智能问答智能体
├── data/                               # 数据管理模块
│   ├── __init__.py
│   └── data_loader.py                  # DataLoader - 文档加载和管理
└── utils/                              # 工具模块
    ├── __init__.py
    └── document_readers.py             # 文档读取器 - 支持多种格式
```

### 核心模块说明

#### `rag_knowledge.py` - RAGKnowledgeBase 类
- **功能**：知识库的核心类，管理向量存储和文档检索
- **主要方法**：
  - `add_processed_document_from_dataloader()`：添加处理后的文档
  - `retrieve()`：检索相关文档

#### `agents/rag_agent.py` - SimpleRAGAgent 类
- **功能**：智能体，从知识库检索信息并生成回答
- **特点**：
  - 自动从知识库检索相关文档
  - 使用 LLM 生成自然语言回答
  - 支持自定义检索参数

#### `data/data_loader.py` - DataLoader 类
- **功能**：文档加载和管理系统
- **特点**：
  - MD5 去重检测
  - 自动文档分块
  - 元数据管理
  - 支持单文件和批量加载

#### `utils/document_readers.py` - 文档读取器
- **支持的格式**：
  - `.txt` - TxtReader
  - `.pdf` - PdfReader
  - `.docx` - DocxReader
  - `.xlsx`, `.xls` - ExcelReader
- **特点**：自动文本分块，保留文档来源信息

## 如何贡献

如果您发现任何问题或想添加新功能，请提交 Issue 或 Pull Request。

## 许可证

MIT