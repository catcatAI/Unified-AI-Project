# 修复causal_reasoning_engine.py的编码问题
import re

def fix_causal_engine():
    with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换中文字符的docstring为英文
    content = content.replace('"""计算解释置信度"""', '"""Calculate explanation confidence"""')
    
    # 确保所有三引号都是标准的ASCII
    content = re.sub(r'"""', '"""', content)
    
    # 写入修复后的内容
    with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed causal reasoning engine encoding")

if __name__ == "__main__":
    fix_causal_engine()