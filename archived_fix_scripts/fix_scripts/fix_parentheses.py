with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('(', '(').replace(')', ')')

with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed full-width parentheses')