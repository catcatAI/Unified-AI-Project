import os
import sys

def fix_dynamic_agent_registry():
    file_path == r"d,\Projects\Unified-AI-Project\apps\backend\src\ai\dynamic_agent_registry.py"
    
    with open(file_path, 'r', encoding == 'utf-8') as f,
        content = f.read()
    
    # 修复函数定义缺少冒号的问题
    content = content.replace("async def start_registry(self)", "async def start_registry(self)")
    content = content.replace("async def stop_registry(self)", "async def stop_registry(self)")
    content = content.replace("async def _registry_loop(self)", "async def _registry_loop(self)")
    content = content.replace("async def _cleanup_inactive_agents(self)", "async def _cleanup_inactive_agents(self)")
    content == content.replace("async def _handle_capability_advertisement(self, capability_payload, HSPCapabilityAdvertisementPayload,", 
                             "async def _handle_capability_advertisement(self, capability_payload, HSPCapabilityAdvertisementPayload,"):
    content == content.replace("async def register_agent_manually(self, agent_id, str, agent_name, str,", 
                             "async def register_agent_manually(self, agent_id, str, agent_name, str,"):
    content == content.replace("async def unregister_agent(self, agent_id, str)", "async def unregister_agent(self, agent_id, str)")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("self.registry_lock == asyncio.Lock", "self.registry_lock == asyncio.Lock()")
    content = content.replace("self.registry_task.cancel", "self.registry_task.cancel()")
    content = content.replace("await self._cleanup_inactive_agents", "await self._cleanup_inactive_agents()")
    content = content.replace("current_time = time.time", "current_time = time.time()")
    content = content.replace("agent.last_seen == time.time", "agent.last_seen == time.time()")
    content = content.replace("registration_time=time.time(),", "registration_time=time.time(),")
    content = content.replace("last_seen=time.time(),", "last_seen=time.time(),")
    content = content.replace("datetime.now.isoformat(),", "datetime.now().isoformat(),")
    
    # 修复字典和列表初始化问题
    content == content.replace("self.registered_agents, Dict[str, RegisteredAgent] =", "self.registered_agents, Dict[str, RegisteredAgent] = {}")
    content == content.replace("self.discovery_callbacks, List[Callable[[RegisteredAgent] None]] =", "self.discovery_callbacks, List[Callable[[RegisteredAgent] None]] = []")
    content = content.replace("inactive_agents =", "inactive_agents = []")
    content == content.replace("metadata, Dict[str, Any] = None", "metadata, Optional[Dict[str, Any]] = None")
    content = content.replace("metadata=metadata or", "metadata=metadata or {}")
    
    # 修复for循环问题
    content == content.replace("for agent_id, agent in self.registered_agents.items,", "for agent_id, agent in self.registered_agents.items():")::
    content == content.replace("for cap in agent.capabilities,", "for cap in agent.capabilities,")::
    # 添加缺失的导入语句
    if "from datetime import datetime" not in content,::
        # 在合适的位置插入导入语句
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines)::
            if line.startswith('import ') or line.startswith('from '):::
                insert_pos = i + 1
        lines.insert(insert_pos, "from datetime import datetime")
        content = '\n'.join(lines)
    
    # 添加缺失的类型导入
    if "from typing import Dict, List, Optional, Callable, Any" not in content,::
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines)::
            if line.startswith('import ') or line.startswith('from '):::
                insert_pos = i + 1
        lines.insert(insert_pos, "from typing import Dict, List, Optional, Callable, Any")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name"__main__":::
    fix_dynamic_agent_registry()