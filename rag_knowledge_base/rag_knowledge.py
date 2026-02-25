"""RAG Knowledge Base Implementation with support for multiple document formats."""
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

from agentscope.rag import SimpleKnowledge, QdrantStore, Document, DocMetadata, KnowledgeBase
import asyncio
from agentscope.embedding import OllamaTextEmbedding


class RAGKnowledgeBase(KnowledgeBase):
    """A RAG knowledge base supporting multiple document formats."""
    
    def __init__(
        self,
        model_name: str = "qwen3-embedding:4b",
        persist_path: Optional[str] = "./persist_data",
        collection_name: str = "rag_knowledge_base",
        recreate: bool = False,
        ollama_host: Optional[str] = None,
        dimensions: int = 1024,
        qdrant_url: Optional[str] = None
    ) -> None:
        """
        Initialize the RAG knowledge base with Ollama embedding model.

        Args:
            model_name: Name of the Ollama embedding model.
            persist_path: Path to persist the vector store metadata.
            collection_name: Name of the collection in the vector store.
            recreate: Whether to recreate the knowledge base from scratch.
            ollama_host: Host URL for Ollama server (default: http://localhost:11434).
            dimensions: Embedding dimensions (default: 1024).
            qdrant_url: URL for Qdrant server (e.g., http://localhost:6333).
                      If provided, uses remote Qdrant service; otherwise uses local file storage.
        """
        self.collection_name = collection_name
        self.persist_path = persist_path
        self.model_name = model_name
        self.ollama_host = ollama_host or "http://localhost:11434"
        self.qdrant_url = qdrant_url

        # Create persist directory if it doesn't exist (for doc mappings)
        if persist_path:
            os.makedirs(persist_path, exist_ok=True)

        # Initialize Ollama embedding model
        self.embedding_model = OllamaTextEmbedding(
            model_name=model_name,
            dimensions=dimensions,
            host=self.ollama_host
        )
        print(f"Using Ollama embedding model: {model_name} (host: {self.ollama_host})")
        self.dimensions = dimensions

        # Initialize vector store (remote Qdrant or local)
        if qdrant_url:
            # Use remote Qdrant server (Docker)
            print(f"Connecting to Qdrant server at {qdrant_url}")
            self.vector_store = QdrantStore(
                location=qdrant_url,
                collection_name=collection_name,
                dimensions=self.dimensions,
                client_kwargs={"timeout": 120}
            )
        elif persist_path and not recreate:
            # Check if persistent data already exists
            vector_store_path = os.path.join(persist_path, "vector_store")
            if os.path.exists(vector_store_path):
                print(f"Loading existing vector store from {vector_store_path}")
                self.vector_store = QdrantStore(
                    location=vector_store_path,
                    collection_name=collection_name,
                    dimensions=self.dimensions
                )
            else:
                print(f"Creating new vector store at {vector_store_path}")
                self.vector_store = QdrantStore(
                    location=vector_store_path,
                    collection_name=collection_name,
                    dimensions=self.dimensions
                )
        else:
            if persist_path:
                vector_store_path = os.path.join(persist_path, "vector_store")
                self.vector_store = QdrantStore(
                    location=vector_store_path,
                    collection_name=collection_name,
                    dimensions=self.dimensions
                )
            else:
                # Use in-memory storage
                self.vector_store = QdrantStore(
                    location=":memory:",
                    collection_name=collection_name,
                    dimensions=self.dimensions
                )
        
        # Initialize knowledge base
        self.knowledge_base = SimpleKnowledge(
            embedding_store=self.vector_store,
            embedding_model=self.embedding_model
        )
        # Required by KnowledgeBase: parent expects embedding_store and embedding_model
        super().__init__(
            embedding_store=self.vector_store,
            embedding_model=self.embedding_model,
        )

        # Load document mapping if it exists
        # 无论使用本地存储还是 Docker Qdrant，都保存 doc_mappings 到本地文件
        mapping_dir = persist_path if persist_path else "./persist_data"
        os.makedirs(mapping_dir, exist_ok=True)
        self.doc_mapping_path = os.path.join(mapping_dir, "doc_mapping.pkl")
        self.doc_mappings = self._load_doc_mappings() if os.path.exists(self.doc_mapping_path) else {}
    
    def _load_doc_mappings(self) -> dict:
        """Load document mappings from persistent storage."""
        if self.doc_mapping_path and os.path.exists(self.doc_mapping_path):
            with open(self.doc_mapping_path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_doc_mappings(self) -> None:
        """Save document mappings to persistent storage."""
        if self.doc_mapping_path:
            with open(self.doc_mapping_path, 'wb') as f:
                pickle.dump(self.doc_mappings, f)

    async def delete_document_by_md5(self, file_md5: str) -> None:
        """Delete all document chunks associated with the given file MD5 from the vector store

        This uses the underlying Qdrant client to delete points by payload `doc_id`.
        After successful deletion, the mapping entry will be removed and persisted.
        """
        if file_md5 not in self.doc_mappings:
            raise KeyError(f"Document with MD5 {file_md5} not found in mappings")

        entry = self.doc_mappings[file_md5]
        parts = entry.get("parts_count", 0)

        # Use qdrant client to delete by payload filter matching each doc_id
        client = self.vector_store.get_client()
        try:
            from qdrant_client import models as q_models

            for i in range(parts):
                doc_id = f"{file_md5}_part_{i}"
                payload_filter = q_models.Filter(
                    must=[
                        q_models.FieldCondition(
                            key="doc_id",
                            match=q_models.MatchValue(value=doc_id),
                        )
                    ]
                )

                # Async delete call on qdrant client: construct a FilterSelector
                points_selector = q_models.FilterSelector(filter=payload_filter)
                await client.delete(collection_name=self.collection_name, points_selector=points_selector)

        except Exception:
            # As a fallback, attempt to delete the entire collection (dangerous) if delete by filter fails
            raise

        # Remove mapping and persist
        self.doc_mappings.pop(file_md5, None)
        self._save_doc_mappings()

    async def add_processed_document_from_dataloader(self, processed_file_path: str, overwrite: bool = False) -> None:
        """Add a processed document from DataLoader to the knowledge base.

        This method is asynchronous and will `await` the underlying
        knowledge base's `add_documents` coroutine.
        """
        try:
            # Read processed document data
            print(f"  📂 正在读取处理后的文档数据...")
            with open(processed_file_path, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)

            file_md5 = processed_data["file_md5"]
            documents = processed_data["documents"]
            original_path = processed_data["original_path"]

            # Check if already added
            if file_md5 in self.doc_mappings:
                if overwrite:
                    print(f"  ⚠️  文档已存在于知识库中，覆盖旧数据...")
                    await self.delete_document_by_md5(file_md5)
                else:
                    print(f"  ⚠️  文档已存在于知识库中，跳过...")
                    return

            # Convert documents to AgentScope Document format
            print(f"  🔄 正在转换文档格式 ({len(documents)} 个文本块)...")
            doc_objects = []
            for i, doc in enumerate(documents):
                doc_id = f"{file_md5}_part_{i}"
                # source = doc.get("source", original_path)

                # Create DocMetadata with content as a dict including a 'type' key
                # agentscope SimpleKnowledge expects metadata.content to be dict-like
                metadata = DocMetadata(
                    content={"type": "text", "text": doc["content"]},
                    doc_id=doc_id,
                    chunk_id=i,
                    total_chunks=len(documents)
                )

                # Create Document object
                document = Document(metadata=metadata)
                doc_objects.append(document)

            # Add all documents to knowledge base at once
            print(f"  🚀 正在添加到知识库（这可能需要一些时间）...")
            # agentscope SimpleKnowledge.add_documents is async: await it directly
            await self.knowledge_base.add_documents(doc_objects)
            print(f"  ✓ 文档已添加到知识库")

            # Record that this document has been added
            self.doc_mappings[file_md5] = {
                "original_path": original_path,
                "processed_path": processed_file_path,
                "added_at": str(Path(processed_file_path).stat().st_mtime),
                "parts_count": len(documents),
                "md5_hash": file_md5
            }
            self._save_doc_mappings()
            print(f"✓ 文档已成功添加: {original_path} (MD5: {file_md5}) - {len(documents)} 个文本块")

        except Exception as e:
            print(f"✗ 添加文档失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float | None = 0.1,
        **kwargs: Any,
    ) -> list[Document]:
        """
        Retrieve relevant documents (KnowledgeBase 接口，供 ReActAgent 调用).
        若 collection 尚未创建（未添加过文档），返回空列表。
        """
        try:
            return await self.knowledge_base.retrieve(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                **kwargs,
            )
        except ValueError as e:
            if "not found" in str(e).lower() or "collection" in str(e).lower():
                return []
            raise

    async def add_documents(
        self,
        documents: list[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents (KnowledgeBase 接口)."""
        await self.knowledge_base.add_documents(documents, **kwargs)

