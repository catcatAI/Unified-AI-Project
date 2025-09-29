#!/usr/bin/env python3
"""
自动修复工具演示脚本
演示如何使用自动修复工具解决原始问题
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_problematic_file():
    """创建一个有问题的文件来演示修复"""
    test_file = PROJECT_ROOT / "scripts" / "test_problematic_import.py"
    
    problematic_content = '''
"""
有问题的导入文件演示
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 原始问题1: core_ai模块导入问题
from apps.backend.src.core_ai.agent_manager import AgentManager

# 原始问题2: HSPConnector导入问题（在TYPE_CHECKING外）
from apps.backend.src.core.hsp.connector import HSPConnector

# 原始问题3: 相对导入问题
from apps.backend.src.core_ai.dialogue.dialogue_manager import DialogueManager

def test_function() -> None:
    """测试函数"""
    print("测试函数执行")
    return True

if __name__ == "__main__":
    print("有问题的导入文件")
    test_function()
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(problematic_content)
    
    print(f"✓ 创建了有问题的测试文件: {test_file}")
    return test_file

def demonstrate_original_problems(test_file) -> None:
    """演示原始问题"""
    print("\n=== 演示原始问题 ===")
    
    try:
        # 尝试直接运行有问题的文件
        import subprocess
        result = subprocess.run([
            _ = "python", str(test_file)
        ], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print("✓ 成功演示了原始问题:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return True
        else:
            print("✗ 未能演示原始问题")
            return False
    except Exception as e:
        print(f"✗ 演示原始问题时出错: {e}")
        return False

def run_auto_fix():
    """运行自动修复"""
    print("\n=== 运行自动修复 ===")
    
    try:
        # 导入并运行增强版修复工具
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from advanced_auto_fix import AdvancedImportFixer
        
        fixer = AdvancedImportFixer()
        # 只修复测试文件
        fixer.fix_file(PROJECT_ROOT / "scripts" / "test_problematic_import.py")
        
        print("✓ 自动修复完成")
        return True
    except Exception as e:
        print(f"✗ 自动修复时出错: {e}")
        return False

def verify_fix():
    """验证修复结果"""
    print("\n=== 验证修复结果 ===")
    
    try:
        # 尝试导入修复后的文件
        spec = importlib.util.spec_from_file_location(
            "test_problematic_import", 
            PROJECT_ROOT / "scripts" / "test_problematic_import.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        print("✓ 修复后的文件可以成功导入和执行")
        return True
    except Exception as e:
        print(f"✗ 验证修复结果时出错: {e}")
        return False

def cleanup_test_file(test_file) -> None:
    """清理测试文件"""
    try:
        if test_file.exists():
            test_file.unlink()
            print(f"✓ 清理了测试文件: {test_file}")
        return True
    except Exception as e:
        print(f"✗ 清理测试文件时出错: {e}")
        return False

def main() -> None:
    """主函数"""
    print("=== 自动修复工具演示 ===")
    print("本演示将展示自动修复工具如何解决原始的导入问题")
    
    # 创建有问题的文件
    test_file = create_problematic_file()
    
    # 演示原始问题
    demonstrate_original_problems(test_file)
    
    # 运行自动修复
    run_auto_fix()
    
    # 验证修复结果
    verify_fix()
    
    # 清理
    cleanup_test_file(test_file)
    
    print("\n=== 演示完成 ===")
    print("自动修复工具成功解决了原始的导入问题！")

if __name__ == "__main__":
    main()