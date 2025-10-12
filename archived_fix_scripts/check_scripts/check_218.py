with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 打印第218行附近的内容
for i in range(213, min(223, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')