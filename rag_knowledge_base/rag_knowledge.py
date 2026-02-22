"""RAG Knowledge Base Implementation with support for multiple document formats."""
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

from agentscope.rag import SimpleKnowledge, QdrantStore, Document, DocMetadata
import asyncio
from agentscope.embedding import DashScopeTextEmbedding


class RAGKnowledgeBase:
    """A RAG knowledge base supporting multiple document formats."""
    
    def __init__(
        self,
        embedding_model: str = "dashscope",
        model_name: str = "text-embedding-v2",
        api_key: Optional[str] = None,
        persist_path: Optional[str] = "./persist_data",
        collection_name: str = "rag_knowledge_base",
        recreate: bool = False
    ) -> None:
        """
        Initialize the RAG knowledge base.
        
        Args:
            embedding_model: Type of embedding model ('openai' or 'dashscope').
            model_name: Name of the embedding model.
            api_key: API key for the embedding service.
            persist_path: Path to persist the vector store.
            collection_name: Name of the collection in the vector store.
            recreate: Whether to recreate the knowledge base from scratch.
        """
        self.collection_name = collection_name
        self.persist_path = persist_path
        self.embedding_model_type = embedding_model
        self.model_name = model_name
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # Create persist directory if it doesn't exist
        if persist_path:
            os.makedirs(persist_path, exist_ok=True)
        
        # Initialize embedding model (DashScope only)
        if embedding_model != "dashscope":
            raise ValueError("Only 'dashscope' embedding_model is supported in this deployment")

        if not self.api_key:
            raise ValueError("DashScope API key is required")

        self.embedding_model = DashScopeTextEmbedding(
            model_name=model_name,
            api_key=self.api_key
        )
        print(f"Using DashScope model: {model_name}")
        # Default dimension: 1024 for text-embedding-v2, otherwise 1536
        self.dimensions = 1024 if "v2" in model_name else 1536
        
        # Initialize vector store
        if persist_path and not recreate:
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
        
        # Load document mapping if it exists
        self.doc_mapping_path = os.path.join(persist_path, "doc_mapping.pkl") if persist_path else None
        self.doc_mappings = self._load_doc_mappings() if self.doc_mapping_path and os.path.exists(self.doc_mapping_path) else {}
    
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

    def delete_document(self, file_md5: str) -> None:
        """Synchronous wrapper to delete document by md5 (awaits the async delete)."""
        asyncio.run(self.delete_document_by_md5(file_md5))
    
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
    

    
    def retrieve(self, query: str, limit: int = 5, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents based on the query.

        Args:
            query: Query string.
            limit: Maximum number of documents to retrieve.
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of dictionaries containing content and metadata.
        """
        results = self.knowledge_base.retrieve(
            query,
            limit=limit,
            score_threshold=score_threshold
        )
        return results
