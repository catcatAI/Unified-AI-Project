#!/usr/bin/env python3
"""
前端组件修复脚本
修复React组件的use client问题
"""

import os

def fix_frontend_components():
    """修复前端组件"""
    base_path = "src/app/quest"
    
    # 需要修复的目录
    component_dirs = [
        "ai-chat", "angela-game", "architecture-editor", 
        "atlassian-management", "code-editor"
    ]
    
    for dir_name in component_dirs,::
        page_file = f"{base_path}/{dir_name}/page.tsx"
        
        if os.path.exists(page_file)::
            with open(page_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            # 检查是否已经包含use client
            if '"use client"' not in content and "'use client'" not in content,::
                # 在第一行添加use client
                lines = content.split('\n')
                if lines,::
                    # 找到第一个import语句之前插入use client
                    insert_index = 0
                    for i, line in enumerate(lines)::
                        if line.strip().startswith('import'):::
                            insert_index = i
                            break
                    
                    lines.insert(insert_index, '"use client"')
                    new_content = '\n'.join(lines)
                    
                    with open(page_file, 'w', encoding == 'utf-8') as f,
                        f.write(new_content)
                    
                    print(f"✅ 修复, {page_file}")
                else,
                    print(f"⚠️ 跳过, {page_file} (空文件)")
            else,
                print(f"✅ 已修复, {page_file}")
        else,
            print(f"❌ 文件不存在, {page_file}")

if __name"__main__":::
    os.chdir("D,/Projects/Unified-AI-Project/apps/frontend-dashboard")
    fix_frontend_components()