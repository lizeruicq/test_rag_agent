# RAG 知识库系统 - 快速开始指南

## 前置要求

1. **Python 3.10+**
2. **API 密钥**：DashScope API Key（用于向量化和 LLM）

## 安装步骤

### 1. 安装依赖

```bash
cd /Volumes/EAGET/test_agent
pip install -r rag_knowledge_base/requirements.txt
```

### 2. 设置环境变量

```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
```

## 使用方式

### 方式 1：交互式菜单（推荐）

```bash
cd /Volumes/EAGET/test_agent
python -m rag_knowledge_base.main
```

**菜单选项**：
```
1. 添加文档  2. 查询  3. 统计  4. 退出
```

**示例操作**：
```
选择: 1
文档路径: /path/to/your/documents/
✓ 批量添加完成: 3 个文件

选择: 2
问题: 文档中提到了什么？
回答: [智能体从知识库检索信息并生成回答]

选择: 3
管理文件: 3 个
存储大小: 125000 字节

选择: 4
```

### 方式 2：Python 编程

#### 基础示例

```python
from rag_knowledge_base.main import SimpleRAGSystem

# 初始化系统
system = SimpleRAGSystem()

# 添加文档
system.add_documents("/path/to/document.pdf")

# 查询
answer = system.query("你的问题")
print(answer)

# 统计
system.stats()
```

#### 高级示例

```python
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.agents.rag_agent import SimpleRAGAgent
from rag_knowledge_base.data.data_loader import DataLoader
from agentscope.message import Msg

# 初始化各个组件
kb = RAGKnowledgeBase(
    embedding_model="dashscope",
    model_name="text-embedding-v2",
    api_key="your_api_key",
    persist_path="./persist_data"
)

loader = DataLoader(data_dir="./data/documents")

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
msg = Msg(name="User", content="你的问题", role="user")
response = agent(msg)
print(response.content)
```

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| 纯文本 | .txt | 直接读取 |
| PDF | .pdf | 按页提取文本 |
| Word | .docx | 提取段落和表格 |
| Excel | .xlsx, .xls | 按工作表提取数据 |

## 常见问题

### Q1: 如何添加多个文档？

**方式 1**：使用菜单，输入目录路径
```
选择: 1
文档路径: /path/to/documents/
```

**方式 2**：编程方式
```python
system.add_documents("/path/to/documents/")
```

### Q2: 如何改进查询结果？

1. **调整检索参数**：
   ```python
   agent = SimpleRAGAgent(
       knowledge_base=kb,
       retrieve_limit=10,      # 增加检索文档数
       score_threshold=0.3     # 降低相似度阈值
   )
   ```

2. **添加更多相关文档**到知识库

3. **使用更具体的问题**

### Q3: 知识库数据存储在哪里？

- **向量存储**：`./data/storage/vector_store/`
- **文档元数据**：`./data/storage/doc_mapping.pkl`
- **原始文件**：`./data/documents/original_files/`
- **处理后文件**：`./data/documents/processed_documents/`

### Q4: 如何清空知识库？

```bash
rm -rf ./data/storage/
rm -rf ./data/documents/
```

然后重新运行程序，会自动创建新的知识库。

### Q5: 如何使用 OpenAI 的嵌入模型？

```python
kb = RAGKnowledgeBase(
    embedding_model="openai",
    model_name="text-embedding-ada-002",
    api_key="your_openai_api_key",
    persist_path="./persist_data"
)
```

## 性能优化建议

1. **文档分块**：系统自动将大文档分块（2000 字符/块）
2. **去重**：基于 MD5 自动检测重复文档
3. **检索参数**：
   - `retrieve_limit`：5-10 通常足够
   - `score_threshold`：0.3-0.5 平衡准确性和召回率

## 故障排除

### 导入错误
```
ModuleNotFoundError: No module named 'rag_knowledge_base'
```
**解决**：确保在项目根目录运行，或添加到 PYTHONPATH

### API 错误
```
ValueError: DASHSCOPE_API_KEY is required
```
**解决**：设置环境变量
```bash
export DASHSCOPE_API_KEY="your_key"
```

### 文件格式错误
```
ValueError: 不支持的文件类型
```
**解决**：确保文件格式在支持列表中

## 下一步

- 查看 `README.md` 了解详细文档
- 查看 `FIXES_SUMMARY.md` 了解修复内容
- 查看源代码了解实现细节

---

**祝你使用愉快！** 🚀

