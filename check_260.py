with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 打印第260行附近的内容
for i in range(255, min(265, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')