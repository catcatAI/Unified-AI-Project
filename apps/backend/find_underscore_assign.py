import re

# 读取文件
with open(r'D:\Projects\Unified-AI-Project\apps\backend\src\hsp\connector.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有包含 "_ =" 的行
pattern = r'_\s*=\s*'
matches = list(re.finditer(pattern, content))

print(f"找到 {len(matches)} 个匹配项:")

# 显示匹配项及其上下文
for i, match in enumerate(matches[:10]):  # 只显示前10个
    start = max(0, match.start() - 50)
    end = min(len(content), match.end() + 50)
    context = content[start:end]
    line_number = content[:match.start()].count('\n') + 1
    print(f"{i+1}. 行号: {line_number}")
    print(f"   上下文: {repr(context)}")
    print()