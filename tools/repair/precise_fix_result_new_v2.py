"""
精确修复 fix_result_new.py 文件的脚本 v2
"""

import re
import ast
import traceback
from pathlib import Path

def fix_specific_issues(content):
    """修复特定的语法错误"""
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        # 修复类定义: class ClassName, -> class ClassName:
        if re.match(r'^\s*class\s+\w+,', line):
            lines[i] = re.sub(r'class\s+(\w+),', r'class \1:', line)
        
        # 修复函数定义: def func(...) -> def func(...):
        if re.match(r'^\s*def\s+\w+\s*\(', line) and not line.strip().endswith(':'):
            # 检查是否是函数定义行的最后一部分
            if i+1 < len(lines) and not re.match(r'^\s*\w+', lines[i+1].strip()):
                lines[i] = line + ':' if not line.endswith(':') else line
        
        # 修复属性定义: attr_name, type -> attr_name: type
        if re.match(r'^\s+\w+,\s*[A-Z]', line):
            lines[i] = re.sub(r'(\w+),\s*([A-Z][A-Za-z_]*)', r'\1: \2', line)
        
        # 修复带默认值的属性定义: attr_name, type == default -> attr_name: type = default
        if re.match(r'^\s+\w+,\s*[A-Z][A-Za-z_]*\s*==', line):
            lines[i] = re.sub(r'(\w+),\s*([A-Z][A-Za-z_]*)\s*==\s*(.+)$', r'\1: \2 = \3', line)
        
        # 修复赋值操作符: == -> =
        lines[i] = re.sub(r'encoding\s*==\s*', 'encoding = ', lines[i])
        lines[i] = re.sub(r'summary\s*==\s*', 'summary = ', lines[i])
        lines[i] = re.sub(r'project_root\s*==\s*', 'project_root = ', lines[i])
        lines[i] = re.sub(r'scope\s*==\s*', 'scope = ', lines[i])
        lines[i] = re.sub(r'priority\s*==\s*', 'priority = ', lines[i])
        lines[i] = re.sub(r'backup_enabled\s*==\s*', 'backup_enabled = ', lines[i])
        lines[i] = re.sub(r'dry_run\s*==\s*', 'dry_run = ', lines[i])
        lines[i] = re.sub(r'ai_assisted\s*==\s*', 'ai_assisted = ', lines[i])
        
        # 修复 with 语句: with open(...) as f, -> with open(...) as f:
        if re.match(r'^\s*with\s+open\(.+\)\s+as\s+\w+,\s*$', line):
            lines[i] = re.sub(r'with\s+(open\(.+\)\s+as\s+\w+),', r'with \1:', line)
        
        # 修复条件语句: if condition,:: -> if condition:
        lines[i] = re.sub(r'if\s+([^:,\n]+),::', r'if \1:', lines[i])
        
        # 修复列表推导式结尾: ]:: -> ]
        lines[i] = re.sub(r'\]::', ']', lines[i])
        
        # 修复字典推导式结尾: }:: -> }
        lines[i] = re.sub(r'}::', '}', lines[i])
        
        # 修复函数调用括号: Func()() -> Func()
        lines[i] = re.sub(r'(\w+\([^)]*\))\(\)', r'\1', lines[i])
        
        # 修复 Scope 和 Priority 枚举调用: Scope.PROJECT() -> Scope.PROJECT
        lines[i] = re.sub(r'(FixScope\.[A-Z_]+)\(\)', r'\1', lines[i])
        lines[i] = re.sub(r'(FixPriority\.[A-Z_]+)\(\)', r'\1', lines[i])
        
        # 修复 f-string 语法错误
        lines[i] = re.sub(r'f"(.*?)\{"success_rate":\.1%\}(.*?)"', r'f"\1{success_rate:.1%}\2"', lines[i])
        
        # 修复字典推导式语法
        lines[i] = re.sub(r'{\s*fix_type\.value,\s*result\.to_dict\(\)\s*for\s+fix_type,\s*result\s+in\s+self\.fix_results\.items\(\)\s*}', 
                         r'{fix_type.value: result.to_dict() for fix_type, result in self.fix_results.items()}', lines[i])
    
    # 处理文件末尾的多余大括号
    # 找到最后几个大括号的位置
    content = '\n'.join(lines)
    
    # 移除多余的结尾大括号
    content = re.sub(r'\s*\}\s*\}\s*$', '\n}\n}', content, flags=re.MULTILINE)
    
    return content

def fix_file(file_path):
    """修复指定文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"开始修复文件: {file_path}")
        print(f"原始内容行数: {len(content.splitlines())}")
        
        # 应用修复
        original_content = content
        content = fix_specific_issues(content)
        
        # 检查是否有实际的修改
        if content == original_content:
            print("未检测到需要修复的内容")
        else:
            print("已应用修复")
        
        # 尝试解析修复后的内容以验证语法
        try:
            ast.parse(content)
            print("语法验证通过")
        except SyntaxError as e:
            print(f"修复后仍有语法错误: {e}")
            print("错误位置附近的内容:")
            lines = content.splitlines()
            for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
                print(f"{i+1:3d}: {lines[i]}")
            return False
        
        # 保存修复后的内容
        backup_path = Path(file_path).with_suffix('.py.bak')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"文件修复完成: {file_path}")
        print(f"原文件已备份至: {backup_path}")
        return True
        
    except Exception as e:
        print(f"修复文件时出错: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    file_path = Path("unified_auto_fix_system/core/fix_result_new.py")
    if file_path.exists():
        fix_file(file_path)
    else:
        print(f"文件不存在: {file_path}")