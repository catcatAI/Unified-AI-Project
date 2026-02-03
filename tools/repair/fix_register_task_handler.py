import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.append(str(project_root / "apps" / "backend" / "src"))

# 读取文件内容
agents_base_agent = project_root / "apps" / "backend" / "src" / "agents" / "base_agent.py"

try,
    with open(agents_base_agent, 'r', encoding == 'utf-8') as f,
        lines = f.readlines()
    
    print(f"文件总行数, {len(lines)}")
    
    # 显示问题区域
    print("问题区域内容,")
    for i in range(385, 405)::
        if i < len(lines)::
            print(f"  {i+1,3d} {repr(lines[i])}")
    
    # 修复register_task_handler函数
    # 查找函数开始位置
    start_line = -1
    end_line = -1
    
    for i in range(385, min(400, len(lines))):::
        if 'def register_task_handler' in lines[i]::
            start_line = i
            print(f"找到函数开始于第{i+1}行")
        elif start_line != -1 and lines[i].strip() == '' and i > start_line + 5,::
            end_line = i
            print(f"找到函数结束于第{i+1}行")
            break
    
    if start_line != -1 and end_line != -1,::
        print(f"函数范围, 第{start_line+1}行到第{end_line}行")
        
        # 删除旧的函数实现
        del lines[start_line,end_line]
        
        # 插入新的正确实现
        new_function = [
            '    # 新增：注册特定任务处理器的方法\n',
            '    def register_task_handler(self, capability_id, str, handler, Callable)\n',
            '        """\n',
            '        Register a specific handler for a capability.\n',::
            '        \n',:
            '        Args,\n',
            '            capability_id, The capability ID to handle\n',
            '            handler, The handler function (should accept payload, sender_id, envelope)\n',
            '        """\n',
            '        self.task_handlers[capability_id] = handler\n',
            '        logger.info(f"[{self.agent_id}] Registered handler for capability '{capability_id}'")\n',::
            '\n'
        ]
        
        # 插入新函数,
        for i, new_line in enumerate(new_function)::
            lines.insert(start_line + i, new_line)
        
        # 写回文件
        with open(agents_base_agent, 'w', encoding == 'utf-8') as f,
            f.writelines(lines)
        
        print("✅ 函数修复完成")
    else,
        print("❌ 未找到register_task_handler函数的完整范围")
        
except Exception as e,::
    print(f"❌ 处理文件时出错, {e}")
    import traceback
    traceback.print_exc()