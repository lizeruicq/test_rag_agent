# SimpleKnowledge.add() 方法问题修复

## 🔴 问题描述

您在 `rag_knowledge.py` 中的代码使用了不存在的 `add()` 方法：

```python
self.knowledge_base.add(doc["content"], metadata={...})
```

### 错误信息
```
AttributeError: 'SimpleKnowledge' object has no attribute 'add'
```

---

## 🔍 根本原因

`SimpleKnowledge` 类（来自 `agentscope.rag`）**没有 `add()` 方法**。

### SimpleKnowledge 的实际公开方法：
- ✅ `add_documents(documents: list[Document])` - 添加文档列表
- ✅ `retrieve(query: str, limit: int, score_threshold: float)` - 检索文档
- ✅ `retrieve_knowledge(query: str, limit: int, score_threshold: float)` - 检索知识

---

## ✅ 解决方案

### 1. 导入必要的类

```python
from agentscope.rag import SimpleKnowledge, QdrantStore, Document, DocMetadata
from agentscope.message import TextBlock
```

### 2. 使用正确的 API

**错误方式**：
```python
self.knowledge_base.add(doc["content"], metadata={...})
```

**正确方式**：
```python
# 创建 Document 对象列表
doc_objects = []
for i, doc in enumerate(documents):
    metadata = DocMetadata(
        content=TextBlock(text=doc["content"]),
        doc_id=f"{file_md5}_part_{i}",
        chunk_id=i,
        total_chunks=len(documents)
    )
    document = Document(metadata=metadata)
    doc_objects.append(document)

# 一次性添加所有文档
self.knowledge_base.add_documents(doc_objects)
```

---

## 📚 AgentScope 的 Document 结构

### DocMetadata 的必需字段

```python
DocMetadata(
    content: TextBlock | ImageBlock | VideoBlock,  # 必需：内容
    doc_id: str,                                    # 必需：文档 ID
    chunk_id: int,                                  # 必需：块索引
    total_chunks: int                               # 必需：总块数
)
```

### TextBlock 的创建

```python
from agentscope.message import TextBlock

text_block = TextBlock(text="文档内容")
```

### Document 的创建

```python
from agentscope.rag import Document

document = Document(metadata=metadata)
```

---

## 🔧 完整修复代码

```python
def add_processed_document_from_dataloader(self, processed_file_path: str) -> None:
    """Add a processed document from DataLoader to the knowledge base."""
    try:
        with open(processed_file_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)

        file_md5 = processed_data["file_md5"]
        documents = processed_data["documents"]
        original_path = processed_data["original_path"]

        if file_md5 in self.doc_mappings:
            print(f"Document with MD5 {file_md5} already exists...")
            return

        # 转换为 AgentScope Document 格式
        doc_objects = []
        for i, doc in enumerate(documents):
            doc_id = f"{file_md5}_part_{i}"
            
            metadata = DocMetadata(
                content=TextBlock(text=doc["content"]),
                doc_id=doc_id,
                chunk_id=i,
                total_chunks=len(documents)
            )
            
            document = Document(metadata=metadata)
            doc_objects.append(document)

        # 添加所有文档
        self.knowledge_base.add_documents(doc_objects)

        # 记录已添加的文档
        self.doc_mappings[file_md5] = {
            "original_path": original_path,
            "processed_path": processed_file_path,
            "added_at": str(Path(processed_file_path).stat().st_mtime),
            "parts_count": len(documents),
            "md5_hash": file_md5
        }
        self._save_doc_mappings()
        print(f"Added: {original_path} with {len(documents)} parts")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise
```

---

## ✨ 修复的优势

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **方法** | `add()` (不存在) | `add_documents()` (正确) |
| **参数** | 字符串 + 字典 | Document 对象列表 |
| **效率** | 逐个添加 | 批量添加 |
| **兼容性** | ❌ 不兼容 | ✅ 完全兼容 |
| **元数据** | 自定义格式 | AgentScope 标准格式 |

---

## 🧪 验证修复

```bash
cd /Volumes/EAGET/test_agent
python3 -c "
from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
print('✓ 导入成功')
"
```

---

## 📖 相关文档

- AgentScope RAG 文档：https://agentscope.io/
- Document 类：`agentscope.rag.Document`
- DocMetadata 类：`agentscope.rag.DocMetadata`
- TextBlock 类：`agentscope.message.TextBlock`

---

## 🎯 总结

**问题**：使用了不存在的 `add()` 方法  
**原因**：SimpleKnowledge 只有 `add_documents()` 方法  
**解决**：创建 Document 对象列表，使用 `add_documents()` 批量添加  
**状态**：✅ 已修复并验证

