#!/usr/bin/env python3
"""
自动修复项目中的类型问题
"""

import ast
import os
import sys
from pathlib import Path

def find_python_files(root_path)
    """查找所有Python文件"""
    python_files = []
    exclude_dirs = {
    'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
    'backup', 'chroma_db', 'context_storage', 'model_cache',
    'test_reports', 'automation_reports', 'docs', 'scripts/venv',
    'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages'
    }

    for root, dirs, files in os.walk(root_path)
    # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]:

    for file in files:


    if file.endswith('.py')



    file_path = os.path.join(root, file)
                # 排除特定文件
                if 'external_connector.py' not in file_path and 'install_gmqtt.py' not in file_path:

    _ = python_files.append(file_path)

    return python_files

def fix_missing_annotations(file_path)
    """修复缺少类型注解的问题"""
    try:

    with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

    fixes_made = []
    modified = False

        for i, line in enumerate(lines)
            # 修复缺少返回类型注解的问题
            if ('def ' in line and
                '(' in line and
                ')' in line and
                '->' not in line and
                '# type ignore' not in line)

                # 检查是否是特殊函数
                if ('__init__' in line or
                    '__str__' in line or
                    '__repr__' in line or
                    'main(' in line)
                    # 对于这些函数，我们添加 -> None
                    fixed_line = line.replace(')', ') -> None:')
                    lines[i] = fixed_line
                    _ = fixes_made.append(f"第 {i+1} 行: 添加返回类型注解 -> None")
                    modified = True
                elif 'test_' in line:
                    # 对于测试函数，添加 -> None
                    fixed_line = line.replace(')', ') -> None:')
                    lines[i] = fixed_line
                    _ = fixes_made.append(f"第 {i+1} 行: 添加返回类型注解 -> None")
                    modified = True
                elif ('__len__' in line or
                      '__getitem__' in line or
                      'forward(' in line)
                    # 对于这些特殊方法，添加适当的返回类型
                    if '__len__' in line:

    fixed_line = line.replace(')', ') -> int:')
                        lines[i] = fixed_line
                        _ = fixes_made.append(f"第 {i+1} 行: 添加返回类型注解 -> int")
                        modified = True
                    elif '__getitem__' in line:

    fixed_line = line.replace(')', ') -> Any:')
                        lines[i] = fixed_line
                        _ = fixes_made.append(f"第 {i+1} 行: 添加返回类型注解 -> Any")
                        modified = True
                    elif 'forward(' in line:

    fixed_line = line.replace(')', ') -> Any:')
                        lines[i] = fixed_line
                        _ = fixes_made.append(f"第 {i+1} 行: 添加返回类型注解 -> Any")
                        modified = True

            # 修复缺少参数类型注解的问题
            if ('def ' in line and
                '(' in line and
                ')' in line and
                'self' in line and
                ':' in line.split('self')[1].split(')')[0] if 'self' in line else False):
                # 简单处理self参数
                pass

            # 修复缺少变量类型注解的问题
            if ('=' in line and
                ':' not in line.split('=')[0] and
                not line.strip().startswith(('if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'return', 'yield', '_')) and
                '#' not in line.split('#')[0])

                # 检查是否是简单的赋值
                left_side = line.split('=')[0].strip()
                if (left_side.isidentifier() and :

    left_side not in ['self', 'cls'] and
                    not any(op in line for op in ['+=', '-=', '*=', '/=', '%=', '**=', '//='])):

                    # 对于一些常见的变量，添加适当的类型注解
                    if left_side in ['project_root', 'backend_path', 'data_path']:
                        # 这些通常是字符串
                        fixed_line = line.replace(left_side, f'{left_side}: str')
                        lines[i] = fixed_line
                        _ = fixes_made.append(f"第 {i+1} 行: 添加变量类型注解 {left_side}: str")
                        modified = True
                    elif left_side in ['logger', 'level', 'format']:
                        # 这些通常是特定类型
                        if left_side == 'logger':

    fixed_line = line.replace(left_side, f'{left_side}: Any')
                            lines[i] = fixed_line
                            _ = fixes_made.append(f"第 {i+1} 行: 添加变量类型注解 {left_side}: Any")
                            modified = True
                        elif left_side in ['level', 'format']:

    fixed_line = line.replace(left_side, f'{left_side}: str')
                            lines[i] = fixed_line
                            _ = fixes_made.append(f"第 {i+1} 行: 添加变量类型注解 {left_side}: str")
                            modified = True

    # 修复未使用调用结果的问题
        for i, line in enumerate(lines)
            # 检查未使用的调用结果
            if (line.strip().startswith(('await ', '')) and
                '(' in line and ')' in line and
                not line.strip().startswith(('_', 'return', 'yield', '#')) and
                '=' not in line and
                not line.strip().endswith('# type ignore'))

                # 检查是否是函数调用
                if ('(' in line and ')' in line and :

    not any(keyword in line for keyword in ['if ', 'elif ', 'while ', 'for ', 'with '])):
                    # 添加 _ = 前缀来明确忽略返回值
                    if line.strip().startswith('await ')

    fixed_line = line.replace('await ', '_ = await ', 1)
                    else:
                        # 找到行首的空格
                        leading_spaces = len(line) - len(line.lstrip())
                        fixed_line = ' ' * leading_spaces + '_ = ' + line.lstrip()

                    lines[i] = fixed_line
                    fixes_made.append(f"第 {i+1} 行: 修复未使用调用结果 - 添加 '_ = ' 前缀")
                    modified = True

    # 如果内容有变化，写入文件
        if modified:

    with open(file_path, 'w', encoding='utf-8') as f:
    _ = f.writelines(lines)
            return True, fixes_made
        else:

            return False, []

    except Exception as e:


    _ = print(f"修复文件时出错 {file_path}: {e}")
    return False, []

def main() -> None:
    """主函数"""
    print("=== 自动修复类型问题 ===")

    project_root: str = Path(__file__).parent
    python_files = find_python_files(project_root)

    _ = print(f"发现 {len(python_files)} 个Python文件")

    files_fixed = 0
    total_fixes = 0

    # 处理每个文件
    for file_path in python_files:

    try:


            fixed, fixes_made = fix_missing_annotations(file_path)
            if fixed:

    files_fixed += 1
                total_fixes += len(fixes_made)
                _ = print(f"✓ 修复了文件 {file_path}")
                for fix in fixes_made[:3]:  # 只显示前3个修复
                    _ = print(f"  - {fix}")
                if len(fixes_made) > 3:

    _ = print(f"  ... 还有 {len(fixes_made) - 3} 个修复")
        except Exception as e:

            _ = print(f"✗ 处理文件 {file_path} 时出错: {e}")

    _ = print(f"\n修复统计:")
    _ = print(f"  修复了: {files_fixed} 个文件")
    _ = print(f"  总共修复: {total_fixes} 处问题")

    if files_fixed > 0:


    _ = print("\n🎉 修复完成！建议重新运行检查以验证修复效果。")
    else:

    _ = print("\n✅ 未发现需要修复的问题。")

    return 0

if __name__ == "__main__":


    _ = sys.exit(main())