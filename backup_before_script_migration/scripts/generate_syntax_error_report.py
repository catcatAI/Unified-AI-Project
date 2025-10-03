import os
import ast
import subprocess
from typing import List, Tuple

def has_syntax_error(file_path: str) -> Tuple[bool, str]:
    """檢查文件是否有語法錯誤，如果有則返回錯誤信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return False, ""
    except SyntaxError as e:
        return True, str(e)
    except Exception as e:
        # 其他錯誤（如編碼錯誤）
        return True, str(e)

def get_files_with_syntax_errors() -> List[Tuple[str, str]]:
    """獲取所有有語法錯誤的Python文件及其錯誤信息"""
    py_files_with_errors = []
    
    # 遍歷當前目錄下的所有Python文件
    for root, dirs, files in os.walk('.'):
        # 跳過某些目錄以提高效率
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file).replace('\\', '/')
                has_error, error_msg = has_syntax_error(file_path)
                if has_error:
                    py_files_with_errors.append((file_path, error_msg))
    
    return py_files_with_errors

def main():
    """主函數"""
    print("Generating syntax error report...")
    
    # 獲取所有有語法錯誤的Python文件
    files_with_errors = get_files_with_syntax_errors()
    
    if not files_with_errors:
        print("No Python files with syntax errors found.")
        return
    
    print(f"Found {len(files_with_errors)} Python files with syntax errors.")
    
    # 生成報告
    report_lines = []
    report_lines.append("# Syntax Error Report")
    report_lines.append("")
    report_lines.append(f"Total files with syntax errors: {len(files_with_errors)}")
    report_lines.append("")
    report_lines.append("## Files with syntax errors:")
    report_lines.append("")
    
    for file_path, error_msg in files_with_errors:
        report_lines.append(f"- {file_path}")
        if error_msg:
            report_lines.append(f"  - Error: {error_msg}")
        report_lines.append("")
    
    # 寫入報告文件
    report_path = "syntax_error_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Syntax error report generated: {report_path}")
    
    # 顯示前10個文件的錯誤信息
    print("\nFirst 10 files with syntax errors:")
    for i, (file_path, error_msg) in enumerate(files_with_errors[:10]):
        print(f"{i+1}. {file_path}")
        if error_msg:
            print(f"   Error: {error_msg}")
        print()

if __name__ == "__main__":
    main()