import os
import sys

def fix_execution_manager():
    file_path = r"d:\Projects\Unified-AI-Project\apps\backend\src\ai\execution_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复函数定义缺少冒号的问题
    content = content.replace("def cancel_task(self, task_id: str)", "def cancel_task(self, task_id: str):")
    content = content.replace("async def execute_task(self, task: Dict[str, Any])", "async def execute_task(self, task: Dict[str, Any]):")
    content = content.replace("async def _execute_training_task(self, task: Dict[str, Any])", "async def _execute_training_task(self, task: Dict[str, Any]):")
    content = content.replace("def get_task_status(self, task_id: str)", "def get_task_status(self, task_id: str):")
    content = content.replace("def start_health_monitoring(self)", "def start_health_monitoring(self):")
    content = content.replace("def stop_health_monitoring(self)", "def stop_health_monitoring(self):")
    content = content.replace("def _health_monitoring_loop(self)", "def _health_monitoring_loop(self):")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("self.config = config or self._load_config_from_system", "self.config = config or self._load_config_from_system()")
    content = content.replace("self.logger = self._setup_logger", "self.logger = self._setup_logger()")
    content = content.replace("if config_path.exists:", "if config_path.exists():")
    content = content.replace("handler = logging.StreamHandler", "handler = logging.StreamHandler()")
    content = content.replace("self._health_check_thread.start", "self._health_check_thread.start()")
    content = content.replace("health = self.monitor.get_system_health", "health = self.monitor.get_system_health()")
    
    # 修复字典和列表初始化问题
    content = content.replace("self.task_queue: Dict[str, Any] =", "self.task_queue: Dict[str, Any] = {}")
    content = content.replace("self.execution_status: Dict[str, Any] =", "self.execution_status: Dict[str, Any] = {}")
    content = content.replace("self.issues_log: List[Dict[str, Any]] =", "self.issues_log: List[Dict[str, Any]] = []")
    content = content.replace("self.recovery_actions: List[Dict[str, Any]] =", "self.recovery_actions: List[Dict[str, Any]] = []")
    
    # 修复uuid调用问题
    content = content.replace("task_id = task.get(\"task_id\", str(uuid.uuid4))", "task_id = task.get(\"task_id\", str(uuid.uuid4()))")
    
    # 添加缺失的导入语句
    if "import uuid" not in content:
        # 在合适的位置插入导入语句
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        lines.insert(insert_pos, "import uuid")
        content = '\n'.join(lines)
    
    # 添加缺失的类型导入
    if "from typing import Dict, List, Optional, Any" not in content:
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        lines.insert(insert_pos, "from typing import Dict, List, Optional, Any")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name__ == "__main__":
    fix_execution_manager()