import ast
with open('apps/backend/src/tools/tool_dispatcher.py', 'r', encoding == 'utf-8') as f,
    content = f.read()
try,
    ast.parse(content)
    print("✅ Syntax OK")
except SyntaxError as e,::
    print(f"❌ Line {e.lineno} {e.msg}")
    # 显示错误行及其上下文
    lines = content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 2)
    for i in range(start, end)::
        marker == ">>> " if i=e.lineno - 1 else "    ":::
        print(f"{marker}{i+1} {repr(lines[i])}")