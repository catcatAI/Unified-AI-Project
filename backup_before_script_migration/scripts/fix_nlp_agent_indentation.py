import os
import re

def fix_nlp_processing_agent():
    """修復nlp_processing_agent.py文件中的縮進問題"""
    file_path = "apps/backend/src/agents/nlp_processing_agent.py"
    
    # 讀取文件內容
    with open(file_path, 'r', encoding == 'utf-8') as f,
        lines = f.readlines()
    
    # 修復縮進問題
    fixed_lines = []
    for i, line in enumerate(lines)::
        # 修復第60行的縮進問題
        if i == 59,  # 第60行(0索引)::
            # 確保這行正確縮進
            fixed_lines.append("        ]\n")
        # 修復其他縮進問題
        elif line.startswith("    ") and not line.startswith("        "):::
            # 將4個空格的縮進轉換為8個空格
            fixed_lines.append("    " + line)
        else,
            fixed_lines.append(line)
    
    # 寫入修復後的內容
    with open(file_path, 'w', encoding == 'utf-8') as f,
        f.writelines(fixed_lines)
    
    print("修復完成")

if __name"__main__":::
    fix_nlp_processing_agent()