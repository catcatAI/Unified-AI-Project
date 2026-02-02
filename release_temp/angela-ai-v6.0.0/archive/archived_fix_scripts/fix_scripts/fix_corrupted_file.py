# 修复文件结构
import re

with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除重复的混乱代码
# 找到正确的函数开始位置
pattern = r'(\s+return detected_confounders\s+\n\s*\n\s*async def _update_causal_graph_enhanced.*?\n\s+"""增強的因果圖更新"""\s+\n\s+try:\s+\n)(.*?)\n(\s+async def _update_causal_graph_enhanced.*?\n\s+"""增強的因果圖更新"""\s+\n\s+try:\s+\n\s+try:\s+\n)'

replacement = r'\1\3'
fixed_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if fixed_content != content:
    print("发现重复的函数定义,正在修复...")
    with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    print("修复完成")
else:
    # 尝试另一种修复模式
    pattern2 = r'(\s+return detected_confounders\s+\n)(\s*etected_confounders\.append\(confounder\)\s*\n\s*\n\s*return detected_confounders\s*\n\s*\n\s*return detected_confounders\s*\n\s*\n\s*)(async def _update_causal_graph_enhanced)'
    replacement2 = r'\1\3'
    fixed_content2 = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    if fixed_content2 != content:
        print("发现混乱代码,正在修复...")
        with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'w', encoding='utf-8') as f:
            f.write(fixed_content2)
        print("修复完成")
    else:
        print("未找到匹配的混乱代码模式")