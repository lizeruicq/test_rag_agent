"""
RAG 智能体 - 从知识库中检索信息并生成回答
"""
from typing import Optional
from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit
from agentscope.formatter import DashScopeChatFormatter
from ..rag_knowledge import RAGKnowledgeBase


class SimpleRAGAgent(AgentBase):
    """
    RAG 智能体 - 从知识库中检索相关文档并生成回答
    """

    def __init__(
        self,
        name: str,
        knowledge_base: RAGKnowledgeBase,
        model_name: str = "qwen-max",
        api_key: Optional[str] = None,
        retrieve_limit: int = 5,
        score_threshold: float = 0.5
    ):
        """
        初始化 RAG 智能体

        Args:
            name: 智能体名称
            knowledge_base: RAG 知识库实例
            model_name: 使用的语言模型名称
            api_key: API 密钥（如果为 None，将从环境变量读取）
            retrieve_limit: 检索文档的最大数量
            score_threshold: 相似度阈值
        """
        super().__init__()
        self.name = name
        self.kb = knowledge_base
        self.model_name = model_name
        self.api_key = api_key or knowledge_base.api_key
        self.retrieve_limit = retrieve_limit
        self.score_threshold = score_threshold

        # 初始化语言模型
        if not self.api_key:
            raise ValueError("API key is required for RAG agent")

        self.model = DashScopeChatModel(
            model_name=model_name,
            api_key=self.api_key
        )

        # 创建 formatter、工具包并注册工具函数
        formatter = DashScopeChatFormatter()
        toolkit = Toolkit()
        toolkit.register_tool_function(self.retrieve_from_knowledge_base)

        # 创建 ReAct 智能体（匹配 agentscope.ReActAgent 的构造签名）
        sys_prompt = f"你是{self.name}，一个从知识库检索并回答的助手。"
        self.react_agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=self.model,
            formatter=formatter,
            toolkit=toolkit,
            knowledge=self.kb,
            max_iters=10,
        )

    async def retrieve_from_knowledge_base(self, query: str, limit: int = 5, score_threshold: float = 0.5) -> str:
        """
        从知识库中检索信息的异步工具函数
        
        Args:
            query: 查询字符串
            limit: 返回结果的最大数量
            score_threshold: 相似度阈值
            
        Returns:
            检索到的结果
        """
        try:
            retrieved_docs = self.kb.retrieve(
                query=query,
                limit=limit,
                score_threshold=score_threshold
            )
            
            if not retrieved_docs:
                return "未找到与查询相关的信息。"
            
            # 格式化结果
            formatted_results = []
            for i, doc in enumerate(retrieved_docs, 1):
                source = doc.get("metadata", {}).get("source", "未知来源")
                content = doc.get("content", "")[:500]  # 限制每个文档的长度
                formatted_result = f"[文档 {i}] (来源: {source})\n{content}\n"
                formatted_results.append(formatted_result)
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"检索过程中发生错误: {str(e)}"

    async def reply(self, msg: Msg) -> Msg:
        """
        处理用户查询，从知识库检索相关信息并生成回答

        Args:
            msg: 用户消息

        Returns:
            智能体的回复消息
        """
        # 转发给 ReActAgent 进行处理（ReActAgent.reply 是异步的）
        return await self.react_agent.reply(msg)


# 保持兼容性
SpecializedRAGAgent = SimpleRAGAgent