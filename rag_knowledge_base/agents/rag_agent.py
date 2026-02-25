"""
RAG 智能体 - 从知识库中检索信息并生成回答
"""
from typing import Optional
from agentscope.agent import AgentBase
from agentscope.message import Msg, TextBlock
from agentscope.model import DashScopeChatModel, OllamaChatModel
from agentscope.tool import ToolResponse
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit
from agentscope.formatter import DashScopeChatFormatter, OllamaChatFormatter
from ..rag_knowledge import RAGKnowledgeBase


class SimpleRAGAgent(AgentBase):
    """
    RAG 智能体 - 从知识库检索相关文档并生成回答
    """

    def __init__(
        self,
        name: str,
        knowledge_base: RAGKnowledgeBase,
        model_name: str = "deepseek-v3.2",
        api_key: Optional[str] = None,
        retrieve_limit: int = 5,
        score_threshold: float = 0.1,
        model_type: str = "dashscope",
        ollama_host: Optional[str] = None
    ):
        """
        初始化 RAG 智能体

        Args:
            name: 智能体名称
            knowledge_base: RAG 知识库实例
            model_name: 使用的语言模型名称
            api_key: API 密钥（如果为 None，将从环境变量读取，不适用于 ollama）
            retrieve_limit: 检索文档的最大数量
            score_threshold: 相似度阈值
            model_type: 模型类型 ('dashscope' 或 'ollama')
            ollama_host: Ollama 服务器地址 (如 'http://localhost:11434')
        """
        super().__init__()
        self.name = name
        self.kb = knowledge_base
        self.model_name = model_name
        self.model_type = model_type
        self.ollama_host = ollama_host
        self.api_key = api_key or getattr(knowledge_base, 'api_key', None)
        self.retrieve_limit = retrieve_limit
        self.score_threshold = score_threshold

        # 初始化语言模型
        if model_type == "ollama":
            self.model = OllamaChatModel(
                model_name=model_name,
                host=ollama_host,
                enable_thinking=False
            )
            formatter = OllamaChatFormatter()
            print(f"Using Ollama chat model: {model_name} (host: {ollama_host or 'default'})")
        elif model_type == "dashscope":
            if not self.api_key:
                raise ValueError("API key is required for DashScope model")
            self.model = DashScopeChatModel(
                model_name=model_name,
                api_key=self.api_key
            )
            formatter = DashScopeChatFormatter()
            print(f"Using DashScope chat model: {model_name}")
        else:
            raise ValueError(f"Unsupported model_type: {model_type}. Use 'dashscope' or 'ollama'")

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
