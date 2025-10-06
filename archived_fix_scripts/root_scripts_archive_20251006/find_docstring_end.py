with open('apps/backend/src/core/hsp/connector.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找从第669行开始的闭合三引号
start_line = 668
found_end = False
for i in range(start_line, len(lines)):
    line_content = lines[i].rstrip()
    if line_content.strip() == '"""' and i > start_line:
        print(f'找到闭合三引号在第{i+1}行')
        found_end = True
        break
    elif i > start_line + 50:  # 限制搜索范围
        break

if not found_end:
    print('在合理范围内未找到闭合三引号')
    print('最后几行:')
    for i in range(max(0, len(lines)-5), len(lines)):
        print(f'{i+1:3d}: {repr(lines[i].rstrip())}')