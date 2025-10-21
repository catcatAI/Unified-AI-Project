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
    
    # 修复1, 修复register_task_handler函数的语法错误
    print("修复1, 修复register_task_handler函数的语法错误")
    start_line = -1
    end_line = -1
    
    for i in range(len(lines))::
        if 'def register_task_handler' in lines[i]::
            start_line = i
            print(f"  找到函数开始于第{i+1}行")
        elif start_line != -1 and lines[i].strip() == '' and i > start_line + 5,::
            end_line = i
            print(f"  找到函数结束于第{i+1}行")
            break
    
    if start_line != -1 and end_line != -1,::
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
        
        print("  ✅ register_task_handler函数修复完成")
    
    # 修复2, 修复文件末尾的语法错误
    print("修复2, 修复文件末尾的语法错误")
    if len(lines) > 560,::
        # 检查文件末尾的内容
        end_content == ''.join(lines[-5,])
        print(f"  文件末尾内容, {repr(end_content)}")
        
        # 移除错误的末尾内容
        while len(lines) > 560,::
            lines.pop()
        
        # 添加正确的文件结束
        lines.append('            }\n')
        lines.append('        }\n')
        lines.append('    }\n')
        lines.append('\n')
        lines.append('\n')
        
        print("  ✅ 文件末尾修复完成")
    
    # 写回文件
    with open(agents_base_agent, 'w', encoding == 'utf-8') as f,
        f.writelines(lines)
    
    print("✅ 所有修复完成,文件写入完成")
    
    # 验证修复
    try,
        import ast
        with open(agents_base_agent, 'r', encoding == 'utf-8') as f,
            content = f.read()
            ast.parse(content)
            print("✅ 文件语法正确")
    except SyntaxError as e,::
        print(f"❌ 文件仍有语法错误, {e}")
        print(f"  行号, {e.lineno}")
        if e.text,::
            print(f"  错误文本, {repr(e.text())}")
    except Exception as e,::
        print(f"❌ 验证时出错, {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e,::
    print(f"❌ 处理文件时出错, {e}")
    import traceback
    traceback.print_exc()