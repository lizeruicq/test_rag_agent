# RAG 知识库系统

基于 AgentScope 的 RAG（检索增强生成）知识库系统，支持多种文档格式的上传与管理，集成 ReAct 智能体实现智能问答。采用 **async/await** 设计，便于嵌入异步应用。

## 功能特点

- **多格式文档支持**：Word (.docx)、PDF (.pdf)、纯文本 (.txt)、Excel (.xlsx, .xls)
- **智能文档管理**：MD5 去重、自动分块、元数据管理
- **向量化存储**：基于 Qdrant 的向量存储与检索（支持内存模式与持久化）
- **ReAct 智能体**：集成 AgentScope ReActAgent，自动检索知识库并生成回答
- **异步优先**：全程 async/await，可无缝嵌入 FastAPI 等异步框架
- **可扩展架构**：RAGKnowledgeBase 继承 KnowledgeBase，与 AgentScope 生态兼容

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境变量

运行前需配置 DashScope API 密钥：

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
```

## 快速开始

### 交互式菜单

```bash
# 在项目根目录执行
python rag_knowledge_base/main.py
```

菜单选项：

| 选项 | 功能 |
|------|------|
| 1 | 添加文档：输入文件或目录路径，自动识别格式并入库 |
| 2 | 查询：输入问题，智能体检索知识库并回答 |
| 3 | 统计：显示 DataLoader 管理的文件数与总大小 |
| 4 | 删除文档：按序号或 `all` 删除已入库文档 |
| 5 | 退出 |

**说明**：默认 `persist_path=None`，向量库为内存模式，进程退出后数据清空。若需持久化，在 `main.py` 中为 `RAGKnowledgeBase` 指定 `persist_path="./persist_data"`。

## 编程使用

### 异步 API（推荐）

所有核心方法均为异步，可在已有事件循环中直接 `await`：

```python
import asyncio
from rag_knowledge_base.main import SimpleRAGSystem

async def main():
    system = SimpleRAGSystem()

    # 添加文档
    await system.add_documents("/path/to/document.pdf")
    await system.add_documents("/path/to/directory")

    # 查询
    answer = await system.query("你的问题")
    print(answer)

    # 删除文档（交互式）
    await system.delete_documents_interactive()

asyncio.run(main())
```

### 嵌入 FastAPI 示例

```python
from fastapi import FastAPI
from rag_knowledge_base.main import SimpleRAGSystem

app = FastAPI()
system = SimpleRAGSystem()

@app.post("/query")
async def api_query(question: str):
    answer = await system.query(question)
    return {"answer": answer}

@app.post("/ingest")
async def api_ingest(path: str):
    await system.add_documents(path)
    return {"status": "ok"}
```

### 直接使用知识库与智能体

```python
import asyncio
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.data.data_loader import DataLoader
from rag_knowledge_base.agents.rag_agent import SpecializedRAGAgent
from agentscope.message import Msg

async def main():
    # 初始化知识库（persist_path=None 为内存模式）
    kb = RAGKnowledgeBase(
        embedding_model="dashscope",
        model_name="text-embedding-v4",
        api_key="your_api_key",  # 或从环境变量读取
        persist_path="./persist_data",  # 持久化路径，None 则内存
    )

    # 加载文档
    loader = DataLoader(data_dir="./data/documents")
    success, processed = loader.load_file("path/to/document.pdf")
    if success and processed:
        await kb.add_processed_document_from_dataloader(processed, overwrite=True)

    # 创建智能体
    agent = SpecializedRAGAgent(name="RAG_Agent", knowledge_base=kb)

    # 提问
    msg = Msg(name="User", content="你的问题", role="user")
    response = await agent(msg)
    print(response.content)

asyncio.run(main())
```

### 直接检索

```python
# 异步检索，返回 list[Document]
docs = await kb.retrieve(query="你的问题", limit=5, score_threshold=0.5)
for doc in docs:
    content = doc.metadata.content.get("text", "") if isinstance(doc.metadata.content, dict) else ""
    print(content[:200])
```

## 项目结构

```
rag_knowledge_base/
├── README.md                 # 本说明
├── requirements.txt          # 依赖
├── main.py                   # 主程序入口（交互式菜单）
├── rag_knowledge.py          # RAGKnowledgeBase（继承 KnowledgeBase）
├── agents/
│   └── rag_agent.py          # SimpleRAGAgent / SpecializedRAGAgent
├── data/
│   └── data_loader.py       # DataLoader（文档加载、MD5 去重）
└── utils/
    └── document_readers.py   # 文档读取器（Txt、PDF、Docx、Excel）
```

## 核心模块

### `rag_knowledge.py` — RAGKnowledgeBase

- 继承 `KnowledgeBase`，与 AgentScope ReActAgent 兼容
- **主要方法**：
  - `async add_processed_document_from_dataloader(processed_path, overwrite)`：从 DataLoader 处理结果添加文档
  - `async retrieve(query, limit, score_threshold)`：检索相关文档，返回 `list[Document]`
  - `async add_documents(documents)`：KnowledgeBase 接口，直接添加 Document 列表
  - `async delete_document_by_md5(file_md5)`：按 MD5 删除文档
- **空集合**：未添加过文档时检索会返回空列表，不会报错

### `agents/rag_agent.py` — SimpleRAGAgent

- 基于 ReActAgent，自动检索知识库并生成回答
- 注册 `retrieve_from_knowledge_base` 工具，返回 `ToolResponse`
- 与官方案例一致：`knowledge=self.kb`（单对象，ReActAgent 会自动转为列表）

### `data/data_loader.py` — DataLoader

- MD5 去重、自动分块、元数据管理
- 支持：`.txt`、`.docx`、`.pdf`、`.xlsx`、`.xls`
- `load_file(path)` → `(success, processed_path)`
- `load_directory(path)` → 批量加载统计

### `utils/document_readers.py` — 文档读取器

- 按扩展名自动选择读取器
- 支持 TxtReader、PdfReader、DocxReader、ExcelReader

## 配置说明

| 参数 | 说明 | 默认 |
|------|------|------|
| `embedding_model` | 嵌入模型类型 | `"dashscope"` |
| `model_name` | 嵌入模型名 | `"text-embedding-v4"` |
| `persist_path` | 持久化路径，`None` 为内存 | `"./persist_data"` |
| `collection_name` | Qdrant 集合名 | `"rag_knowledge_base"` |
| `recreate` | 是否重建知识库 | `False` |

**注意**：`text-embedding-v4` 的向量维度需与 Qdrant 集合一致。若更换 embedding 模型，需删除旧 `persist_data/vector_store` 或设置 `recreate=True`。

## 许可证

MIT
