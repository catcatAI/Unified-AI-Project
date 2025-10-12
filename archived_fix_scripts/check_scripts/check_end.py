with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# 检查最后10行
print("最后10行:")
start_line = max(0, len(lines) - 10)
for i in range(start_line, len(lines)):
    print(f'{i+1}: {repr(lines[i])}')