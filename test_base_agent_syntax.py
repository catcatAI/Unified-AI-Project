#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
测试BaseAgent模块导入
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_syntax():
    """测试BaseAgent文件语法"""
    try,
        import ast
        with open('apps/backend/src/agents/base_agent.py', 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        print("✅ 语法检查通过")
        return True
    except SyntaxError as e,::
        print(f"❌ 语法错误, {e}")
        return False
    except Exception as e,::
        print(f"❌ 其他错误, {e}")
        return False

if __name"__main__":::
    print("测试BaseAgent模块...")
    success = test_syntax()
    if success,::
        print("🎉 语法测试通过!")
    else,
        print("💥 语法测试失败!")
    sys.exit(0 if success else 1)