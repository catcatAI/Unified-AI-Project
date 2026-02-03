with open('unified_auto_fix_system/modules/syntax_fixer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查大括号匹配
lines = content.split('\n')
brace_count = 0
for i, line in enumerate(lines):
    for char in line:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count < 0:
                print(f'Unmatched }} at line {i+1}: {line.strip()[:50]}...')
                break

print(f'Final brace count: {brace_count}')

# 检查特定区域
for i in range(480, 500):
    if i < len(lines):
        print(f'{i+1:3d}: {lines[i].rstrip()}')