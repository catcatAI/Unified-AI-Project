#!/usr/bin/env python3
"""
验证修复进展
检查已修复的文件数量
"""

import sys
import subprocess
from pathlib import Path

def verify_fix_progress():
    """验证修复进展"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    
    print('=== 修复进展验证 ===')
    
    # 检查关键目录的Python文件语法状态
    key_directories = [
        'apps/backend/src/core',
        'apps/backend/src/ai', 
        'unified_auto_fix_system',
        'auto_fix_workspace',
        'tests',
        'tools',
        'training'
    ]
    
    total_files = 0
    valid_files = 0
    invalid_files = 0
    invalid_file_list = []
    
    for dir_name in key_directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue
            
        print(f'\n检查 {dir_name}...')
        
        # 获取所有Python文件
        py_files = list(dir_path.rglob('*.py'))
        dir_total = len(py_files)
        dir_valid = 0
        dir_invalid = 0
        
        for py_file in py_files:
            total_files += 1
            
            try:
                # 使用Python编译器检查语法
                result = subprocess.run([
                    sys.executable, '-m', 'pycompile', str(py_file)
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    valid_files += 1
                    dir_valid += 1
                else:
                    invalid_files += 1
                    dir_invalid += 1
                    invalid_file_list.append(py_file.relative_to(project_root))
                    
            except subprocess.TimeoutExpired:
                print(f'  超时: {py_file.name}')
                invalid_files += 1
                dir_invalid += 1
                invalid_file_list.append(py_file.relative_to(project_root))
            except Exception as e:
                print(f'  检查失败: {py_file.name} - {e}')
                invalid_files += 1
                dir_invalid += 1
                invalid_file_list.append(py_file.relative_to(project_root))
        
        # 显示目录统计
        if dir_total > 0:
            success_rate = (dir_valid / dir_total) * 100
            status_icon = "✅" if dir_invalid == 0 else "⚠️"
            print(f'  {status_icon} {dir_name}: {dir_valid}/{dir_total} ({success_rate:.1f}%)')
        else:
            print(f'  ✅ {dir_name}: 无Python文件')
    
    # 总体统计
    print(f'\n=== 总体统计 ===')
    if total_files > 0:
        overall_success_rate = (valid_files / total_files) * 100
        print(f'总文件数: {total_files}')
        print(f'有效文件: {valid_files}')
        print(f'无效文件: {invalid_files}')
        print(f'修复成功率: {overall_success_rate:.1f}%')
        
        if invalid_files > 0:
            print(f'\n=== 仍有问题的文件 (前20个) ===')
            for i, file_path in enumerate(invalid_file_list[:20]):
                print(f'  {i+1}. {file_path}')
            
            if len(invalid_file_list) > 20:
                print(f'  ... 还有 {len(invalid_file_list) - 20} 个文件')
    else:
        print('没有找到Python文件')
    
    return invalid_files == 0, invalid_files

if __name__ == '__main__':
    all_fixed, remaining_issues = verify_fix_progress()
    
    if all_fixed:
        print('\n🎉 恭喜！所有文件语法正确！')
    else:
        print(f'\n⚠️ 还有 {remaining_issues} 个文件需要修复')
    
    sys.exit(0 if all_fixed else 1)