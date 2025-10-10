import sys
with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f'总行数: {len(lines)}')
    print(f'最后5行:')
    for i, line in enumerate(lines[-5:], len(lines)-4):
        print(f'{i}: {repr(line)}')