#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统性测试BaseAgent模块导入路径
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """测试所有相关导入"""
    tests_passed = 0
    tests_failed = 0
    
    # 测试1: 导入BaseAgent (ai/agents/base/base_agent.py)
    try:
        from apps.backend.src.ai.agents.base.base_agent import BaseAgent
        print("✅ 测试1通过: 成功导入apps.backend.src.ai.agents.base.base_agent.BaseAgent")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试1失败: 无法导入apps.backend.src.ai.agents.base.base_agent.BaseAgent - {e}")
        tests_failed += 1
    
    # 测试2: 导入BaseAgent (agents/base_agent.py)
    try:
        from apps.backend.src.agents.base_agent import BaseAgent
        print("✅ 测试2通过: 成功导入apps.backend.src.agents.base_agent.BaseAgent")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试2失败: 无法导入apps.backend.src.agents.base_agent.BaseAgent - {e}")
        tests_failed += 1
    
    # 测试3: 导入ai/agents/__init__.py
    try:
        from apps.backend.src.ai.agents import BaseAgent, CreativeWritingAgent, WebSearchAgent
        print("✅ 测试3通过: 成功导入apps.backend.src.ai.agents")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试3失败: 无法导入apps.backend.src.ai.agents - {e}")
        tests_failed += 1
    
    # 测试4: 导入CreativeWritingAgent
    try:
        from apps.backend.src.ai.agents.specialized.creative_writing_agent import CreativeWritingAgent
        print("✅ 测试4通过: 成功导入CreativeWritingAgent")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试4失败: 无法导入CreativeWritingAgent - {e}")
        tests_failed += 1
    
    # 测试5: 语法检查apps/backend/src/agents/base_agent.py
    try:
        import ast
        with open('apps/backend/src/agents/base_agent.py', 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print("✅ 测试5通过: apps/backend/src/agents/base_agent.py 语法正确")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试5失败: apps/backend/src/agents/base_agent.py 语法错误 - {e}")
        tests_failed += 1
    
    # 测试6: 语法检查apps/backend/src/ai/agents/base/base_agent.py
    try:
        import ast
        with open('apps/backend/src/ai/agents/base/base_agent.py', 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print("✅ 测试6通过: apps/backend/src/ai/agents/base/base_agent.py 语法正确")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 测试6失败: apps/backend/src/ai/agents/base/base_agent.py 语法错误 - {e}")
        tests_failed += 1
    
    print(f"\n📊 测试结果: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0

if __name__ == "__main__":
    print("🔧 开始系统性导入路径测试...")
    success = test_imports()
    if success:
        print("🎉 所有测试通过!")
    else:
        print("💥 部分测试失败!")
    sys.exit(0 if success else 1)