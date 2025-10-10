import re
with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有三引号
triple_quotes = re.findall(r'""".*?"""', content, re.DOTALL)
print(f'找到 {len(triple_quotes)} 个三引号字符串')

# 检查未闭合的三引号
lines = content.split('\n')
open_quotes = []
for i, line in enumerate(lines):
    if '"""' in line:
        # 计算这一行中三引号的数量
        count = line.count('"""')
        if count % 2 == 1:  # 奇数个，可能是未闭合
            open_quotes.append((i+1, line.strip()))

print('可能未闭合的三引号:')
for line_num, line in open_quotes:
    print(f'行 {line_num}: {repr(line)}')