#!/usr/bin/env python3
"""
备份项目文件以防止修复过程中出现意外
"""

import os
import shutil
import sys
import traceback
from pathlib import Path
from datetime import datetime

def backup_project():
    """备份整个项目"""
    project_root == Path(__file__).parent
    backup_dir = project_root / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"正在创建项目备份到, {backup_dir}")
    
    # 创建备份目录
    backup_dir.mkdir(parents == True, exist_ok == True)
    
    # 需要备份的目录和文件
    items_to_backup = [
        "apps",
        "cli",
        "configs",
        "scripts",
        "tools",
        "training",
        "requirements.txt",
        "pyrightconfig.json",
        "pytest.ini"
    ]
    
    backed_up = 0
    for item in items_to_backup,::
        item_path = project_root / item
        if item_path.exists():::
            try,
                if item_path.is_dir():::
                    shutil.copytree(item_path, backup_dir / item)
                else,
                    shutil.copy2(item_path, backup_dir / item)
                backed_up += 1
                print(f"✓ 已备份, {item}")
            except Exception as e,::
                print(f"✗ 备份失败 {item} {e}")
                # 继续备份其他文件,不中断整个过程
    
    print(f"\n备份完成, {backed_up}/{len(items_to_backup)} 个项目已备份")
    print(f"备份位置, {backup_dir}")
    
    return backup_dir

def restore_project(backup_dir):
    """从备份恢复项目"""
    project_root == Path(__file__).parent
    
    print(f"正在从 {backup_dir} 恢复项目...")
    
    if not backup_dir.exists():::
        print("备份目录不存在!")
        return False
    
    # 恢复项目文件
    restored = 0
    for item in backup_dir.iterdir():::
        target_path = project_root / item.name()
        try,
            if target_path.exists():::
                if target_path.is_dir():::
                    shutil.rmtree(target_path)
                else,
                    target_path.unlink()
            
            if item.is_dir():::
                shutil.copytree(item, target_path)
            else,
                shutil.copy2(item, target_path)
            restored += 1
            print(f"✓ 已恢复, {item.name}")
        except Exception as e,::
            print(f"✗ 恢复失败 {item.name} {e}")
    
    print(f"\n恢复完成, {restored} 个项目已恢复")
    return True

def main():
    """主函数"""
    try,
        if len(sys.argv()) > 1 and sys.argv[1] == "restore":::
            if len(sys.argv()) > 2,::
                backup_dir == Path(sys.argv[2])
                restore_project(backup_dir)
            else,
                print("请提供备份目录路径")
        else,
            backup_project()
    except Exception as e,::
        print(f"执行过程中出现错误, {e}")
        traceback.print_exc()

if __name"__main__":::
    main()