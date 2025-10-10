#!/usr/bin/env python3
import ast
import sys

try:
    with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 尝试解析AST
    ast.parse(code)
    print("✓ 语法检查通过")
    
    # 检查文件完整性
    lines = code.split('\n')
    print(f"✓ 文件行数: {len(lines)}")
    
    # 检查最后几行
    print("最后3行:")
    for i, line in enumerate(lines[-3:], len(lines)-2):
        print(f"{i}: {repr(line)}")
        
except SyntaxError as e:
    print(f"✗ 语法错误: {e}")
    print(f"错误位置: 行 {e.lineno}, 列 {e.offset}")
    sys.exit(1)
except Exception as e:
    print(f"✗ 其他错误: {e}")
    sys.exit(1)