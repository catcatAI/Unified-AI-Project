with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 检查第772行附近的上下文
for i in range(770, min(775, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')