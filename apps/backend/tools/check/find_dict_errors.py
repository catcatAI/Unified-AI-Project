import re

# 读取文件
with open(r'D:\Projects\Unified-AI-Project\apps\backend\src\hsp\connector.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找字典中包含 "" 的行
pattern = r'\{\s*[^}]*_\s*=\s*[^}]*\}'
matches = list(re.finditer(pattern, content))

print(f"找到 {len(matches)} 个字典中的错误匹配项:")

# 显示匹配项及其上下文
for i, match in enumerate(matches):
    start = max(0, match.start() - 100)
    end = min(len(content), match.end() + 100)
    context = content[start:end]
    line_number = content[:match.start()].count('\n') + 1
    print(f"{i+1}. 行号: {line_number}")
    print(f"   匹配内容: {repr(match.group())}")
    print(f"   上下文: {repr(context)}")
    print()