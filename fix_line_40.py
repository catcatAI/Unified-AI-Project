with open('unified_auto_fix_system/modules/syntax_fixer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到问题行并替换
lines = content.split('\n')
for i, line in enumerate(lines):
    if i == 39:  # Line 40 (0-indexed)
        # 替换这行
        lines[i] = '                "pattern": r\'^\\s*(class|def|if|elif|else|for|while|try|except|finally|with)\\s+[^:]*$\','
        print(f'Fixed line {i+1}')

# 写回文件
with open('unified_auto_fix_system/modules/syntax_fixer.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Fixed syntax error')