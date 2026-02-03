"""
精确修复 fix_result_new.py 文件的脚本
"""

import re
import ast
import traceback
from pathlib import Path

def fix_class_definitions(content):
    """修复类定义语法错误"""
    # 修复类定义: class ClassName, -> class ClassName:
    content = re.sub(r'class\s+(\w+),', r'class \1:', content)
    return content

def fix_function_definitions(content):
    """修复函数定义语法错误"""
    # 修复函数定义: def func_name(self) -> def func_name(self):
    content = re.sub(r'def\s+(\w+)\(([^)]*)\)(?=\s*\n)', r'def \1(\2):', content)
    # 修复函数定义: def func_name(self) -> str -> def func_name(self) -> str:
    content = re.sub(r'def\s+(\w+)\(([^)]*)\)\s*->\s*([^:\n]+)(?=\s*\n)', r'def \1(\2) -> \3:', content)
    return content

def fix_attribute_definitions(content):
    """修复属性定义语法错误"""
    # 修复属性定义: attr_name, type -> attr_name: type
    content = re.sub(r'(\w+),\s*([A-Za-z_]\w*)', r'\1: \2', content)
    # 修复带默认值的属性定义: attr_name, type == default -> attr_name: type = default
    content = re.sub(r'(\w+),\s*([A-Za-z_]\w*)\s*==\s*(.+)', r'\1: \2 = \3', content)
    return content

def fix_dict_literals(content):
    """修复字典字面量语法错误"""
    # 修复字典字面量: {"key": value,:: -> {"key": value,}
    content = re.sub(r',::', r',', content)
    # 修复字典字面量: {key: value:: -> {key: value,}
    content = re.sub(r'(::)', r',', content)
    # 移除末尾多余的逗号
    content = re.sub(r',\s*}', r'}', content)
    return content

def fix_string_formatting(content):
    """修复字符串格式化错误"""
    # 修复 f-string 语法: f"修复成功率, {"success_rate":.1%}\n" -> f"修复成功率, {success_rate:.1%}\n"
    content = re.sub(r'f"([^"]*)"success_rate"([^"]*)"', r'f"\1{success_rate:.1%}\2"', content)
    return content

def fix_comparisons(content):
    """修复比较操作符错误"""
    # 修复比较操作符: == -> =
    content = re.sub(r'==\s*Path\(', '= Path(', content)
    content = re.sub(r'==\s*FixScope\.', '= FixScope.', content)
    content = re.sub(r'==\s*FixPriority\.', '= FixPriority.', content)
    content = re.sub(r'==\s*True', '= True', content)
    content = re.sub(r'==\s*False', '= False', content)
    return content

def fix_other_syntax_errors(content):
    """修复其他语法错误"""
    # 修复布尔值: True() -> True
    content = re.sub(r'True\(\)', 'True', content)
    # 修复布尔值: False() -> False
    content = re.sub(r'False\(\)', 'False', content)
    # 修复函数调用: str(self.project_root()) -> str(self.project_root)
    content = re.sub(r'(\w+\([^)]*\))\(\)', r'\1', content)
    # 修复字典推导式语法
    content = re.sub(r'{\s*fix_type\.value,\s*result\.to_dict\(\)\s*for\s+fix_type,\s*result\s+in\s+self\.fix_results\.items()::\s*}', 
                     '{fix_type.value: result.to_dict() for fix_type, result in self.fix_results.items()}', content)
    return content

def fix_file(file_path):
    """修复指定文件的语法错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"开始修复文件: {file_path}")
        print(f"原始内容行数: {len(content.splitlines())}")
        
        # 应用各种修复
        content = fix_class_definitions(content)
        content = fix_function_definitions(content)
        content = fix_attribute_definitions(content)
        content = fix_dict_literals(content)
        content = fix_string_formatting(content)
        content = fix_comparisons(content)
        content = fix_other_syntax_errors(content)
        
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
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"文件修复完成: {file_path}")
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