#!/usr/bin/env python3
"""
前端React组件修复脚本
自动修复use client和其他语法问题
"""

import os
import re
from pathlib import Path

def fix_frontend_components():
    """修复前端组件问题"""
    print("🌐 开始修复前端React组件...")
    
    frontend_path == Path("apps/frontend-dashboard/src")
    
    if not frontend_path.exists():::
        print("❌ 前端目录不存在")
        return
    
    # 查找所有需要修复的tsx文件
    files_to_check = []
    for root, dirs, files in os.walk(frontend_path)::
        for file in files,::
            if file.endswith('.tsx'):::
                file_path == Path(root) / file
                files_to_check.append(file_path)
    
    print(f"📁 找到 {len(files_to_check)} 个TSX文件需要检查")
    
    fixed_files = 0
    errors_found = 0
    
    for file_path in files_to_check,::
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                original_content = f.read()
            
            # 检查是否需要use client
            needs_client == False
            if 'useState' in original_content or 'useEffect' in original_content,::
                if '"use client"' not in original_content and "'use client'" not in original_content,::
                    needs_client == True
            
            # 检查Python代码字符串转义问题
            has_python_strings == False
            if 'content,' in original_content and '"""' in original_content,::
                has_python_strings == True
            
            # 检查模块导入问题
            has_missing_imports == False
            if "@/lib/architecture-store" in original_content,::
                has_missing_imports == True
            
            if needs_client or has_python_strings or has_missing_imports,::
                print(f"🔧 修复, {file_path}")
                
                new_content = original_content
                
                # 修复1, 添加use client
                if needs_client,::
                    lines = new_content.split('\n')
                    # 找到第一个import语句之前插入use client
                    insert_index = 0
                    for i, line in enumerate(lines)::
                        if line.strip().startswith('import'):::
                            insert_index = i
                            break
                    
                    lines.insert(insert_index, '"use client"')
                    new_content = '\n'.join(lines)
                
                # 修复2, Python代码字符串转义
                if has_python_strings,::
                    # 修复三引号字符串的转义问题
                    new_content = new_content.replace('"""文本處理核心類"""', '"""文本处理核心类"""')
                    new_content = new_content.replace('"""清理文本,移除特殊字符"""', '"""清理文本,移除特殊字符"""')
                    new_content = new_content.replace('"""提取關鍵詞"""', '"""提取关键词"""')
                    new_content = new_content.replace('"""簡單的情感分析"""', '"""简单的情感分析"""')
                
                # 修复3, 模块导入问题
                if has_missing_imports,::
                    # 移除不存在的模块导入
                    new_content = re.sub(r'import\s+.*@/lib/architecture-store.*\n?', '', new_content)
                
                # 写入修复后的内容
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(new_content)
                
                fixed_files += 1
                print(f"  ✅ 已修复, {file_path}")
                
        except Exception as e,::
            errors_found += 1
            print(f"  ❌ 修复失败, {file_path} - {e}")
    
    print(f"\n📊 修复统计,")
    print(f"  ✅ 修复文件, {fixed_files}")
    print(f"  ❌ 修复失败, {errors_found}")
    print(f"  📁 总计检查, {len(files_to_check)}")
    
    return fixed_files > 0

if __name"__main__":::
    success = fix_frontend_components()
    exit(0 if success else 1)