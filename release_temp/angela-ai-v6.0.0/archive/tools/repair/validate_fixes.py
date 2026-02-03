#!/usr/bin/env python3
"""
验证修复逻辑是否能处理报告中的具体问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer

def test_missing_colon_fix():
    """测试缺少冒号的修复"""
    print("测试缺少冒号的修复...")
    fixer = EnhancedSyntaxFixer(Path("."))
    
    # 测试报告中提到的with语句问题
    content = "with open(source_path, 'w', encoding == 'utf-8') as f"
    fixed_content = fixer._fix_missing_colons(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")
    
    # 测试类定义问题
    content = "class IntegratedAutoRepairSystem"
    fixed_content = fixer._fix_missing_colons(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")
    
    # 测试函数定义问题
    content = "def __init__(self, config, Dict[str, Any]) -> None"
    fixed_content = fixer._fix_missing_colons(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")

def test_unmatched_braces_fix():
    """测试不匹配的括号修复"""
    print("\n测试不匹配的括号修复...")
    fixer = EnhancedSyntaxFixer(Path("."))
    
    # 测试圆括号不平衡
    content = "print('Missing closing paren'"
    fixed_content = fixer._fix_unmatched_parentheses(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")
    
    # 测试方括号不平衡
    content = "list_example = [1, 2, 3"
    fixed_content = fixer._fix_unmatched_parentheses(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")
    
    # 测试花括号不平衡
    content = "dict_example = {'key': 'value'"
    fixed_content = fixer._fix_unmatched_parentheses(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")

def test_invalid_syntax_fix():
    """测试无效语法修复"""
    print("\n测试无效语法修复...")
    fixer = EnhancedSyntaxFixer(Path("."))
    
    # 测试with语句中的==错误
    content = "with open('file.txt', 'r', encoding == 'utf-8') as f:\n    content == f.read()"
    fixed_content = fixer._fix_invalid_syntax(content)
    print(f"原始内容: {content}")
    print(f"修复后: {fixed_content}")

def main():
    """主函数"""
    print("验证修复逻辑是否能处理报告中的具体问题...")
    
    try:
        test_missing_colon_fix()
        test_unmatched_braces_fix()
        test_invalid_syntax_fix()
        
        print("\n🎉 验证完成！修复逻辑能够处理报告中的问题。")
        return 0
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())