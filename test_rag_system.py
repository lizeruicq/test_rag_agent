#!/usr/bin/env python3
"""
RAG 系统测试脚本
测试文档加载、知识库管理和智能体功能
"""
import os
import tempfile
from pathlib import Path

def test_document_readers():
    """测试文档读取器"""
    print("\n" + "="*50)
    print("测试 1: 文档读取器")
    print("="*50)
    
    from rag_knowledge_base.utils.document_readers import (
        get_reader_for_file, TxtReader, PdfReader, DocxReader, ExcelReader
    )
    
    # 创建测试文本文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是一个测试文档。\n" * 100)
        txt_file = f.name
    
    try:
        # 测试 TXT 读取器
        reader = get_reader_for_file(txt_file)
        assert isinstance(reader, TxtReader), "应该返回 TxtReader"
        docs = reader.read(txt_file)
        assert len(docs) > 0, "应该读取到文档"
        print(f"✓ TXT 读取器: 成功读取 {len(docs)} 个文档块")
        
        # 测试不支持的格式
        try:
            get_reader_for_file("test.unknown")
            assert False, "应该抛出异常"
        except ValueError as e:
            print(f"✓ 不支持的格式检测: {str(e)}")
    finally:
        os.unlink(txt_file)


def test_data_loader():
    """测试数据加载器"""
    print("\n" + "="*50)
    print("测试 2: 数据加载器")
    print("="*50)
    
    from rag_knowledge_base.data.data_loader import DataLoader
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DataLoader(data_dir=tmpdir)
        
        # 创建测试文件
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("测试内容\n" * 50, encoding='utf-8')
        
        # 测试加载文件
        success, processed_path = loader.load_file(str(test_file))
        assert success, "文件加载应该成功"
        assert processed_path is not None, "应该返回处理后的文件路径"
        print(f"✓ 文件加载: 成功加载文件")
        
        # 测试重复检测
        success2, processed_path2 = loader.load_file(str(test_file))
        assert success2, "重复文件应该返回成功"
        assert processed_path2 == processed_path, "重复文件应该返回相同的路径"
        print(f"✓ 重复检测: 成功检测到重复文件")
        
        # 测试统计
        stats = loader.get_statistics()
        assert stats['total_files'] == 1, "应该有 1 个文件"
        print(f"✓ 统计信息: {stats}")


def test_rag_knowledge_base():
    """测试 RAG 知识库"""
    print("\n" + "="*50)
    print("测试 3: RAG 知识库")
    print("="*50)

    from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase

    # 检查 API 密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("⚠️  跳过知识库初始化测试（未设置 DASHSCOPE_API_KEY）")
        print("✓ 知识库类导入成功")
        return

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 初始化知识库
        kb = RAGKnowledgeBase(
            embedding_model="dashscope",
            model_name="text-embedding-v2",
            api_key=api_key,
            persist_path=tmpdir,
            recreate=True
        )
        print(f"✓ 知识库初始化: 成功")

        # 检查属性
        assert kb.collection_name == "rag_knowledge_base"
        assert kb.dimensions == 1024
        print(f"✓ 知识库配置: collection_name={kb.collection_name}, dimensions={kb.dimensions}")


def test_imports():
    """测试所有导入"""
    print("\n" + "="*50)
    print("测试 0: 模块导入")
    print("="*50)
    
    try:
        from rag_knowledge_base.rag_knowledge import RAGKnowledgeBase
        print("✓ RAGKnowledgeBase 导入成功")
        
        from rag_knowledge_base.data.data_loader import DataLoader
        print("✓ DataLoader 导入成功")
        
        from rag_knowledge_base.agents.rag_agent import SimpleRAGAgent, SpecializedRAGAgent
        print("✓ SimpleRAGAgent 导入成功")
        
        from rag_knowledge_base.utils.document_readers import (
            get_reader_for_file, TxtReader, PdfReader, DocxReader, ExcelReader
        )
        print("✓ 所有文档读取器导入成功")
        
        from rag_knowledge_base.main import SimpleRAGSystem
        print("✓ SimpleRAGSystem 导入成功")
        
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "="*50)
    print("RAG 系统测试")
    print("="*50)
    
    test_imports()
    test_document_readers()
    test_data_loader()
    test_rag_knowledge_base()
    
    print("\n" + "="*50)
    print("✓ 所有测试通过！")
    print("="*50)

