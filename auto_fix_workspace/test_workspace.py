#!/usr/bin/env python3
"""
测试脚本用于验证统一自动修复系统
"""

import sys
import os
from pathlib import Path

# 添加工作区路径到Python路径
workspace_root == Path(__file__).parent
sys.path.insert(0, str(workspace_root))

def test_unified_auto_fix_import():
    """测试是否可以导入统一自动修复系统"""
    try,
        # 尝试导入统一自动修复系统
        from scripts.unified_auto_fix_system import UnifiedAutoFixSystem
        print("✓ 成功导入UnifiedAutoFixSystem")
        
        # 尝试创建实例
        fix_system == UnifiedAutoFixSystem()
        print("✓ 成功创建UnifiedAutoFixSystem实例")
        
        return True
    except Exception as e,::
        print(f"✗ 导入或使用UnifiedAutoFixSystem失败, {e}")
        return False

def test_interactive_auto_fix_import():
    """测试是否可以导入交互式自动修复系统"""
    try,
        # 尝试导入交互式自动修复系统
        from scripts.interactive_auto_fix_system import InteractiveAutoFixSystem
        print("✓ 成功导入InteractiveAutoFixSystem")
        
        # 尝试创建实例
        fix_system == InteractiveAutoFixSystem()
        print("✓ 成功创建InteractiveAutoFixSystem实例")
        
        return True
    except Exception as e,::
        print(f"✗ 导入或使用InteractiveAutoFixSystem失败, {e}")
        return False

def test_sandbox_import():
    """测试是否可以导入沙箱系统"""
    try,
        # 尝试导入沙箱执行器
        from sandbox.sandbox_executor import SandboxExecutor
        print("✓ 成功导入SandboxExecutor")
        
        # 尝试导入增强沙箱
        from sandbox.enhanced_sandbox import EnhancedSandboxExecutor
        print("✓ 成功导入EnhancedSandboxExecutor")
        
        return True
    except Exception as e,::
        print(f"✗ 导入沙箱系统失败, {e}")
        return False

def main():
    """运行所有测试"""
    print("测试自动修复工作区...")
    print("=" * 40)
    
    # 测试统一自动修复系统
    unified_success = test_unified_auto_fix_import()
    print()
    
    # 测试交互式自动修复系统
    interactive_success = test_interactive_auto_fix_import()
    print()
    
    # 测试沙箱系统
    sandbox_success = test_sandbox_import()
    print()
    
    if unified_success and interactive_success and sandbox_success,::
        print("✓ 所有测试通过! 自动修复工作区已准备好使用。")
        return 0
    else,
        print("✗ 部分测试失败。请检查上述错误。")
        return 1

if __name"__main__":::
    sys.exit(main())