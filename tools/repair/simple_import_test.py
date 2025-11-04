import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, project_root)

try:
    # 测试导入ai.agents模块
    from apps.backend.src.ai.agents import BaseAgent
    print("✅ 成功导入BaseAgent")
except Exception as e:
    print(f"❌ 导入BaseAgent失败: {e}")

try:
    # 测试导入CreativeWritingAgent
    from apps.backend.src.ai.agents.specialized.creative_writing_agent import CreativeWritingAgent
    print("✅ 成功导入CreativeWritingAgent")
except Exception as e:
    print(f"❌ 导入CreativeWritingAgent失败: {e}")

try:
    # 测试导入WebSearchAgent
    from apps.backend.src.ai.agents.specialized.web_search_agent import WebSearchAgent
    print("✅ 成功导入WebSearchAgent")
except Exception as e:
    print(f"❌ 导入WebSearchAgent失败: {e}")

try:
    # 测试BaseAgent类是否可实例化
    from apps.backend.src.ai.agents.base.base_agent import BaseAgent
    agent = BaseAgent("test_agent")
    print("✅ 成功创建BaseAgent实例")
except Exception as e:
    print(f"❌ 创建BaseAgent实例失败: {e}")