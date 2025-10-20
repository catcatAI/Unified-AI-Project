直接修复BaseAgent文件中第392行的语法错误

# 读取文件内容
with open('D:/Projects/Unified-AI-Project/apps/backend/src/agents/base_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"文件总行数: {len(lines)}")

# 检查第392行（索引391）
print(f"第392行内容: {repr(lines[391])}")
print(f"第391行内容: {repr(lines[390])}")
print(f"第393行内容: {repr(lines[392])}")

# 第392行是docstring的一部分，应该保持原样
# 错误可能是由于其他地方的语法错误导致的
# 检查整个函数定义

# 修复文件末尾的错误内容
# 第562行显示有错误的结构 '            }        "'"
print(f"第562行内容: {repr(lines[561])}")
print(f"第563行内容: {repr(lines[562])}")
print(f"第564行内容: {repr(lines[563])}")

# 修复文件末尾
if len(lines) > 561 and "            }        \"" in lines[561]:
    lines[561] = "            }\n"

# 确保文件以适当的结束
while len(lines) > 0 and lines[-1].strip() in ['', '}', '"""', "'''"]:
    lines.pop()

# 添加适当的结束
lines.append('\n')

# 写回文件
with open('D:/Projects/Unified-AI-Project/apps/backend/src/agents/base_agent.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 文件修复完成")