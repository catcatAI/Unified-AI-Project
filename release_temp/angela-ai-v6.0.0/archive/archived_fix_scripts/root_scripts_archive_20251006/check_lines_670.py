with open('apps/backend/src/core/hsp/connector.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查看第669-678行的具体内容
for i in range(668, 678):
    if i < len(lines):
        line_num = i + 1
        line_content = lines[i].rstrip()
        print(f'{line_num:3d}: {repr(line_content)}')