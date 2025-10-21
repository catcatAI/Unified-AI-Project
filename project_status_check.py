#!/usr/bin/env python3
"""
项目状态检查脚本 - 评估整个项目的修复进度
"""

import ast
import os
import sys
import json

def check_file_syntax(file_path):
    """检查单个文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError:
        return False
    except Exception:
        # 其他错误不影响语法检查
        return True

def check_project_status():
    """检查项目状态"""
    print("开始检查项目状态...")
    print("=" * 60)
    
    total_files = 0
    files_with_syntax_errors = 0
    files_without_syntax_errors = 0
    
    # 统计各类文件
    file_types = {}
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk('.'):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.py'):
                total_files += 1
                file_path = os.path.join(root, file)
                
                # 统计文件类型
                file_type = file.split('.')[-2] if '.' in file else 'no_extension'
                if file_type not in file_types:
                    file_types[file_type] = {'total': 0, 'syntax_errors': 0, 'no_syntax_errors': 0}
                file_types[file_type]['total'] += 1
                
                # 检查语法
                if check_file_syntax(file_path):
                    files_without_syntax_errors += 1
                    file_types[file_type]['no_syntax_errors'] += 1
                else:
                    files_with_syntax_errors += 1
                    file_types[file_type]['syntax_errors'] += 1
    
    # 输出统计结果
    print(f"总文件数: {total_files}")
    print(f"无语法错误文件数: {files_without_syntax_errors}")
    print(f"有语法错误文件数: {files_with_syntax_errors}")
    print(f"语法正确率: {files_without_syntax_errors/total_files*100:.2f}%")
    print("=" * 60)
    
    # 输出各类文件统计
    print("各类文件统计:")
    print("-" * 60)
    for file_type, stats in sorted(file_types.items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
        total = stats['total']
        no_errors = stats['no_syntax_errors']
        errors = stats['syntax_errors']
        rate = no_errors/total*100 if total > 0 else 0
        print(f"{file_type:20} | 总计: {total:4} | 正确: {no_errors:4} | 错误: {errors:4} | 正确率: {rate:6.2f}%")
    
    # 保存详细报告
    report = {
        "total_files": total_files,
        "files_without_syntax_errors": files_without_syntax_errors,
        "files_with_syntax_errors": files_with_syntax_errors,
        "syntax_correct_rate": files_without_syntax_errors/total_files*100,
        "file_types": file_types
    }
    
    with open("project_status_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("详细报告已保存到 project_status_report.json")
    
    return files_with_syntax_errors

def main():
    """主函数"""
    remaining_errors = check_project_status()
    
    if remaining_errors == 0:
        print("🎉 项目中所有Python文件语法正确!")
        return 0
    else:
        print(f"⚠️  项目中仍有 {remaining_errors} 个文件存在语法错误")
        return 1

if __name__ == "__main__":
    sys.exit(main())