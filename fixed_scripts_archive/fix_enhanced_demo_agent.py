import os
import sys

def fix_enhanced_demo_agent():
    file_path = r"d:\Projects\Unified-AI-Project\apps\backend\src\agents\enhanced_demo_agent.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复类定义缺少冒号的问题
    content = content.replace("class EnhancedDemoAgent(BaseAgent)\n", "class EnhancedDemoAgent(BaseAgent):\n")
    
    # 修复函数定义缺少冒号的问题
    content = content.replace("async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope)\n", 
                             "async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):\n")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("_ = await self.refresh_agent_status\n", "_ = await self.refresh_agent_status()\n")
    content = content.replace("health_report = await self.get_health_report\n", "health_report = await self.get_health_report()\n")
    content = content.replace("queue_status = await self.get_task_queue_status\n", "queue_status = await self.get_task_queue_status()\n")
    content = content.replace("await self.get_agent_registry_stats\n", "await self.get_agent_registry_stats()\n")
    content = content.replace("_ = await agent.start\n", "_ = await agent.start()\n")
    content = content.replace("_ = await agent.stop\n", "_ = await agent.stop()\n")
    
    # 修复time.time调用
    content = content.replace("int(time.time)", "int(time.time())")
    
    # 修复变量初始化问题
    content = content.replace("results =\n\n            for i in range(task_count)\n", 
                             "results = []\n\n            for i in range(task_count):\n")
    
    # 修复其他缺少冒号的地方
    content = content.replace("parameters = task_payload.get(\"parameters\", )\n    action = parameters.get(\"action\", \"process\")\n\n        if action == \"process\":\n", 
                             "parameters = task_payload.get(\"parameters\", {})\n    action = parameters.get(\"action\", \"process\")\n\n        if action == \"process\":\n")
    
    # 修复async def main后缺少冒号的问题
    content = content.replace("async def main -> None:\n", "async def main() -> None:\n")
    
    # 添加缺失的导入语句
    if "from typing import Any, Dict" not in content:
        # 找到import语句的位置并添加typing导入
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        lines.insert(insert_pos, "from typing import Any, Dict")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name__ == "__main__":
    fix_enhanced_demo_agent()