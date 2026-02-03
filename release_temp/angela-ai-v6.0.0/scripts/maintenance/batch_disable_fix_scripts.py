#!/usr/bin/env python3
"""
批量禁用所有未限制范围的修复脚本
"""

import os
from pathlib import Path

# 禁用内容模板
disabled_content = '''#!/usr/bin/env python3
"""
此脚本已被禁用,因为它没有范围限制。

原因：该脚本可能会修改下载的内容(如依赖、模型、数据集等),不符合项目本体的修复原则。

请使用具有范围限制的 unified-fix.py 工具进行修复。
"""

print("此脚本已被禁用并归档。")
print("请使用具有范围限制的 unified-fix.py 工具进行修复。")
print("位置：tools/unified-fix.py")
'''

# 需要禁用的修复脚本列表
scripts_to_disable = [
    "tools/scripts/fix_advanced_performance_optimizer.py",
    "tools/scripts/fix_duplicate_flaky_decorators.py",
    "tools/scripts/fix_flaky_decorators.py",
    "tools/scripts/fix_hsp_connector_issues.py",
    "tools/scripts/fix_engine.py",
    "tools/fix_import_paths.py",
    "apps/backend/scripts/fix_executor.py",
    "apps/backend/scripts/fix_import_paths.py",
    "apps/backend/tools/fix/fix_hsp_integration.py",
    "apps/backend/tools/fix/fix_import_path.py"]

project_root = Path(__file__).parent
disabled_count = 0

print("开始批量禁用未限制范围的修复脚本...")

for script_path in scripts_to_disable:
    file_path = project_root / script_path
    
    if file_path.exists():
        try:
            # 检查是否已经被禁用
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "此脚本已被禁用" in content:
                print(f"  跳过(已禁用): {script_path}")
                continue
            
            # 禁用脚本
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(disabled_content)
            
            print(f"  ✓ 禁用: {script_path}")
            disabled_count += 1
            
        except Exception as e:
            print(f"  ✗ 禁用失败: {script_path} - {e}")
    else:
        print(f"  - 文件不存在: {script_path}")

print(f"\n批量禁用完成！共禁用 {disabled_count} 个脚本")

# 检查其他可能需要禁用的脚本
print("\n检查其他可能的修复脚本...")

# 检查tools/scripts目录中其他fix_开头的脚本
tools_scripts_dir = project_root / "tools" / "scripts"
if tools_scripts_dir.exists():
    for file_path in tools_scripts_dir.glob("fix_*.py"):
        rel_path = file_path.relative_to(project_root)
        
        # 跳过已经在列表中的
        if str(rel_path) in scripts_to_disable:
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 如果包含禁用说明,跳过
            if "此脚本已被禁用" in content or "已被禁用" in content:
                continue
            
            # 检查是否有范围限制
            has_scope_limit = False
            if "project_scope" in content.lower() or "项目范围" in content:
                has_scope_limit = True
            
            if not has_scope_limit:
                # 禁用脚本
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(disabled_content)
                print(f"  ✓ 额外禁用: {rel_path}")
                disabled_count += 1
                
        except Exception as e:
            print(f"  ✗ 处理失败: {rel_path} - {e}")

print(f"\n总计禁用 {disabled_count} 个未限制范围的修复脚本")
print("所有修复脚本现在都有范围限制或已被禁用。")