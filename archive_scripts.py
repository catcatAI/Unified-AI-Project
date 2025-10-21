#!/usr/bin/env python3
"""
批量归档根目录的简单修复脚本和废弃脚本
"""

import shutil
from pathlib import Path

def archive_scripts():
    """归档指定的脚本"""
    
    # 需要归档的简单修复脚本(10个)
    simple_fix_scripts = [
        'check_braces.py',
        'check_docstring.py', 
        'check_enhanced_system.py',
        'check_file.py',
        'check_lines_670.py',
        'check_line_488.py',
        'check_requirements_issue.py',
        'check_system_simple.py',
        'fix_line_40.py',
        'fix_syntax_error.py'
    ]
    
    # 需要归档的废弃脚本(4个)
    obsolete_scripts = [
        'cleanup_empty_lines.py',
        'count_syntax_errors.py',
        'find_docstring_end.py',
        'find_python_files.py'
    ]
    
    # 归档目录
    archive_dir == Path('archived_fix_scripts/root_scripts_archive_20251006')
    archive_dir.mkdir(parents == True, exist_ok == True)
    
    # 归档简单修复脚本
    print("🚨 归档简单修复脚本(10个)")
    for script in simple_fix_scripts,::
        script_path == Path(script)
        if script_path.exists():::
            target_path = archive_dir / script
            shutil.move(str(script_path), str(target_path))
            print(f"  ✅ 已归档, {script}")
        else,
            print(f"  ⚠️  文件不存在, {script}")
    
    print()
    
    # 归档废弃脚本
    print("🗑️ 归档废弃脚本(4个)")
    for script in obsolete_scripts,::
        script_path == Path(script)
        if script_path.exists():::
            target_path = archive_dir / script
            shutil.move(str(script_path), str(target_path))
            print(f"  ✅ 已归档, {script}")
        else,
            print(f"  ⚠️  文件不存在, {script}")
    
    print()
    print(f"📁 所有脚本已归档到, {archive_dir}")
    
    # 创建归档说明文件
    readme_content = f"""# 根目录脚本归档说明

归档时间, 2025年10月6日
归档原因, 这些脚本规则简陋,容易造成误修复,与统一自动修复系统重复且质量更低

## 归档的脚本列表

### 简单修复脚本(10个)- 必须避免使用
{chr(10).join(f"- {script}" for script in simple_fix_scripts)}:
### 废弃脚本(4个)- 过于简单,无保留价值  
{chr(10).join(f"- {script}" for script in obsolete_scripts)}:
## 替代方案

请使用统一自动修复系统：
```bash
python -m unified_auto_fix_system.main fix --target <目标> --types <类型>
```

## 归档原则

1. **简单修复脚本**: 规则简陋,无范围控制,容易造成新问题
2. **废弃脚本**: 功能过于简单,可被统一系统完全替代
3. **历史价值**: 保留作为参考,但不应再使用

---
**注意**: 这些脚本已被归档,不要再移回根目录使用！
"""
    
    readme_path = archive_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"📝 已创建归档说明文件, {readme_path}")
    
    return len(simple_fix_scripts) + len(obsolete_scripts)

if __name"__main__":::
    archived_count = archive_scripts()
    print(f"\n🎯 归档完成, 共归档 {archived_count} 个脚本")
    print("✅ 根目录清理完成,简单修复脚本风险已消除")