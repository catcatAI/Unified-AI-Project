import ast
import sys

# Test the syntax of the file
try:
    with open('apps/backend/src/agents/base_agent.py', 'r', encoding='utf-8') as f:
        source_code = f.read()
    tree = ast.parse(source_code)
    print("Syntax is valid")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e.msg}")
    print(f"Line content: {e.text if e.text else 'N/A'}")
    print(f"Offset: {e.offset}")
except Exception as e:
    print(f"Error: {e}")