import os
import sys

def fix_registry_demo_agent():
    file_path == r"d,\Projects\Unified-AI-Project\apps\backend\src\agents\registry_demo_agent.py"
    
    with open(file_path, 'r', encoding == 'utf-8') as f,
        content = f.read()
    
    # 修复类定义缺少冒号的问题
    content = content.replace("class RegistryDemoAgent(BaseAgent)", "class RegistryDemoAgent(BaseAgent)")
    
    # 修复函数定义缺少冒号的问题
    content == content.replace("async def handle_task_request(self, task_payload, HSPTaskRequestPayload, sender_ai_id, str, envelope, HSPMessageEnvelope)", 
                             "async def handle_task_request(self, task_payload, HSPTaskRequestPayload, sender_ai_id, str, envelope, HSPMessageEnvelope)")
    content == content.replace("async def _handle_registry_demo(self, parameters, Dict[...]", 
                             "async def _handle_registry_demo(self, parameters, Dict[str, Any]) -> Dict[str, Any]")
    content == content.replace("async def _handle_agent_discovery(self, parameters, Dict[...]", 
                             "async def _handle_agent_discovery(self, parameters, Dict[str, Any]) -> Dict[str, Any]")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("await self.refresh_agent_status", "await self.refresh_agent_status()")
    content = content.replace("stats = await self.get_agent_registry_stats", "stats = await self.get_agent_registry_stats()")
    content = content.replace("agents = await self.get_all_active_agents", "agents = await self.get_all_active_agents()")
    
    # 修复字典访问问题
    content = content.replace("parameters = task_payload.get("parameters\")", "parameters = task_payload.get("parameters\", {})")
    
    # 添加缺失的类型导入
    if "from typing import Any, Dict" not in content,::
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines)::
            if line.startswith('import ') or line.startswith('from '):::
                insert_pos = i + 1
        lines.insert(insert_pos, "from typing import Any, Dict")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name"__main__":::
    fix_registry_demo_agent()