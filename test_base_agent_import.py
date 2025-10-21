import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / "apps" / "backend" / "src"))

print("Python路径:")
for path in sys.path:
    print(f"  {path}")

# 检查两个BaseAgent文件
agents_base_agent = project_root / "apps" / "backend" / "src" / "agents" / "base_agent.py"
ai_base_agent = project_root / "apps" / "backend" / "src" / "ai" / "agents" / "base" / "base_agent.py"

print(f"\n检查文件存在性:")
print(f"  agents/base_agent.py: {agents_base_agent.exists()}")
print(f"  ai/agents/base/base_agent.py: {ai_base_agent.exists()}")

# 直接读取文件内容检查语法错误
try:
    with open(agents_base_agent, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"\n✅ 成功读取agents/base_agent.py文件,长度: {len(content)} 字符")
        
        # 检查特定行的内容
        lines = content.split('\n')
        print(f"文件总行数: {len(lines)}")
        if len(lines) > 349:
            print(f"第350行内容: {repr(lines[349])}")
        if len(lines) > 350:
            print(f"第351行内容: {repr(lines[350])}")
except Exception as e:
    print(f"❌ 读取agents/base_agent.py文件失败: {e}")

try:
    # 尝试直接导入正确的BaseAgent文件
    from ai.agents.base.base_agent import BaseAgent
    print("✅ 正确的BaseAgent导入成功")
except Exception as e:
    print(f"❌ 正确的BaseAgent导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    # 尝试导入错误的BaseAgent文件
    from agents.base_agent import BaseAgent
    print("✅ 错误的BaseAgent导入成功")
except Exception as e:
    print(f"❌ 错误的BaseAgent导入失败: {e}")