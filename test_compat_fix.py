#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试兼容性修复脚本
验证我们的兼容性修复是否有效
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'apps', 'backend'))

def test_keras_availability():
    """测试Keras是否可用"""
    print("测试Keras可用性...")
    try:
        from apps.backend.src.compat.transformers_compat import KERAS_AVAILABLE
        print(f"✓ Keras可用性检查: {KERAS_AVAILABLE}")
        return KERAS_AVAILABLE
    except Exception as e:
        print(f"✗ Keras可用性检查失败: {e}")
        return False

def test_safe_imports():
    """测试安全导入功能"""
    print("\n测试安全导入功能...")
    
    # 测试SentenceTransformer安全导入
    try:
        from apps.backend.src.compat.transformers_compat import import_sentence_transformers
        SentenceTransformer, success = import_sentence_transformers()
        print(f"✓ SentenceTransformer安全导入: {success}")
        if success:
            print(f"  类型: {type(SentenceTransformer)}")
    except Exception as e:
        print(f"✗ SentenceTransformer安全导入测试失败: {e}")
    
    # 测试Transformers pipeline安全导入
    try:
        from apps.backend.src.compat.transformers_compat import import_transformers_pipeline
        pipeline, success = import_transformers_pipeline()
        print(f"✓ Transformers pipeline安全导入: {success}")
        if success:
            print(f"  类型: {type(pipeline)}")
    except Exception as e:
        print(f"✗ Transformers pipeline安全导入测试失败: {e}")

def test_rag_manager_import():
    """测试RAG管理器导入"""
    print("\n测试RAG管理器导入...")
    try:
        # 测试AI RAG管理器
        from apps.backend.src.ai.rag.rag_manager import SENTENCE_TRANSFORMERS_AVAILABLE
        print(f"✓ AI RAG管理器导入成功: SENTENCE_TRANSFORMERS_AVAILABLE={SENTENCE_TRANSFORMERS_AVAILABLE}")
        
        # 测试Core AI RAG管理器
        from apps.backend.src.core_ai.rag.rag_manager import SENTENCE_TRANSFORMERS_AVAILABLE as core_avail
        print(f"✓ Core AI RAG管理器导入成功: SENTENCE_TRANSFORMERS_AVAILABLE={core_avail}")
    except Exception as e:
        print(f"✗ RAG管理器导入测试失败: {e}")

def test_nlg_tool_import():
    """测试自然语言生成工具导入"""
    print("\n测试自然语言生成工具导入...")
    try:
        # 测试核心工具
        from apps.backend.src.core.tools.natural_language_generation_tool import TRANSFORMERS_AVAILABLE as core_avail
        print(f"✓ 核心自然语言生成工具导入成功: TRANSFORMERS_AVAILABLE={core_avail}")
        
        # 测试工具
        from apps.backend.src.tools.natural_language_generation_tool import TRANSFORMERS_AVAILABLE as tools_avail
        print(f"✓ 自然语言生成工具导入成功: TRANSFORMERS_AVAILABLE={tools_avail}")
    except Exception as e:
        print(f"✗ 自然语言生成工具导入测试失败: {e}")

def main():
    """主函数"""
    print("开始测试兼容性修复...")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")
    
    # 设置环境变量
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    print(f"TF_USE_LEGACY_KERAS = {os.environ.get('TF_USE_LEGACY_KERAS', '未设置')}")
    
    # 运行测试
    test_keras_availability()
    test_safe_imports()
    test_rag_manager_import()
    test_nlg_tool_import()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()