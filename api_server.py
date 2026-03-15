#!/usr/bin/env python3
"""
FastAPI 后端 - 为 RPG 前端提供 API 服务
"""
import os
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
import shutil

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import sys
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
from rag_knowledge_base.data.data_loader import DataLoader
from rag_knowledge_base.agents.rag_agent import SpecializedRAGAgent
from agentscope.message import Msg

# ============== 全局状态 ==============
system_state = {
    "kb": None,
    "loader": None,
    "agent": None,
    "initialized": False,
}

# ============== 命令行参数 ==============
parser = argparse.ArgumentParser(description="RPG Chat API Server")
parser.add_argument(
    "--dev",
    action="store_true",
    help="开发模式：不构建前端，仅提供 API 服务"
)
parser.add_argument(
    "--build",
    action="store_true",
    help="构建前端后启动（生产模式）"
)
args = parser.parse_args()

# 默认生产模式（构建前端）
DEV_MODE = args.dev
BUILD_FRONTEND = args.build or not args.dev  # 默认构建，--dev 时不构建

# ============== 数据模型 ==============


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None


class DocumentInfo(BaseModel):
    id: str
    name: str
    md5: str
    partsCount: int
    size: int
    uploadedAt: str


class DocumentStats(BaseModel):
    totalFiles: int
    totalSize: int


class UploadResponse(BaseModel):
    success: bool
    message: str


# ============== 前端构建 ==============

def build_frontend():
    """构建前端静态文件"""
    frontend_dir = os.path.join(os.path.dirname(__file__), "rpg-frontend")
    dist_dir = os.path.join(frontend_dir, "dist")

    # 如果已经构建过，跳过
    if os.path.exists(dist_dir) and os.path.exists(os.path.join(dist_dir, "index.html")):
        print("📦 前端已构建，跳过构建步骤")
        return dist_dir

    # 检查是否有 node_modules
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("📦 安装前端依赖...")
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 前端依赖安装失败: {e}")
            return None
        except FileNotFoundError:
            print("⚠️ 未找到 npm，请安装 Node.js")
            return None

    print("🔨 构建前端...")
    try:
        subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            check=True,
            capture_output=True,
        )
        print("✅ 前端构建完成")
        return dist_dir
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 前端构建失败: {e}")
        return None


# ============== 生命周期管理 ==============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 正在初始化 RAG 系统...")
    await init_system()
    print("✅ 系统初始化完成")

    # 仅在非开发模式下构建前端
    if BUILD_FRONTEND:
        dist_dir = build_frontend()
        if dist_dir:
            print(f"📦 前端资源路径: {dist_dir}")
            # 设置静态文件服务
            setup_static_files()
    else:
        print("🔧 开发模式：不构建前端，仅提供 API 服务")
        print("   请运行: cd rpg-frontend && npm run dev")

    yield

    # 关闭时清理
    print("🛑 正在关闭系统...")


async def init_system():
    """初始化 RAG 系统"""
    if system_state["initialized"]:
        return

    qdrant_url = os.getenv("QDRANT_URL")
    persist_path = None if qdrant_url else "./persist_data"

    kb = RAGKnowledgeBase(
        embedding_model="dashscope",
        model_name="text-embedding-v4",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        persist_path=persist_path,
        qdrant_url=qdrant_url,
    )

    loader = DataLoader(data_dir="./data/documents")

    agent = SpecializedRAGAgent(
        name="RAG_Agent",
        knowledge_base=kb,
        score_threshold=0.1,
    )

    system_state["kb"] = kb
    system_state["loader"] = loader
    system_state["agent"] = agent
    system_state["initialized"] = True


# ============== FastAPI 应用 ==============

app = FastAPI(
    title="RPG Chat API",
    description="RAG 知识库问答系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
# 开发模式允许 Vite 端口，生产模式允许所有
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"] if BUILD_FRONTEND else ["*"]
if DEV_MODE:
    ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== API 端点 ==============


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口"""
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="系统未初始化")

    try:
        agent = system_state["agent"]
        msg = Msg(name="User", content=request.message, role="user")
        response = await agent(msg)

        # 处理不同类型的 content
        content = response.content
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
                elif isinstance(item, str):
                    texts.append(item)
            answer = "\n".join(texts)
        elif isinstance(content, dict):
            answer = content.get("text", str(content))
        else:
            answer = str(content)

        return ChatResponse(answer=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传文档"""
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="系统未初始化")

    # 检查文件类型
    allowed_types = [
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ]

    if file.content_type not in allowed_types:
        return UploadResponse(
            success=False,
            message=f"不支持的文件类型: {file.content_type}",
        )

    try:
        # 保存文件
        upload_dir = "./data/uploaded"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 加载到知识库
        loader = system_state["loader"]
        kb = system_state["kb"]

        success, processed = loader.load_file(file_path)
        if success and processed:
            await kb.add_processed_document_from_dataloader(
                processed, overwrite=True
            )
            return UploadResponse(
                success=True,
                message=f"✅ {file.filename} 添加成功！",
            )
        else:
            return UploadResponse(
                success=False,
                message="❌ 文档处理失败",
            )

    except Exception as e:
        return UploadResponse(
            success=False,
            message=f"❌ 错误: {str(e)}",
        )


@app.get("/api/docs", response_model=List[DocumentInfo])
async def list_documents():
    """获取文档列表"""
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="系统未初始化")

    kb = system_state["kb"]
    documents = []

    if kb.doc_mappings:
        for md5, meta in kb.doc_mappings.items():
            original_path = meta.get("original_path", "未知")
            documents.append(
                DocumentInfo(
                    id=md5,
                    name=os.path.basename(original_path),
                    md5=md5,
                    partsCount=meta.get("parts_count", 0),
                    size=meta.get("file_size", 0),
                    uploadedAt=meta.get("uploaded_at", ""),
                )
            )

    return documents


@app.delete("/api/docs/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="系统未初始化")

    try:
        kb = system_state["kb"]
        loader = system_state["loader"]

        await kb.delete_document_by_md5(doc_id)
        try:
            loader.delete_by_md5(doc_id)
        except KeyError:
            pass

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@app.get("/api/stats", response_model=DocumentStats)
async def get_stats():
    """获取统计信息"""
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="系统未初始化")

    loader = system_state["loader"]
    stats = loader.get_statistics()

    return DocumentStats(
        totalFiles=stats.get("total_files", 0),
        totalSize=stats.get("total_size", 0),
    )


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "initialized": system_state["initialized"],
    }


# ============== 静态文件服务 (生产模式) ==============

def setup_static_files():
    """配置静态文件服务"""
    dist_dir = os.path.join(os.path.dirname(__file__), "rpg-frontend", "dist")

    if os.path.exists(dist_dir):
        # 挂载静态文件目录
        app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

        # 首页路由 - 返回 index.html
        @app.get("/")
        async def serve_index():
            return FileResponse(os.path.join(dist_dir, "index.html"))

        # 所有其他路由也返回 index.html (支持前端路由)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # API 路由不处理
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not Found")

            index_file = os.path.join(dist_dir, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="Frontend not built")

        print(f"📦 静态文件服务已配置: {dist_dir}")
    else:
        print("⚠️ 前端未构建，运行开发模式")
        print("   开发模式: cd rpg-frontend && npm run dev")


# ============== 主入口 ==============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
