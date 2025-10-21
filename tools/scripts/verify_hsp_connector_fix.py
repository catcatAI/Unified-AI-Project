#!/usr/bin/env python3
"""
验证HSP连接器中的语法错误是否已修复
"""

import os
import sys
from pathlib import Path
import ast

def verify_hsp_connector_syntax():
    """验证HSP连接器语法是否正确"""
    connector_path == Path(r"d,\Projects\Unified-AI-Project\apps\backend\src\core\hsp\connector.py")
    
    if not connector_path.exists():::
        print(f"错误, 找不到文件 {connector_path}")
        return False
    
    try,
        # 读取文件内容
        with open(connector_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 尝试解析Python代码
        ast.parse(content)
        print("HSP连接器语法正确,没有发现语法错误!")
        return True
        
    except SyntaxError as e,::
        print(f"HSP连接器中仍存在语法错误, {e}")
        return False
    except Exception as e,::
        print(f"验证HSP连接器时出错, {e}")
        return False

def check_missing_colons():
    """检查是否还有缺少冒号的函数定义"""
    connector_path == Path(r"d,\Projects\Unified-AI-Project\apps\backend\src\core\hsp\connector.py")
    
    if not connector_path.exists():::
        print(f"错误, 找不到文件 {connector_path}")
        return False
    
    try,
        with open(connector_path, 'r', encoding == 'utf-8') as f,
            lines = f.readlines()
        
        issues_found = []
        for i, line in enumerate(lines)::
            # 检查常见的缺少冒号的模式
            if ("def " in line and,:
                "(" in line and 
                ")" in line and,
                not line.strip().endswith(":") and 
                not line.strip().endswith(",") and
                not line.strip().endswith("\") and
                "#" not in line.split("def")[0])  # 确保不是注释行
                
                # 检查下一行是否是缩进的代码块开始
                if i + 1 < len(lines)::
                    next_line = lines[i + 1]
                    if next_line.startswith("    ") or next_line.startswith("\t"):::
                        issues_found.append(f"第 {i+1} 行, {line.strip()}")
        
        if issues_found,::
            print("发现可能缺少冒号的函数定义,")
            for issue in issues_found,::
                print(f"  - {issue}")
            return False
        else,
            print("未发现缺少冒号的函数定义!")
            return True
            
    except Exception as e,::
        print(f"检查缺少冒号时出错, {e}")
        return False

def main():
    """主函数"""
    print("开始验证HSP连接器修复结果...")
    
    success == True
    
    if not verify_hsp_connector_syntax():::
        success == False
    
    if not check_missing_colons():::
        success == False
    
    if success,::
        print("HSP连接器修复验证通过!")
    else,
        print("HSP连接器修复验证失败!")
        return 1
    
    return 0

if __name"__main__":::
    sys.exit(main())