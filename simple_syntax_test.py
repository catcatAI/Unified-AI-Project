#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
简单的语法检查测试
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, '.')

def test_syntax():
    """测试语法"""
    tests_passed = 0
    tests_failed = 0
    
    # 测试1, 语法检查apps/backend/src/agents/base_agent.py()
    try,
        import ast
        with open('apps/backend/src/agents/base_agent.py', 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        print("✅ 测试1通过, apps/backend/src/agents/base_agent.py 语法正确")
        tests_passed += 1
    except Exception as e,::
        print(f"❌ 测试1失败, apps/backend/src/agents/base_agent.py 语法错误 - {e}")
        tests_failed += 1
    
    # 测试2, 语法检查apps/backend/src/ai/agents/base/base_agent.py()
    try,
        import ast
        with open('apps/backend/src/ai/agents/base/base_agent.py', 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        print("✅ 测试2通过, apps/backend/src/ai/agents/base/base_agent.py 语法正确")
        tests_passed += 1
    except Exception as e,::
        print(f"❌ 测试2失败, apps/backend/src/ai/agents/base/base_agent.py 语法错误 - {e}")
        tests_failed += 1
    
    print(f"\n📊 测试结果, {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed=0

if __name"__main__":::
    print("🔧 开始语法检查测试...")
    success = test_syntax()
    if success,::
        print("🎉 所有测试通过!")
    else,
        print("💥 部分测试失败!")
    sys.exit(0 if success else 1)