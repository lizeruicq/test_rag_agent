#!/usr/bin/env python3
"""
Streamlit 前端 - RAG 知识库问答界面
"""
import os
import sys
import asyncio
import streamlit as st

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.data.data_loader import DataLoader
from rag_knowledge_base.agents.rag_agent import SpecializedRAGAgent

# 页面配置
st.set_page_config(
    page_title="RAG 知识库问答",
    page_icon="📚",
    layout="wide"
)

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system" not in st.session_state:
    st.session_state.system = None

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "refresh_docs" not in st.session_state:
    st.session_state.refresh_docs = False


def init_system():
    """初始化 RAG 系统"""
    if st.session_state.system is None:
        with st.spinner("正在初始化知识库..."):
            qdrant_url = os.getenv("QDRANT_URL")
            if qdrant_url:
                persist_path = None
            else:
                persist_path = "./persist_data"

            kb = RAGKnowledgeBase(
                embedding_model="dashscope",
                model_name="text-embedding-v4",
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                persist_path=persist_path,
                qdrant_url=qdrant_url
            )

            loader = DataLoader(data_dir="./data/documents")
            agent = SpecializedRAGAgent(
                name="RAG_Agent",
                knowledge_base=kb,
                score_threshold=0.1
            )

            st.session_state.system = {
                "kb": kb,
                "loader": loader,
                "agent": agent
            }


async def query_agent(question: str) -> str:
    """查询智能体"""
    from agentscope.message import Msg

    system = st.session_state.system
    if system is None:
        return "系统未初始化"

    msg = Msg(name="User", content=question, role="user")
    response = await system["agent"](msg)

    # 处理不同类型的 content
    content = response.content
    if isinstance(content, list):
        # 如果是列表，提取所有文本块
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts)
    elif isinstance(content, dict):
        # 如果是字典，提取文本
        return content.get("text", str(content))
    else:
        # 字符串直接返回
        return str(content)


def main():
    """主界面"""
    st.title("📚 RAG 知识库问答系统")
    st.markdown("---")

    # 初始化系统
    init_system()

    # 侧边栏 - 文档管理
    with st.sidebar:
        st.header("📁 文档管理")

        # 添加文档
        uploaded_file = st.file_uploader(
            "上传文档",
            type=["txt", "pdf", "docx", "xlsx", "xls"],
            help="支持 TXT, PDF, DOCX, XLSX, XLS 格式"
        )

        if uploaded_file is not None:
            if st.button("📤 添加到知识库"):
                with st.spinner("正在处理文档..."):
                    # 保存上传的文件
                    file_path = f"./data/uploaded/{uploaded_file.name}"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    # 异步添加到知识库
                    async def add_doc():
                        system = st.session_state.system
                        success, processed = system["loader"].load_file(file_path)
                        if success and processed:
                            await system["kb"].add_processed_document_from_dataloader(
                                processed, overwrite=True
                            )
                            return True
                        return False

                    try:
                        result = asyncio.run(add_doc())
                        if result:
                            st.success(f"✅ {uploaded_file.name} 添加成功！")
                        else:
                            st.error("❌ 添加失败")
                    except Exception as e:
                        st.error(f"❌ 错误: {str(e)}")

        st.markdown("---")

        # 显示统计
        if st.button("📊 刷新统计"):
            system = st.session_state.system
            stats = system["loader"].get_statistics()
            st.metric("管理文件", stats.get("total_files", 0))
            st.metric("存储大小", f"{stats.get('total_size', 0) / 1024:.1f} KB")

        st.markdown("---")

        # 已添加的文档列表
        st.subheader("📄 已添加文档")

        system = st.session_state.system
        if system and system["kb"].doc_mappings:
            doc_items = list(system["kb"].doc_mappings.items())
            for idx, (md5, meta) in enumerate(doc_items, 1):
                with st.expander(f"{idx}. {os.path.basename(meta.get('original_path', '未知'))}", expanded=False):
                    st.text(f"MD5: {md5[:16]}...")
                    st.text(f"分块数: {meta.get('parts_count', 0)}")
                    st.text(f"路径: {meta.get('original_path', 'N/A')}")

                    # 删除按钮
                    if st.button(f"🗑️ 删除", key=f"delete_{md5}"):
                        async def delete_doc(doc_md5):
                            # 从知识库删除
                            await system["kb"].delete_document_by_md5(doc_md5)
                            # 从本地存储删除
                            try:
                                system["loader"].delete_by_md5(doc_md5)
                            except KeyError:
                                pass

                        try:
                            asyncio.run(delete_doc(md5))
                            st.success("✅ 删除成功！")
                            st.session_state.refresh_docs = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 删除失败: {str(e)}")
        else:
            st.info("暂无文档")

        # 刷新按钮
        if st.button("🔄 刷新列表"):
            st.rerun()

    # 主界面 - 对话区域
    st.header("💬 对话")

    # 显示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 输入框
    if question := st.chat_input("请输入你的问题...", disabled=st.session_state.is_processing):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": question})

        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(question)

        # 处理回答
        st.session_state.is_processing = True

        with st.chat_message("assistant"):
            # 流式输出容器
            response_container = st.empty()
            full_response = ""

            with st.spinner("🤔 思考中..."):
                try:
                    # 运行查询
                    answer = asyncio.run(query_agent(question))

                    # 模拟流式输出（实际可改造智能体支持真流式）
                    import time
                    for char in answer:
                        full_response += char
                        response_container.markdown(full_response + "▌")
                        time.sleep(0.01)  # 模拟打字效果

                    response_container.markdown(full_response)

                except Exception as e:
                    st.error(f"❌ 查询失败: {str(e)}")
                    full_response = f"查询失败: {str(e)}"

            # 保存回答
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

        st.session_state.is_processing = False
        st.rerun()


if __name__ == "__main__":
    main()
