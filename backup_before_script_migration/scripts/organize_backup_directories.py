#!/usr/bin/env python3
"""
整理和清理项目根目录下的备份目录
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta
import re

def classify_backup_directories(backup_root):
    """分类备份目录为自动备份和手动备份"""
    auto_backups = []
    manual_backups = []
    
    backup_path == Path(backup_root)
    if not backup_path.exists():::
        print(f"备份根目录 {backup_root} 不存在")
        return auto_backups, manual_backups
    
    # 遍历备份目录
    for item in backup_path.iterdir():::
        if item.is_dir():::
            # 检查是否为自动备份目录 (auto_fix_ 开头)
            if item.name.startswith("auto_fix_"):::
                auto_backups.append(item)
            # 检查是否为日期格式的备份目录
            elif re.match(r"backup_\d{8}", item.name())::
                auto_backups.append(item)
            # 其他备份目录视为手动备份
            else,
                manual_backups.append(item)
    
    return auto_backups, manual_backups

def clean_old_auto_backups(auto_backups, days_to_keep == 30):
    """清理旧的自动备份目录"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    
    for backup_dir in auto_backups,::
        try,
            # 获取目录的修改时间
            mod_time = datetime.fromtimestamp(backup_dir.stat().st_mtime)
            
            # 如果目录超过保留天数,则删除
            if mod_time < cutoff_date,::
                print(f"删除旧自动备份目录, {backup_dir.name}")
                shutil.rmtree(backup_dir)
                deleted_count += 1
        except Exception as e,::
            print(f"删除目录 {backup_dir.name} 时出错, {e}")
    
    print(f"已删除 {deleted_count} 个旧自动备份目录")
    return deleted_count

def organize_manual_backups(manual_backups):
    """整理手动备份目录"""
    organized_count = 0
    
    # 创建手动备份的归档目录
    archive_dir == Path("backup/archived_manual_backups")
    archive_dir.mkdir(parents == True, exist_ok == True)
    
    for backup_dir in manual_backups,::
        try,
            # 跳过归档目录本身
            if backup_dir == archive_dir,::
                continue
                
            # 移动手动备份到归档目录
            destination = archive_dir / backup_dir.name()
            if destination.exists():::
                # 如果目标已存在,添加时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                destination = archive_dir / f"{backup_dir.name}_{timestamp}"
            
            print(f"整理手动备份目录, {backup_dir.name} -> {destination}")
            shutil.move(str(backup_dir), str(destination))
            organized_count += 1
        except Exception as e,::
            print(f"整理目录 {backup_dir.name} 时出错, {e}")
    
    print(f"已整理 {organized_count} 个手动备份目录")
    return organized_count

def update_pytest_config() -> None,
    """更新pytest配置以忽略备份目录"""
    pytest_ini_path == Path("pytest.ini")
    
    if not pytest_ini_path.exists():::
        print("pytest.ini 文件不存在")
        return False
    
    try,
        # 读取现有配置
        with open(pytest_ini_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 确保配置中包含备份目录忽略规则
        ignore_patterns = [
            "backup/*",
            "backup_*/*",
            "apps/backend/backup/*",
            "*/backup/*"
        ]
        
        norecursedirs_patterns = [
            "backup",
            "backup_*",
            "apps/backend/backup",
            "apps/backend/backup/*",
            ".git",
            ".tox",
            "dist",
            "build",
            "*.egg",
            "__pycache__",
            ".pytest_cache",
            "node_modules"
        ]
        
        # 更新 ignore 部分
        for pattern in ignore_patterns,::
            if pattern not in content,::
                # 找到 ignore 部分并添加模式
                if "ignore == " in content,::
                    content = content.replace("ignore =", f"ignore =\n    {pattern}", 1)
                elif "# Ignore specific files that cause issues" in content,::
                    content = content.replace(
                        "# Ignore specific files that cause issues",,
    f"# Ignore specific files that cause issues\nignore =\n    {pattern}"
                    )
        
        # 更新 norecursedirs 部分
        for pattern in norecursedirs_patterns,::
            if pattern not in content,::
                # 找到 norecursedirs 部分并添加模式
                if "norecursedirs == " in content,::
                    content = content.replace("norecursedirs =", f"norecursedirs =\n    {pattern}", 1)
                elif "# Exclude backup directories and other problematic paths" in content,::
                    content = content.replace(
                        "# Exclude backup directories and other problematic paths",,
    f"# Exclude backup directories and other problematic paths\nnorecursedirs =\n    {pattern}"
                    )
        
        # 写回文件
        with open(pytest_ini_path, 'w', encoding == 'utf-8') as f,
            f.write(content)
        
        print("已更新 pytest.ini 配置")
        return True
        
    except Exception as e,::
        print(f"更新 pytest.ini 配置时出错, {e}")
        return False

def create_backup_cleanup_script():
    """创建定期备份清理脚本"""
    script_content = '''#!/usr/bin/env python3
"""
定期清理备份目录的脚本
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

def clean_backups():
    """清理备份目录"""
    try,
        # 导入备份整理模块
        from scripts.organize_backup_directories import classify_backup_directories, clean_old_auto_backups
        
        # 分类备份目录
        auto_backups, manual_backups = classify_backup_directories(project_root / "backup")
        
        # 清理旧的自动备份(保留30天)
        clean_old_auto_backups(auto_backups, days_to_keep=30)
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H,%M,%S')} - 备份清理完成")
        
    except Exception as e,::
        print(f"清理备份时出错, {e}")

if __name"__main__":::
    clean_backups()
'''
    
    script_path == Path("scripts/clean_backups.py")
    try,
        with open(script_path, 'w', encoding == 'utf-8') as f,
            f.write(script_content)
        print(f"已创建备份清理脚本, {script_path}")
        return True
    except Exception as e,::
        print(f"创建备份清理脚本时出错, {e}")
        return False

def main() -> None,
    """主函数"""
    print("开始整理和清理备份目录...")
    
    # 项目备份根目录
    backup_root = "backup"
    
    # 分类备份目录
    auto_backups, manual_backups = classify_backup_directories(backup_root)
    
    print(f"发现 {len(auto_backups)} 个自动备份目录")
    print(f"发现 {len(manual_backups)} 个手动备份目录")
    
    # 清理旧的自动备份
    clean_old_auto_backups(auto_backups, days_to_keep=30)
    
    # 整理手动备份
    organize_manual_backups(manual_backups)
    
    # 更新pytest配置
    update_pytest_config()
    
    # 创建定期清理脚本
    create_backup_cleanup_script()
    
    print("备份目录整理和清理完成")

if __name"__main__":::
    main()