#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试兼容性修复脚本
验证我们的兼容性修复是否有效
"""

import os
import sys

# 添加项目路径
project_root: str = os.path.dirname(os.path.abspath(__file__))
_ = sys.path.insert(0, project_root)
_ = sys.path.insert(0, os.path.join(project_root, 'apps', 'backend'))

def test_keras_availability() -> None:
    """测试Keras是否可用"""
    _ = print("测试Keras可用性...")
    try:
        from apps.backend.src.compat.transformers_compat import KERAS_AVAILABLE
        _ = print(f"✓ Keras可用性检查: {KERAS_AVAILABLE}")
        return KERAS_AVAILABLE
    except Exception as e:
        _ = print(f"✗ Keras可用性检查失败: {e}")
        return False

def test_safe_imports() -> None:
    """测试安全导入功能"""
    _ = print("\n测试安全导入功能...")
    
    # 测试SentenceTransformer安全导入
    try:
        from apps.backend.src.compat.transformers_compat import import_sentence_transformers
        SentenceTransformer, success = import_sentence_transformers()
        _ = print(f"✓ SentenceTransformer安全导入: {success}")
        if success:
            _ = print(f"  类型: {type(SentenceTransformer)}")
    except Exception as e:
        _ = print(f"✗ SentenceTransformer安全导入测试失败: {e}")
    
    # 测试Transformers pipeline安全导入
    try:
        from apps.backend.src.compat.transformers_compat import import_transformers_pipeline
        pipeline, success = import_transformers_pipeline()
        _ = print(f"✓ Transformers pipeline安全导入: {success}")
        if success:
            _ = print(f"  类型: {type(pipeline)}")
    except Exception as e:
        _ = print(f"✗ Transformers pipeline安全导入测试失败: {e}")

def test_rag_manager_import() -> None:
    """测试RAG管理器导入"""
    _ = print("\n测试RAG管理器导入...")
    try:
        # 测试AI RAG管理器
        from apps.backend.src.core_ai.rag.rag_manager import SENTENCE_TRANSFORMERS_AVAILABLE
        print(f"✓ AI RAG管理器导入成功: SENTENCE_TRANSFORMERS_AVAILABLE={SENTENCE_TRANSFORMERS_AVAILABLE}")
        
        # 测试Core AI RAG管理器
        from apps.backend.src.core_ai.rag.rag_manager import SENTENCE_TRANSFORMERS_AVAILABLE as core_avail
        print(f"✓ Core AI RAG管理器导入成功: SENTENCE_TRANSFORMERS_AVAILABLE={core_avail}")
    except Exception as e:
        _ = print(f"✗ RAG管理器导入测试失败: {e}")

def test_nlg_tool_import() -> None:
    """测试自然语言生成工具导入"""
    _ = print("\n测试自然语言生成工具导入...")
    try:
        # 测试核心工具
        from apps.backend.src.core.tools.natural_language_generation_tool import TRANSFORMERS_AVAILABLE as core_avail
        print(f"✓ 核心自然语言生成工具导入成功: TRANSFORMERS_AVAILABLE={core_avail}")
        
        # 测试工具
        from apps.backend.src.tools.natural_language_generation_tool import TRANSFORMERS_AVAILABLE as tools_avail
        print(f"✓ 自然语言生成工具导入成功: TRANSFORMERS_AVAILABLE={tools_avail}")
    except Exception as e:
        _ = print(f"✗ 自然语言生成工具导入测试失败: {e}")

def main() -> None:
    """主函数"""
    _ = print("开始测试兼容性修复...")
    _ = print(f"Python路径: {sys.executable}")
    _ = print(f"工作目录: {os.getcwd()}")
    
    # 设置环境变量
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    print(f"TF_USE_LEGACY_KERAS = {os.environ.get('TF_USE_LEGACY_KERAS', '未设置')}")
    
    # 运行测试
    _ = test_keras_availability()
    _ = test_safe_imports()
    _ = test_rag_manager_import()
    _ = test_nlg_tool_import()
    
    _ = print("\n测试完成!")

if __name__ == "__main__":
    _ = main()