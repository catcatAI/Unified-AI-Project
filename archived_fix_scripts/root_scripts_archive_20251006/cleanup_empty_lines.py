# 清理第671-692行的多余空行
with open('apps/backend/src/core/hsp/connector.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 删除第671-692行(0索引670-691)
new_lines = lines[:670] + lines[692:]  # 保留670行及之前,692行及之后

print(f'原始行数: {len(lines)}')
print(f'新行数: {len(new_lines)}')
print(f'删除了{692-670}行')

# 写回文件
with open('apps/backend/src/core/hsp/connector.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('空行清理完成')