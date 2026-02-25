#!/usr/bin/env python3
"""
Streamlit 前端 - RAG 知识库问答界面（带机器人动画）
"""
import os
import sys
import asyncio
import time
import streamlit as st
from streamlit_lottie import st_lottie
import requests

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.data.data_loader import DataLoader
from rag_knowledge_base.agents.rag_agent import SpecializedRAGAgent


# ==================== 异步处理辅助函数 ====================
def run_async(coro):
    """在 Streamlit 中安全地运行异步协程。"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# ==================== 机器人动画配置 ====================
# 使用在线 Lottie 动画 URL
ROBOT_ANIMATIONS = {
    "idle": "https://lottie.host/4b880451-8277-412b-9254-0e70f55119b7/1G8r4q3z8i.json",  # 静止
    "thinking": "https://lottie.host/c24c1e6c-99e6-4539-9b69-6e4c5c3e5d4e/2J9s5r4z9j.json",  # 思考/运行
    "speaking": "https://lottie.host/a35d2f7d-0aa7-5240-0c7a-7f5d6d4f6e5f/3K0t6s5z0k.json",  # 说话
}

# 如果网络不可用，使用简单的 CSS 动画作为备选
CSS_ROBOT = """
<style>
.robot-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
}

.robot {
    width: 120px;
    height: 120px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    position: relative;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

/* 眼睛 */
.robot::before {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    background: #fff;
    border-radius: 50%;
    top: 30px;
    left: 25px;
    box-shadow: 50px 0 0 #fff;
    animation: blink 3s infinite;
}

/* 嘴巴 */
.robot::after {
    content: '';
    position: absolute;
    width: 40px;
    height: 10px;
    background: #fff;
    border-radius: 5px;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
}

/* 静止状态 */
.robot.idle {
    animation: float 3s ease-in-out infinite;
}

/* 思考状态 */
.robot.thinking {
    animation: shake 0.5s ease-in-out infinite, glow 1s ease-in-out infinite alternate;
}

/* 说话状态 */
.robot.speaking {
    animation: bounce 0.3s ease-in-out infinite;
}
.robot.speaking::after {
    animation: speak 0.3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

@keyframes shake {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-5deg); }
    75% { transform: rotate(5deg); }
}

@keyframes glow {
    from { box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5); }
    to { box-shadow: 0 10px 40px rgba(102, 126, 234, 0.8), 0 0 20px rgba(255,255,255,0.5); }
}

@keyframes bounce {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes blink {
    0%, 90%, 100% { transform: scaleY(1); }
    95% { transform: scaleY(0.1); }
}

@keyframes speak {
    0%, 100% { width: 40px; height: 10px; }
    50% { width: 50px; height: 15px; }
}

.robot-status {
    text-align: center;
    margin-top: 10px;
    font-size: 14px;
    color: #666;
}
</style>
"""


def load_lottie_url(url: str):
    """加载 Lottie 动画"""
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def render_robot(status: str = "idle"):
    """渲染机器人动画"""
    # 先注入 CSS
    st.markdown(CSS_ROBOT, unsafe_allow_html=True)

    # 状态文本
    status_text = {
        "idle": "🟢 待机中",
        "thinking": "🤔 思考中...",
        "speaking": "💬 回复中..."
    }.get(status, "🟢 待机中")

    # 使用 CSS 动画
    html = f"""
    <div class="robot-container">
        <div class="robot {status}"></div>
    </div>
    <div class="robot-status">{status_text}</div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ==================== 页面配置 ====================
st.set_page_config(
    page_title="RAG 知识库问答",
    page_icon="🤖",
    layout="wide"
)

# ==================== Session State ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "system" not in st.session_state:
    st.session_state.system = None

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "robot_status" not in st.session_state:
    st.session_state.robot_status = "idle"

if "refresh_docs" not in st.session_state:
    st.session_state.refresh_docs = False


# ==================== 初始化系统 ====================
def init_system():
    """Initialize RAG system with local Ollama models."""
    if st.session_state.system is None:
        with st.spinner("正在初始化知识库..."):
            persist_path = "./persist_data"

            # Ollama server configuration
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

            # Qdrant URL (optional, for Docker Qdrant service)
            qdrant_url = os.getenv("QDRANT_URL")

            # Initialize with local Ollama models
            kb = RAGKnowledgeBase(
                model_name="qwen3-embedding:4b",
                persist_path=persist_path,
                ollama_host=ollama_host,
                dimensions=1024,
                qdrant_url=qdrant_url
            )

            loader = DataLoader(data_dir="./data/documents")
            agent = SpecializedRAGAgent(
                name="RAG_Agent",
                knowledge_base=kb,
                model_name="qwen3:4b",
                ollama_host=ollama_host,
                score_threshold=0.1
            )

            st.session_state.system = {
                "kb": kb,
                "loader": loader,
                "agent": agent
            }


# ==================== 查询智能体 ====================
async def query_agent(question: str) -> str:
    """查询智能体"""
    from agentscope.message import Msg

    system = st.session_state.system
    if system is None:
        return "系统未初始化"

    msg = Msg(name="User", content=question, role="user")
    response = await system["agent"].reply(msg)

    # 处理不同类型的 content
    content = response.content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts)
    elif isinstance(content, dict):
        return content.get("text", str(content))
    else:
        return str(content)


# ==================== 主界面 ====================
def main():
    """主界面"""
    st.title("📚 RAG 知识库问答系统")
    st.markdown("---")

    # 初始化系统
    init_system()

    # ==================== 侧边栏 ====================
    with st.sidebar:
        # ===== 机器人动画区域 =====
        st.header("🤖 AI 助手")
        robot_container = st.container()
        with robot_container:
            render_robot(st.session_state.robot_status)

        st.markdown("---")

        # ===== 文档管理 =====
        st.header("📁 文档管理")

        # 上传文档
        uploaded_file = st.file_uploader(
            "上传文档",
            type=["txt", "pdf", "docx", "xlsx", "xls"],
            help="支持 TXT, PDF, DOCX, XLSX, XLS 格式"
        )

        if uploaded_file is not None:
            if st.button("📤 添加到知识库"):
                with st.spinner("正在处理文档..."):
                    file_path = f"./data/uploaded/{uploaded_file.name}"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

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
                        result = run_async(add_doc())
                        if result:
                            st.success(f"✅ {uploaded_file.name} 添加成功！")
                        else:
                            st.error("❌ 添加失败")
                    except Exception as e:
                        st.error(f"❌ 错误: {str(e)}")

        st.markdown("---")

        # 统计
        if st.button("📊 刷新统计"):
            system = st.session_state.system
            stats = system["loader"].get_statistics()
            st.metric("管理文件", stats.get("total_files", 0))
            st.metric("存储大小", f"{stats.get('total_size', 0) / 1024:.1f} KB")

        st.markdown("---")

        # 已添加文档列表
        st.subheader("📄 已添加文档")

        system = st.session_state.system
        if system and system["kb"].doc_mappings:
            doc_items = list(system["kb"].doc_mappings.items())
            for idx, (md5, meta) in enumerate(doc_items, 1):
                with st.expander(f"{idx}. {os.path.basename(meta.get('original_path', '未知'))}", expanded=False):
                    st.text(f"MD5: {md5[:16]}...")
                    st.text(f"分块数: {meta.get('parts_count', 0)}")
                    st.text(f"路径: {meta.get('original_path', 'N/A')}")

                    if st.button(f"🗑️ 删除", key=f"delete_{md5}"):
                        async def delete_doc(doc_md5):
                            await system["kb"].delete_document_by_md5(doc_md5)
                            try:
                                system["loader"].delete_by_md5(doc_md5)
                            except KeyError:
                                pass

                        try:
                            run_async(delete_doc(md5))
                            st.success("✅ 删除成功！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ 删除失败: {str(e)}")
        else:
            st.info("暂无文档")

        if st.button("🔄 刷新列表"):
            st.rerun()

    # ==================== 对话区域 ====================
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

        # 设置机器人状态为思考中
        st.session_state.is_processing = True
        st.session_state.robot_status = "thinking"
        st.rerun()

    # 处理回答（在 rerun 后执行）
    if st.session_state.is_processing and st.session_state.messages:
        last_message = st.session_state.messages[-1]

        if last_message["role"] == "user":
            # 如果还是思考状态，先执行查询
            if st.session_state.robot_status == "thinking":
                try:
                    # 运行查询
                    answer = run_async(query_agent(last_message["content"]))
                    st.session_state.current_answer = answer
                    # 切换到说话状态并刷新，让侧边栏机器人更新
                    st.session_state.robot_status = "speaking"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 查询失败: {str(e)}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"查询失败: {str(e)}"
                    })
                    st.session_state.is_processing = False
                    st.session_state.robot_status = "idle"
                    st.rerun()

            # 说话状态，进行流式输出
            with st.chat_message("assistant"):
                response_container = st.empty()
                full_response = ""
                answer = st.session_state.get("current_answer", "")

                # 流式输出
                for char in answer:
                    full_response += char
                    response_container.markdown(full_response + "▌")
                    time.sleep(0.02)

                response_container.markdown(full_response)

                # 清理临时状态并保存回答
                if "current_answer" in st.session_state:
                    del st.session_state.current_answer
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })

            # 恢复待机状态
            st.session_state.is_processing = False
            st.session_state.robot_status = "idle"
            st.rerun()


if __name__ == "__main__":
    main()
