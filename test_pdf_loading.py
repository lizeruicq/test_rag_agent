#!/usr/bin/env python3
"""
测试 PDF 加载功能的诊断脚本
"""
import os
import sys
from pathlib import Path

# 支持直接运行此文件
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent))
    from rag_knowledge_base.utils.document_readers import PdfReader
    from rag_knowledge_base.data.data_loader import DataLoader
else:
    from .rag_knowledge_base.utils.document_readers import PdfReader
    from .rag_knowledge_base.data.data_loader import DataLoader


def test_pdf_reading(pdf_path):
    """测试 PDF 读取"""
    print(f"🧪 测试 PDF 读取: {pdf_path}")
    print("-" * 50)
    
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return False
    
    try:
        print("📖 正在读取 PDF 文件...")
        reader = PdfReader()
        documents = reader.read(pdf_path)
        
        print(f"✓ 成功读取 PDF")
        print(f"  - 文本块数: {len(documents)}")
        
        if documents:
            print(f"  - 第一个文本块长度: {len(documents[0]['content'])} 字符")
            print(f"  - 第一个文本块来源: {documents[0]['source']}")
            print(f"  - 第一个文本块内容预览: {documents[0]['content'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loader(pdf_path):
    """测试数据加载器"""
    print(f"\n🧪 测试数据加载器: {pdf_path}")
    print("-" * 50)
    
    try:
        loader = DataLoader(data_dir="./data/documents")
        print("✓ 数据加载器初始化成功")
        
        print("📄 正在加载文件...")
        success, processed_path = loader.load_file(pdf_path)
        
        if success:
            print(f"✓ 文件加载成功")
            print(f"  - 处理后的文件路径: {processed_path}")
            
            # 检查处理后的文件
            if os.path.exists(processed_path):
                import json
                with open(processed_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  - 文本块数: {data['document_count']}")
                print(f"✓ 处理后的文件已保存")
            
            return True
        else:
            print(f"❌ 文件加载失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    pdf_path = "/Volumes/EAGET/test_agent/example.pdf"
    
    print("=" * 50)
    print("PDF 加载诊断工具")
    print("=" * 50)
    
    # 测试 PDF 读取
    pdf_ok = test_pdf_reading(pdf_path)
    
    # 测试数据加载器
    if pdf_ok:
        loader_ok = test_data_loader(pdf_path)
    
    print("\n" + "=" * 50)
    print("诊断完成")
    print("=" * 50)

