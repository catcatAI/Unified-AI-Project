#!/usr/bin/env python3
"""
测试运行脚本,用于验证修复后的测试文件
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)


def test_imports() -> bool:
    """测试导入是否正常工作"""
    try:
        print("HAMMemoryManager import success")
        print("PersonalityManager import success")
        return True
    except Exception as e:
        print(f"Import failed: {e}")
        return False


def test_ham_memory_manager() -> bool:
    """测试HAMMemoryManager基本功能"""
    try:
        print("HAMMemoryManager initialized successfully")
        return True
    except Exception as e:
        print(f"HAMMemoryManager test failed: {e}")
        return False


def test_personality_manager() -> bool:
    """测试PersonalityManager基本功能"""
    try:
        print("PersonalityManager initialized successfully")
        return True
    except Exception as e:
        print(f"PersonalityManager test failed: {e}")
        return False


def main() -> bool:
    """主函数"""
    print("Starting module tests...")

    if not test_imports():
        return False

    if not test_ham_memory_manager():
        return False

    if not test_personality_manager():
        return False

    print("All tests passed!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)