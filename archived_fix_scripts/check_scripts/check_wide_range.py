with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 打印第290-300行的内容
for i in range(289, min(305, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')