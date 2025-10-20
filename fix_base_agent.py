"""
手动修复BaseAgent中的语法错误
"""

# 检查文件内容
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / "apps" / "backend" / "src"))

# 读取文件内容
agents_base_agent = project_root / "apps" / "backend" / "src" / "agents" / "base_agent.py"

try:
    with open(agents_base_agent, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查当前文件内容
    lines = content.split('\n')
    print(f"文件总行数: {len(lines)}")
    
    # 检查问题区域
    for i in range(345, 365):
        if i < len(lines):
            print(f"第{i+1}行: {repr(lines[i])}")
    
    # 修复问题：看起来函数定义部分有重复或不正确的格式
    # 完全替换问题函数内容
    new_content = []
    
    for i, line in enumerate(lines):
        if i == 349:  # 问题行
            # 替换为正确的docstring部分
            new_content.append('        """')
        elif i == 350:  # 问题行
            # 跳过这行，因为它导致语法错误
            continue
        else:
            new_content.append(line)
    
    # 写回文件
    with open(agents_base_agent, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_content))
    
    print("✅ 文件修复完成，移除了导致语法错误的行")
    
    # 验证修复
    try:
        import ast
        with open(agents_base_agent, 'r', encoding='utf-8') as f:
            content = f.read()
            ast.parse(content)
            print("✅ 文件语法正确")
    except SyntaxError as e:
        print(f"❌ 文件仍有语法错误: {e}")
        print(f"  行号: {e.lineno}")
        if e.text:
            print(f"  错误文本: {repr(e.text)}")
    except Exception as e:
        print(f"❌ 验证时出错: {e}")
        
except Exception as e:
    print(f"❌ 处理文件时出错: {e}")
    import traceback
    traceback.print_exc()
