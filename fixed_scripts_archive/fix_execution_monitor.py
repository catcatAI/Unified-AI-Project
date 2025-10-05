import os
import sys

def fix_execution_monitor():
    file_path = r"d:\Projects\Unified-AI-Project\apps\backend\src\ai\execution_monitor.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复函数定义缺少冒号的问题
    content = content.replace("def _monitor_terminal(self)", "def _monitor_terminal(self):")
    content = content.replace("def _monitor_resources(self)", "def _monitor_resources(self):")
    content = content.replace("def _start_monitoring(self)", "def _start_monitoring(self):")
    content = content.replace("def _stop_monitoring(self)", "def _stop_monitoring(self):")
    
    # 修复函数调用缺少括号的问题
    content = content.replace("start_time = time.time", "start_time = time.time()")
    content = content.replace("response_time = time.time - start_time", "response_time = time.time() - start_time")
    content = content.replace("self._terminal_status = self.check_terminal_responsiveness", "self._terminal_status = self.check_terminal_responsiveness()")
    content = content.replace("memory = psutil.virtual_memory", "memory = psutil.virtual_memory()")
    content = content.replace("disk = psutil.disk_usage('/')", "disk = psutil.disk_usage('/')")
    content = content.replace("self._terminal_check_thread.start", "self._terminal_check_thread.start()")
    
    # 修复字典访问问题
    content = content.replace("self._execution_history:", "self._execution_history:")
    
    # 添加缺失的导入语句
    if "import psutil" not in content:
        # 在合适的位置插入导入语句
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_pos = i + 1
        lines.insert(insert_pos, "import psutil")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name__ == "__main__":
    fix_execution_monitor()