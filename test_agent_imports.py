#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试专门化代理导入BaseAgent
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试专门化代理导入"""
    tests_passed = 0
    tests_failed = 0
    
    # 测试1: 导入CreativeWritingAgent
    try:
        from apps.backend.src.ai.agents.specialized.creative_writing_agent import CreativeWritingAgent
        print("✅ 测试1通过: 成功导入CreativeWritingAgent")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试1失败: 无法导入CreativeWritingAgent - {e}")
        tests_failed += 1
    
    # 测试2: 导入WebSearchAgent
    try:
        from apps.backend.src.ai.agents.specialized.web_search_agent import WebSearchAgent
        print("✅ 测试2通过: 成功导入WebSearchAgent")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试2失败: 无法导入WebSearchAgent - {e}")
        tests_failed += 1
    
    # 测试3: 导入ai/agents模块
    try:
        from apps.backend.src.ai.agents import BaseAgent, CreativeWritingAgent, WebSearchAgent
        print("✅ 测试3通过: 成功导入apps.backend.src.ai.agents")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试3失败: 无法导入apps.backend.src.ai.agents - {e}")
        tests_failed += 1
    
    print(f"\n📊 测试结果: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0

if __name__ == "__main__":
    print("🔧 开始专门化代理导入测试...")
    success = test_imports()
    if success:
        print("🎉 所有测试通过!")
    else:
        print("💥 部分测试失败!")
    sys.exit(0 if success else 1)