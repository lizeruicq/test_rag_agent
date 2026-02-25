"""
RAG 智能体 - 从知识库中检索信息并生成回答
"""
from typing import Optional
from agentscope.agent import AgentBase
from agentscope.message import Msg, TextBlock
from agentscope.model import OllamaChatModel
from agentscope.tool import ToolResponse
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit
from agentscope.formatter import OllamaChatFormatter
from ..rag_knowledge import RAGKnowledgeBase


class SimpleRAGAgent(AgentBase):
    """
    RAG 智能体 - 从知识库检索相关文档并生成回答
    """

    def __init__(
        self,
        name: str,
        knowledge_base: RAGKnowledgeBase,
        model_name: str = "qwen3:4b",
        retrieve_limit: int = 5,
        score_threshold: float = 0.1,
        ollama_host: Optional[str] = None
    ):
        """
        Initialize RAG agent with Ollama chat model.

        Args:
            name: Agent name
            knowledge_base: RAG knowledge base instance
            model_name: Name of the Ollama chat model (default: qwen3:4b)
            retrieve_limit: Maximum number of documents to retrieve
            score_threshold: Similarity threshold for retrieval
            ollama_host: Ollama server address (default: http://localhost:11434)
        """
        super().__init__()
        self.name = name
        self.kb = knowledge_base
        self.model_name = model_name
        self.ollama_host = ollama_host or "http://localhost:11434"
        self.retrieve_limit = retrieve_limit
        self.score_threshold = score_threshold

        # Initialize Ollama chat model
        self.model = OllamaChatModel(
            model_name=model_name,
            host=self.ollama_host,
            enable_thinking=False
        )
        formatter = OllamaChatFormatter()
        print(f"Using Ollama chat model: {model_name} (host: {self.ollama_host or 'default'})")

        # 保存 formatter 供后续使用
        self.formatter = formatter

        # 创建工具包并注册工具函数
        toolkit = Toolkit()
        toolkit.register_tool_function(self.retrieve_from_knowledge_base)

        # 创建 ReAct 智能体
        sys_prompt = f"""你是{name}，一个从知识库检索并回答的助手。

你有以下工具可用：
- retrieve_from_knowledge_base: 从知识库中检索相关信息

请遵循以下步骤：
1. 分析用户问题
2. 使用 retrieve_from_knowledge_base 工具检索相关信息
3. 基于检索结果生成回答

如果知识库中没有相关信息，请明确告知用户。"""

        # 注意：不传 knowledge 参数给 ReActAgent，改为使用工具函数检索
        self.react_agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=self.model,
            formatter=formatter,
            toolkit=toolkit,
            max_iters=5,
        )

    async def retrieve_from_knowledge_base(self, query: str, limit: int = 5, score_threshold: float = 0.1) -> ToolResponse:
        """
        从知识库中检索信息的异步工具函数

        Args:
            query: 查询字符串
            limit: 返回结果的最大数量
            score_threshold: 相似度阈值

        Returns:
            ToolResponse 对象
        """
        try:
            retrieved_docs = await self.kb.retrieve(
                query=query,
                limit=limit,
                score_threshold=score_threshold
            )

            if not retrieved_docs:
                return ToolResponse(content=[TextBlock(type="text", text="未找到与查询相关的信息。")])

            # 格式化结果（Document 对象）
            formatted_results = []
            for i, doc in enumerate(retrieved_docs, 1):
                source = getattr(doc.metadata, "doc_id", "未知来源")
                content = (
                    doc.metadata.content.get("text", "")
                    if isinstance(doc.metadata.content, dict)
                    else str(getattr(doc.metadata.content, "text", doc.metadata.content))
                )[:500]
                formatted_result = f"[文档 {i}] (来源: {source})\n{content}\n"
                formatted_results.append(formatted_result)

            return ToolResponse(content=[TextBlock(type="text", text="\n".join(formatted_results))])
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"检索过程中发生错误: {str(e)}")])

    async def reply(self, msg: Msg) -> Msg:
        """
        处理用户查询，从知识库检索相关信息并生成回答

        Args:
            msg: 用户消息

        Returns:
            智能体的回复消息
        """
        # 转发给 ReActAgent 进行处理
        return await self.react_agent.reply(msg)


# 保持兼容性
SpecializedRAGAgent = SimpleRAGAgent
