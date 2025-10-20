#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试BaseAgent模块导入
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def test_base_agent_import():
    """测试BaseAgent类导入"""
    try:
        from apps.backend.src.agents.base_agent import BaseAgent
        print("✅ BaseAgent导入成功")
        return True
    except ImportError as e:
        print(f"❌ BaseAgent导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入时发生未知错误: {e}")
        return False

if __name__ == "__main__":
    print("测试BaseAgent模块导入...")
    success = test_base_agent_import()
    if success:
        print("🎉 所有测试通过!")
    else:
        print("💥 测试失败!")
    sys.exit(0 if success else 1)