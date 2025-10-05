#!/usr/bin/env python3
"""
修复HSP连接器中函数块的缩进问题
"""

import os
import sys
from pathlib import Path

def fix_hsp_function_blocks():
    """修复HSP连接器中函数块的缩进问题"""
    connector_path = Path(r"d:\Projects\Unified-AI-Project\apps\backend\src\core\hsp\connector.py")
    
    if not connector_path.exists():
        print(f"错误: 找不到文件 {connector_path}")
        return False
    
    try:
        with open(connector_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 需要修复的函数名称
        target_functions = [
            "_dispatch_fact_to_callbacks",
            "_dispatch_capability_advertisement_to_callbacks",
            "_dispatch_task_request_to_callbacks",
            "_dispatch_task_result_to_callbacks",
            "_dispatch_acknowledgement_to_callbacks"
        ]
        
        # 遍历所有行，寻找需要修复的函数
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是目标函数定义
            for func_name in target_functions:
                if f"async def {func_name}" in line and line.strip().endswith(":"):
                    print(f"找到函数 {func_name} 在第 {i+1} 行")
                    
                    # 修复该函数内的所有缩进
                    j = i + 1
                    brace_count = 0
                    
                    while j < len(lines):
                        current_line = lines[j]
                        
                        # 检查是否到达下一个顶级函数定义或类定义
                        if (current_line.strip().startswith("def ") or 
                            current_line.strip().startswith("async def ") or
                            current_line.strip().startswith("class ")):
                            # 只有当不在嵌套代码块内时才停止
                            if brace_count == 0:
                                break
                        
                        # 检查大括号
                        brace_count += current_line.count("{")
                        brace_count -= current_line.count("}")
                        
                        # 如果不是空行且不是注释行，需要修复缩进
                        if (current_line.strip() != "" and 
                            not current_line.strip().startswith("#") and
                            not current_line.strip().startswith('"""') and
                            not current_line.strip().startswith("'''")):
                            
                            # 检查是否已经有正确的缩进（4个空格）
                            if not current_line.startswith("    "):
                                # 修复缩进 - 添加4个空格
                                lines[j] = "    " + current_line.lstrip()
                                print(f"  修复第 {j+1} 行缩进: {current_line.strip()}")
                        
                        j += 1
                    
                    # 跳过已处理的行
                    i = j
                    break
            else:
                i += 1
        
        # 写入修复后的内容
        with open(connector_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"成功修复HSP连接器中的函数块缩进问题: {connector_path}")
        return True
        
    except Exception as e:
        print(f"修复HSP连接器函数块缩进时出错: {e}")
        return False

def main():
    """主函数"""
    print("开始修复HSP连接器中的函数块缩进问题...")
    
    if fix_hsp_function_blocks():
        print("HSP连接器函数块缩进问题修复完成!")
    else:
        print("HSP连接器函数块缩进问题修复失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())