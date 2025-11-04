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
    
    # 检查行号392的内容
    lines = content.split('\n')
    
    print(f"第392行内容: {repr(lines[391])}")  # 0-based index
    
    # 尝试修复问题
    # 问题可能是该行包含未闭合的docstring或错误的格式
    # 在第392行应该是docstring中的内容
    if 391 < len(lines):
        # 修复第392行(索引391)
        if "Register a specific handler for a capability." in lines[391]:
            # 修正这行内容,确保它正确地作为docstring的一部分
            lines[391] = "        Register a specific handler for a capability."
            print("✅ 修复了第392行的内容")
    
    # 检查前一行和后一行:
    print(f"第391行内容: {repr(lines[390])}")
    print(f"第393行内容: {repr(lines[392])}")
    
    # 写回文件
    with open(agents_base_agent, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ 文件写入完成")
    
except Exception as e:
    print(f"❌ 处理文件时出错: {e}")
    import traceback
    traceback.print_exc()