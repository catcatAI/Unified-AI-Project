with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 打印第196行附近的内容
for i in range(191, min(201, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')