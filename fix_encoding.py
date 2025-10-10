# 修复tool_dispatcher.py的编码问题
import re

def fix_file_encoding():
    with open('apps/backend/src/tools/tool_dispatcher.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换可能的智能引号
    content = content.replace('"""Adds a new tool to the dispatcher."""', '"""Adds a new tool to the dispatcher."""')
    content = content.replace('"""Adds a new model to the dispatcher."""', '"""Adds a new model to the dispatcher."""')
    
    # 确保所有三引号都是标准的ASCII引号
    content = re.sub(r'["""]', '"""', content)
    content = re.sub(r'["""]', '"""', content)
    
    # 写入修复后的内容
    with open('apps/backend/src/tools/tool_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Applied encoding fixes to tool_dispatcher.py")

if __name__ == "__main__":
    fix_file_encoding()