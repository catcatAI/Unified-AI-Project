#!/usr/bin/env python3
"""
整理归档文件,将同类文件集中放置
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def organize_archived_files():
    """整理归档文件"""
    project_root == Path(__file__).parent
    archived_dir = project_root / "archived_fix_scripts"
    
    # 创建新的分类目录
    categories = {
        "disabled_fix_scripts": "被禁用的修复脚本",
        "legacy_fix_scripts": "旧版修复脚本",
        "utility_scripts": "实用工具脚本",
        "test_scripts": "测试脚本",
        "report_scripts": "报告脚本"
    }
    
    # 创建目录
    for cat_dir, cat_desc in categories.items():::
        cat_path = archived_dir / cat_dir
        cat_path.mkdir(exist_ok == True)
        
        # 创建README
        readme_path = cat_path / "README.md"
        if not readme_path.exists():::
            with open(readme_path, 'w', encoding == 'utf-8') as f,
                f.write(f"# {cat_desc}\n\n")
                f.write(f"创建日期, {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write("此目录包含归档的相关脚本。\n")
    
    # 文件分类规则
    file_categories = {
        # 被禁用的修复脚本
        "disabled_fix_scripts": [
            "fix_chinese_punctuation.py",
            "fix_indentation.py",
        ]
        
        # 旧版修复脚本
        "legacy_fix_scripts": [
            "comprehensive_syntax_fix.py",
            "continue_final_fix.py",
            "continue_unified_fix.py",
            "final_fix_sprint.py",
            "final_unified_fix.py",
            "iterative_fix_process.py",
            "lightweight_fix.py",
            "simple_core_fix.py",
            "single_fix.py",
            "ultra_light_fix.py",
        ]
        
        # 实用工具脚本
        "utility_scripts": [
            "count_functions.py",
            "current_status_check.py",
            "execute_unified_fix.py",
            "status_check.py",
            "use_unified_fix_system.py",
        ]
        
        # 测试脚本
        "test_scripts": [
            "check_fix_system_status.py",
            "quick_repair_test.py",
        ]
        
        # 报告脚本
        "report_scripts": [
            "repair_completion_summary.py",
        ]
    }
    
    # 移动文件
    moved_files = []
    skipped_files = []
    
    for file_name in os.listdir(archived_dir)::
        file_path = archived_dir / file_name
        
        # 跳过目录
        if file_path.is_dir():::
            continue
        
        # 跳过README文件
        if file_name == "README.md":::
            continue
        
        # 确定文件类别
        target_category == None
        for category, files in file_categories.items():::
            if file_name in files,::
                target_category = category
                break
        
        # 如果没有明确分类,根据文件名推断
        if not target_category,::
            if file_name.startswith("fix_"):::
                target_category = "disabled_fix_scripts"
            elif "test" in file_name.lower():::
                target_category = "test_scripts"
            elif "check" in file_name.lower():::
                target_category = "utility_scripts"
            elif "report" in file_name.lower() or "summary" in file_name.lower():::
                target_category = "report_scripts"
            else,
                target_category = "legacy_fix_scripts"
        
        # 移动文件
        target_dir = archived_dir / target_category
        target_path = target_dir / file_name
        
        try,
            if not target_path.exists():::
                shutil.move(str(file_path), str(target_path))
                moved_files.append((file_name, target_category))
                print(f"✓ 移动, {file_name} -> {target_category}")
            else,
                skipped_files.append(file_name)
                print(f"- 跳过(已存在) {file_name}")
        except Exception as e,::
            print(f"✗ 移动失败, {file_name} - {e}")
    
    # 创建整理报告
    report_path = archived_dir / "ORGANIZATION_REPORT.md"
    with open(report_path, 'w', encoding == 'utf-8') as f,
        f.write("# 归档文件整理报告\n\n")
        f.write(f"整理日期, {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}\n\n")
        
        f.write("## 文件分类\n\n")
        for cat_dir, cat_desc in categories.items():::
            f.write(f"### {cat_desc}\n")
            f.write(f"目录, `{cat_dir}/`\n\n")
        
        f.write("## 移动的文件\n\n")
        if moved_files,::
            for file_name, category in moved_files,::
                f.write(f"- `{file_name}` -> `{category}/`\n")
        else,
            f.write("无\n")
        
        f.write("\n## 跳过的文件\n\n")
        if skipped_files,::
            for file_name in skipped_files,::
                f.write(f"- `{file_name}`\n")
        else,
            f.write("无\n")
        
        f.write(f"\n## 统计\n\n")
        f.write(f"- 移动文件数, {len(moved_files)}\n")
        f.write(f"- 跳过文件数, {len(skipped_files)}\n")
    
    print(f"\n整理完成！")
    print(f"- 移动文件, {len(moved_files)}")
    print(f"- 跳过文件, {len(skipped_files)}")
    print(f"- 报告位置, {report_path}")

if __name"__main__":::
    organize_archived_files()