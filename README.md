# RAG 知识库系统 (Ollama + Qdrant)

基于本地 Ollama 模型和 Qdrant 向量数据库的 RAG (Retrieval-Augmented Generation) 知识库问答系统。

## 模型配置

- **嵌入模型**: `qwen3-embedding:4b` (文本向量化) - Ollama 本地
- **对话模型**: `qwen3:4b` (问答生成) - Ollama 本地
- **向量存储**: Qdrant (本地文件模式或 Docker 服务)

## 前置要求

### 1. 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# 或使用 Homebrew (macOS)
brew install ollama
```

### 2. 下载所需模型

```bash
# 下载嵌入模型
ollama pull qwen3-embedding:4b

# 下载对话模型
ollama pull qwen3:4b
```

### 3. 确保 Ollama 服务运行

```bash
# 默认运行在 http://localhost:11434
ollama serve
```

### 4. 向量存储 (二选一)

#### 方案 A: Qdrant Docker 服务（推荐）

```bash
# 使用 docker-compose 启动 Qdrant
docker-compose up -d qdrant
```

或手动启动：
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

#### 方案 B: Qdrant 本地文件模式

无需额外配置，数据将存储在 `./persist_data/vector_store`。

## 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r rag_knowledge_base/requirements.txt
pip install streamlit streamlit-lottie
```

## 使用方法

### 命令行界面

```bash
python -m rag_knowledge_base.main
```

菜单选项：
1. 添加文档 - 支持 txt, pdf, docx, xlsx 等格式
2. 查询 - 输入问题进行问答
3. 统计 - 查看知识库统计信息
4. 删除文档 - 管理已添加的文档
5. Web界面 - 启动 Web 界面
6. 退出

### Web 界面

```bash
streamlit run app.py
```

访问 http://localhost:8501

## 环境变量配置

创建 `.env` 文件：

```bash
# ============================================
# Ollama 配置
# ============================================
OLLAMA_HOST=http://localhost:11434

# ============================================
# 向量存储配置 (二选一)
# ============================================

# 方案 A: 使用 Qdrant Docker 服务
QDRANT_URL=http://localhost:6333

# 方案 B: 使用本地文件存储 (当 QDRANT_URL 未设置时生效)
# PERSIST_PATH=./persist_data
```

## 项目结构

```
.
├── rag_knowledge_base/
│   ├── main.py              # 命令行主程序
│   ├── rag_knowledge.py     # RAG 知识库实现
│   ├── agents/
│   │   └── rag_agent.py     # RAG Agent
│   ├── data/
│   │   └── data_loader.py   # 数据加载器
│   └── utils/
│       └── document_readers.py
├── app.py                   # Streamlit Web 界面
├── docker-compose.yml       # Docker Compose 配置
├── data/documents/          # 文档存储目录
├── persist_data/            # 本地向量存储数据 (元数据映射)
└── qdrant_storage/          # Qdrant Docker 数据卷
```

## 支持的文档格式

- TXT (文本文件)
- PDF
- DOCX (Word)
- XLSX/XLS (Excel)

## 特点

- ✅ 嵌入和对话模型完全本地运行（Ollama）
- ✅ 灵活的向量存储（本地文件或 Docker 服务）
- ✅ 保护隐私，数据不上传到远程 API
- ✅ 支持多种文档格式
- ✅ 向量检索 + 生成式问答
- ✅ 提供命令行和 Web 两种界面
