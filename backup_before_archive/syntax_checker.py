#!/usr/bin/env python3
"""
語法檢查工具
用於檢查Python文件的語法錯誤並提供詳細報告
"""

import ast
import sys
from pathlib import Path

def check_file_syntax(filename):
    """檢查單個文件的語法"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None, None
    except SyntaxError as e:
        return False, e.lineno, e.msg
    except Exception as e:
        return False, None, str(e)

def analyze_syntax_errors(filename):
    """詳細分析語法錯誤"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 嘗試解析並獲取第一個錯誤
        try:
            source = ''.join(lines)
            ast.parse(source)
            return True, []
        except SyntaxError as e:
            error_line = e.lineno
            error_msg = e.msg
            
            # 顯示錯誤上下文
            start_line = max(1, error_line - 2)
            end_line = min(len(lines), error_line + 2)
            
            context = []
            for i in range(start_line, end_line + 1):
                if i <= len(lines):
                    prefix = ">>> " if i == error_line else "    "
                    context.append(f"{prefix}{i}: {lines[i-1].rstrip()}")
            
            return False, [{
                'line': error_line,
                'message': error_msg,
                'context': context
            }]
            
    except Exception as e:
        return False, [str(e)]

def main():
    """主函數"""
    if len(sys.argv) != 2:
        print("用法: python syntax_checker.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    file_path = Path(filename)
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {filename}")
        sys.exit(1)
    
    print(f"正在檢查文件: {filename}")
    print("=" * 60)
    
    # 基本語法檢查
    success, error_line, error_msg = check_file_syntax(filename)
    
    if success:
        print("✅ 語法正確")
        return 0
    else:
        print(f"❌ 語法錯誤")
        if error_line and error_msg:
            print(f"錯誤位置: 第{error_line}行")
            print(f"錯誤信息: {error_msg}")
            
            # 詳細分析
            success_detail, errors = analyze_syntax_errors(filename)
            if errors:
                print("\n詳細分析:")
                for error in errors:
                    if isinstance(error, dict):
                        print(f"\n第{error['line']}行: {error['message']}")
                        if 'context' in error:
                            print("上下文:")
                            for line in error['context']:
                                print(line)
                    else:
                        print(f"錯誤: {error}")
        else:
            print(f"錯誤: {error_msg}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())