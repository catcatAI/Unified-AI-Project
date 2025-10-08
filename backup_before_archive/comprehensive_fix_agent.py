import os
import sys

def fix_enhanced_demo_agent_comprehensive():
    """fix_enhanced_demo_agent_comprehensive 函数"""
    file_path = r"d:\Projects\Unified-AI-Project\apps\backend\src\agents\enhanced_demo_agent.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复所有缩进问题
    lines = content.split('\n')
    fixed_lines = []
    
    # 跟踪缩进级别
    indent_level = 0
    in_class = False
    in_function = False
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # 跳过空行
        if not stripped_line:
            fixed_lines.append(line)
            continue
            
        # 处理类定义
        if stripped_line.startswith('class '):
            in_class = True
            indent_level = 1
            fixed_lines.append(line.rstrip() + ':')  # 确保有冒号
            continue
            
        # 处理函数定义
        if stripped_line.startswith('def ') or stripped_line.startswith('async def '):
            # 如果是类中的函数，增加缩进
            if in_class:
                indent_level = 2
            else:
                indent_level = 1
            in_function = True
            fixed_lines.append('    ' * (indent_level - 1) + line.strip())
            continue
            
        # 处理代码块开始
        if stripped_line.endswith(':') and not stripped_line.startswith('#'):
            # 保持当前缩进并增加下一级
            fixed_lines.append('    ' * (indent_level - 1) + stripped_line)
            # 检查是否是控制结构
            if any(stripped_line.startswith(keyword) for keyword in ['if ', 'for ', 'while ', 'else:', 'elif ']):
                indent_level += 1
            continue
            
        # 处理代码块结束
        if stripped_line in ['else:', 'elif ']:
            # 减少缩进
            indent_level = max(1, indent_level - 1)
            fixed_lines.append('    ' * (indent_level - 1) + stripped_line)
            indent_level += 1
            continue
            
        # 处理return语句
        if stripped_line.startswith('return '):
            fixed_lines.append('    ' * (indent_level - 1) + stripped_line)
            continue
            
        # 处理普通代码行
        fixed_lines.append('    ' * (indent_level - 1) + stripped_line)
        
        # 检查是否需要减少缩进（例如在return后）
        if stripped_line.startswith('return ') and indent_level > 1:
            indent_level -= 1
    
    # 重新组合内容
    fixed_content = '\n'.join(fixed_lines)
    
    # 修复特定的语法问题
    fixed_content = fixed_content.replace("parameters = task_payload.get(\"parameters\", )", 
                                         "parameters = task_payload.get(\"parameters\", {})")
    
    fixed_content = fixed_content.replace("health_report.get('uptime_seconds', 0).1f", 
                                         "health_report.get('uptime_seconds', 0):.1f")
    
    fixed_content = fixed_content.replace("for i in range(count)", "for i in range(count):")
    fixed_content = fixed_content.replace("await self.get_all_active_agents", "await self.get_all_active_agents()")
    fixed_content = fixed_content.replace("await self.get_agent_registry_stats",
     "await self.get_agent_registry_stats()")
    fixed_content = fixed_content.replace("health_report = await self.get_health_report()",
     "health_report = await self.get_health_report()")
    fixed_content = fixed_content.replace("queue_status = await self.get_task_queue_status()",
     "queue_status = await self.get_task_queue_status()")
    fixed_content = fixed_content.replace("_ = await agent.refresh_agent_status",
     "_ = await agent.refresh_agent_status()")
    fixed_content = fixed_content.replace("health_report = await agent.get_health_report",
     "health_report = await agent.get_health_report()")
    fixed_content = fixed_content.replace("queue_status = await agent.get_task_queue_status",
     "queue_status = await agent.get_task_queue_status()")
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"已全面修复 {file_path} 中的语法和缩进错误")

if __name__ == "__main__":
    fix_enhanced_demo_agent_comprehensive()