with open('apps/backend/src/core/hsp/connector.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查看从第669行开始的文档字符串，直到找到闭合的三引号
start_line = 668  # 第669行（0索引）
for i in range(start_line, min(start_line + 20, len(lines))):
    line_content = lines[i].rstrip()
    print(f'{i+1:3d}: {repr(line_content)}')
    if line_content.strip() == '"""' and i > start_line:
        print(f'找到闭合三引号在第{i+1}行')
        break