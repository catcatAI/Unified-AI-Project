#!/usr/bin/env python3
"""
测试语法修复器对实际文件的修复效果
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
from unified_auto_fix_system.core.fix_result import FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixPriority

def test_syntax_fixer_on_file():
    """测试语法修复器对实际文件的修复效果"""
    print("测试语法修复器对实际文件的修复效果...")
    
    # 创建测试文件的副本
    test_file = Path("test_files/test_syntax_errors.py")
    if not test_file.exists():
        print(f"测试文件 {test_file} 不存在")
        return False
    
    # 创建临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "test_syntax_errors.py"
        shutil.copy2(test_file, temp_file)
        
        print(f"复制测试文件到: {temp_file}")
        
        # 创建修复器实例
        fixer = EnhancedSyntaxFixer(Path("."))
        
        # 创建修复上下文
        context = FixContext(
            project_root=Path("."),
            target_path=temp_file,
            scope=FixScope.SPECIFIC_FILE,
            priority=FixPriority.NORMAL,
            dry_run=False  # 实际修改文件
        )
        
        # 分析文件
        print("分析文件中的语法问题...")
        issues = fixer.analyze(context)
        print(f"发现 {len(issues)} 个语法问题:")
        
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. 行 {issue.line_number}: {issue.error_type} - {issue.error_message}")
        
        # 修复文件
        print("修复文件...")
        result = fixer.fix(context)
        
        print(f"修复结果: {result.summary()}")
        print(f"发现的问题: {result.issues_found}")
        print(f"修复的问题: {result.issues_fixed}")
        
        # 读取修复后的文件内容
        with open(temp_file, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        print("修复后的文件内容:")
        print("-" * 50)
        print(fixed_content)
        print("-" * 50)
        
        # 验证修复后的文件是否能通过语法检查
        try:
            import ast
            ast.parse(fixed_content)
            print("✅ 修复后的文件语法正确")
            return True
        except SyntaxError as e:
            print(f"❌ 修复后的文件仍有语法错误: {e}")
            return False

def main():
    """主函数"""
    print("开始测试语法修复器对实际文件的修复效果...")
    
    try:
        success = test_syntax_fixer_on_file()
        
        if success:
            print("\n🎉 语法修复器成功修复了文件中的语法错误！")
            return 0
        else:
            print("\n❌ 语法修复器未能完全修复文件中的语法错误。")
            return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())