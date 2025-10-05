import os
import sys

def fix_demo_learning_manager():
    file_path = r"d:\Projects\Unified-AI-Project\apps\backend\src\ai\demo_learning_manager.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复函数定义缺少冒号的问题
    content = content.replace("async def start_learning(self, model_id: str, config: Dict[...]", 
                             "async def start_learning(self, model_id: str, config: Dict[str, Any]) -> Any:")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("self.config = self._load_config", "self.config = self._load_config()")
    
    # 修复字典初始化问题
    content = content.replace("'user_interactions': ,", "'user_interactions': [],")
    content = content.replace("'error_patterns': ,", "'error_patterns': {},")
    content = content.replace("'performance_metrics': ,", "'performance_metrics': [],")
    content = content.replace("'system_events':", "'system_events': [],")
    
    # 修复字典初始化问题
    content = content.replace("self.training_configs: Dict[str, Any] =", "self.training_configs: Dict[str, Any] = {}")
    content = content.replace("self.model_registry: Dict[str, Any] =", "self.model_registry: Dict[str, Any] = {}")
    
    # 修复路径获取问题
    content = content.replace("self.storage_path = Path(self.config.get('demo_credentials', )", 
                             "self.storage_path = Path(self.config.get('demo_credentials', {})")
    
    # 修复datetime调用问题
    content = content.replace("datetime.now.isoformat", "datetime.now().isoformat()")
    content = content.replace("datetime.now.strftime('%Y%m%d_%H%M%S')", "datetime.now().strftime('%Y%m%d_%H%M%S')")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("_ = await self._enable_demo_mode", "_ = await self._enable_demo_mode()")
    content = content.replace("_ = await self._initialize_learning", "_ = await self._initialize_learning()")
    content = content.replace("_ = await self._setup_mock_services", "_ = await self._setup_mock_services()")
    content = content.replace("_ = await self._configure_auto_cleanup", "_ = await self._configure_auto_cleanup()")
    content = content.replace("_ = await self._save_learning_data", "_ = await self._save_learning_data()")
    content = content.replace("_ = await self._collect_learning_data", "_ = await self._collect_learning_data()")
    content = content.replace("_ = await self._perform_cleanup(cleanup_config)", "_ = await self._perform_cleanup(cleanup_config)")
    
    # 修复if语句缺少冒号的问题
    content = content.replace("if self.config_path.exists:", "if self.config_path.exists():")
    content = content.replace("except Exception as e", "except Exception as e:")
    content = content.replace("for key, value in credentials.items", "for key, value in credentials.items():")
    
    # 添加缺失的导入语句
    if "from datetime import datetime" not in content:
        # 在合适的位置插入导入语句
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        lines.insert(insert_pos, "from datetime import datetime")
        content = '\n'.join(lines)
    
    # 添加缺失的类型导入
    if "from typing import Dict, List, Optional, TYPE_CHECKING, Any" not in content:
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        lines.insert(insert_pos, "from typing import Dict, List, Optional, TYPE_CHECKING, Any")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name__ == "__main__":
    fix_demo_learning_manager()