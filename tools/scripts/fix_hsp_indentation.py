#!/usr/bin/env python3
"""
修复HSP连接器中的缩进问题
"""

import os
import sys
from pathlib import Path

def fix_hsp_indentation():
    """修复HSP连接器中的缩进问题"""
    connector_path = Path(r"d:\Projects\Unified-AI-Project\apps\backend\src\core\hsp\connector.py")
    
    if not connector_path.exists():
        print(f"错误: 找不到文件 {connector_path}")
        return False
    
    try:
        with open(connector_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 需要修复缩进的函数列表
        functions_to_fix = [
            "_dispatch_fact_to_callbacks",
            "_dispatch_capability_advertisement_to_callbacks", 
            "_dispatch_task_request_to_callbacks",
            "_dispatch_task_result_to_callbacks",
            "_dispatch_acknowledgement_to_callbacks"
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检查是否是需要修复的函数定义
            for func_name in functions_to_fix:
                if f"async def {func_name}" in line and line.strip().endswith(":"):
                    # 找到函数定义的下一行
                    if i + 1 < len(lines):
                        # 修复该函数内的所有缩进
                        j = i + 1
                        in_function = True
                        function_indent_level = None
                        
                        while j < len(lines) and in_function:
                            current_line = lines[j]
                            
                            # 检查是否到达下一个函数定义或类定义
                            if (current_line.strip().startswith("def ") or 
                                current_line.strip().startswith("async def ") or
                                current_line.strip().startswith("class ")):
                                in_function = False
                                break
                            
                            # 如果是空行，跳过
                            if current_line.strip() == "":
                                j += 1
                                continue
                            
                            # 如果是注释行，保持原样
                            if current_line.strip().startswith("#"):
                                j += 1
                                continue
                            
                            # 计算当前行的缩进级别
                            if function_indent_level is None and current_line.strip() != "":
                                # 第一个非空行应该是4个空格缩进
                                if not current_line.startswith("    "):
                                    # 修复缩进
                                    lines[j] = "    " + current_line.lstrip()
                                function_indent_level = 4
                            
                            # 如果已经有缩进级别，检查并修复
                            if function_indent_level is not None:
                                # 确保至少有4个空格缩进
                                if not current_line.startswith("    ") and current_line.strip() != "":
                                    lines[j] = "    " + current_line.lstrip()
                            
                            j += 1
                        
                        # 跳过已处理的行
                        i = j
                        break
            else:
                i += 1
        
        # 写入修复后的内容
        with open(connector_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"成功修复HSP连接器中的缩进问题: {connector_path}")
        return True
        
    except Exception as e:
        print(f"修复HSP连接器缩进时出错: {e}")
        return False

def main():
    """主函数"""
    print("开始修复HSP连接器中的缩进问题...")
    
    if fix_hsp_indentation():
        print("HSP连接器缩进问题修复完成!")
    else:
        print("HSP连接器缩进问题修复失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())