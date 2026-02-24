#!/usr/bin/env python3
"""
RAG 系统主程序 - 交互式菜单
"""
import os
import sys
from pathlib import Path
import asyncio

# 支持直接运行此文件
if __name__ == "__main__" and __package__ is None:
    # 当直接运行时，添加父目录到 sys.path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
    from rag_knowledge_base.data.data_loader import DataLoader
    from rag_knowledge_base.agents.rag_agent import SpecializedRAGAgent
else:
    # 当作为模块导入时，使用相对导入
    from .rag_knowledge import RAGKnowledgeBase
    from .data.data_loader import DataLoader
    from .agents.rag_agent import SpecializedRAGAgent

class SimpleRAGSystem:
    """简化版RAG系统"""

    def __init__(self):
        # 检查是否使用 Docker Qdrant
        # 优先从环境变量读取，如果没有则检测本地 Qdrant 是否运行
        qdrant_url = os.getenv("QDRANT_URL")
        # if not qdrant_url:
        #     # 检测 localhost:6333 是否可用
        #     import urllib.request
        #     try:
        #         urllib.request.urlopen("http://localhost:6333/healthz", timeout=2)
        #         qdrant_url = "http://localhost:6333"
        #         print("检测到本地 Qdrant 服务运行中")
        #     except:
        #         pass

        if qdrant_url:
            print(f"使用 Docker Qdrant: {qdrant_url}")
            persist_path = None  # 使用远程 Qdrant 时不需要本地路径
        else:
            print("使用本地文件存储")
            persist_path = "./persist_data"  # 本地持久化路径

        self.kb = RAGKnowledgeBase(
            embedding_model="dashscope",
            model_name="text-embedding-v4",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            persist_path=persist_path,
            qdrant_url=qdrant_url
        )
        self.loader = DataLoader(data_dir="./data/documents")
        self.agent = SpecializedRAGAgent(name="RAG_Agent", knowledge_base=self.kb, score_threshold=0.1)
    
    async def add_documents(self, path: str) -> None:
        """添加文档（异步，可在已有事件循环中调用）。"""
        if os.path.isfile(path):
            print(f"📄 正在加载文件: {os.path.basename(path)}...")
            success, processed = self.loader.load_file(path)
            if success and processed:
                print(f"✓ 文件加载成功，正在添加到知识库...")
                try:
                    await self.kb.add_processed_document_from_dataloader(processed, overwrite=True)
                    print("✓ 文档添加成功")
                except Exception as e:
                    print(f"✗ 添加文档失败: {str(e)}")
            else:
                print(f"✗ 文件加载失败")
        elif os.path.isdir(path):
            print(f"📁 正在加载目录: {path}...")
            stats = self.loader.load_directory(path)
            for file_info in stats['loaded_files']:
                try:
                    await self.kb.add_processed_document_from_dataloader(file_info['processed'], overwrite=True)
                except Exception as e:
                    print(f"✗ 添加文档失败: {str(e)}")
            print(f"✓ 批量添加完成: {stats['successfully_loaded']} 个文件")
        else:
            print(f"✗ 路径不存在或不是文件/目录: {path}")

    async def delete_documents_interactive(self) -> None:
        """Interactive deletion: list available docs and delete selected ones."""
        if not self.kb.doc_mappings:
            print("当前没有可删除的文档。")
            return

        items = list(self.kb.doc_mappings.items())
        print("可删除的文档:")
        for idx, (md5, meta) in enumerate(items, start=1):
            print(f"{idx}. MD5: {md5} | 原始路径: {meta.get('original_path')} | parts: {meta.get('parts_count')}")

        sel = input("输入要删除的序号（逗号分隔），或输入 all: ").strip()
        targets = []
        if sel.lower() == 'all':
            targets = [md5 for md5, _ in items]
        else:
            try:
                idxs = [int(x.strip()) for x in sel.split(',') if x.strip()]
                for i in idxs:
                    if 1 <= i <= len(items):
                        targets.append(items[i-1][0])
            except Exception:
                print("输入无效。取消操作。")
                return

        for md5 in targets:
            try:
                print(f"正在从知识库删除 MD5={md5} ...")
                await self.kb.delete_document_by_md5(md5)
                print(f"正在删除处理文件与原始存储 for MD5={md5} ...")
                try:
                    self.loader.delete_by_md5(md5)
                except KeyError:
                    print("元数据中未找到对应条目或已被移除")
                print(f"已删除 {md5}")
            except Exception as e:
                print(f"删除 {md5} 失败: {e}")
    
    async def query(self, question: str) -> str:
        """查询知识库。"""
        from agentscope.message import Msg
        msg = Msg(name="User", content=question, role="user")
        response = await self.agent(msg)
        return response.content
    
    def stats(self):
        """显示统计信息"""
        stats = self.loader.get_statistics()
        print(f"管理文件: {stats['total_files']} 个")
        print(f"存储大小: {stats['total_size']} 字节")

async def main_async() -> None:
    """主流程（异步，全程使用 await，仅入口处使用一次 asyncio.run）。"""
    system = SimpleRAGSystem()

    while True:
        print("\n1. 添加文档  2. 查询  3. 统计  4. 删除文档  5. Web界面  6. 退出")
        choice = input("选择: ").strip()

        if choice == "1":
            path = input("文档路径: ").strip()
            if os.path.exists(path):
                await system.add_documents(path)
            else:
                print("路径不存在")

        elif choice == "2":
            question = input("问题: ").strip()
            if question:
                answer = await system.query(question)
                print(f"\n回答: {answer}")

        elif choice == "3":
            system.stats()

        elif choice == "4":
            await system.delete_documents_interactive()
        elif choice == "5":
            import subprocess
            print("\n🚀 启动 Web 界面...")
            print("📍 访问地址: http://localhost:8501")
            print("⏳ 正在启动 Streamlit...")
            try:
                subprocess.Popen(
                    ["streamlit", "run", "app.py", "--server.port=8501"],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                print("✅ Web 界面已启动，请在浏览器中访问 http://localhost:8501")
            except FileNotFoundError:
                print("❌ 未找到 streamlit，请先安装: pip install streamlit")
        elif choice == "6":
            break


if __name__ == "__main__":
    asyncio.run(main_async())