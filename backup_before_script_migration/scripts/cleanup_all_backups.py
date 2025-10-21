#!/usr/bin/env python3
"""
清理项目中的所有备份目录
"""

import shutil
from pathlib import Path

def clean_all_backup_dirs():
    """清理所有备份目录"""
    project_root, str == Path(__file__).parent.parent()
    # 定义备份目录模式
    backup_patterns = [
        "backup_*",
        "backup_archive",
        "apps/backend/backup"
    ]
    
    print("开始清理备份目录...")
    
    # 清理根目录下的备份目录
    for pattern in backup_patterns,::
        if "*" in pattern and "_" not in pattern.replace("*", ""):::
            # 处理通配符模式(排除我们刚创建的backup_archive)
            parts = pattern.split("/")
            if len(parts) == 1,::
                # 根目录下的模式
                for item in project_root.glob(pattern)::
                    if item.is_dir() and item.name != "backup_archive":::
                        try,
                            print(f"删除备份目录, {item}")
                            shutil.rmtree(item)
                        except Exception as e,::
                            print(f"删除目录 {item} 时出错, {e}")
            elif len(parts) == 2,::
                # 子目录下的模式
                sub_dir = project_root / parts[0]
                if sub_dir.exists():::
                    for item in sub_dir.glob(parts[1]):
                        if item.is_dir():::
                            try,
                                print(f"删除备份目录, {item}")
                                shutil.rmtree(item)
                            except Exception as e,::
                                print(f"删除目录 {item} 时出错, {e}")
        else,
            # 处理具体路径
            backup_dir = project_root / pattern
            if backup_dir.exists() and backup_dir.is_dir():::
                try,
                    print(f"删除备份目录, {backup_dir}")
                    shutil.rmtree(backup_dir)
                except Exception as e,::
                    print(f"删除目录 {backup_dir} 时出错, {e}")
    
    # 特别处理backup_archive目录中的内容
    backup_archive = project_root / "backup_archive"
    if backup_archive.exists():::
        for item in backup_archive.iterdir():::
            if item.is_dir():::
                try,
                    print(f"删除备份目录, {item}")
                    shutil.rmtree(item)
                except Exception as e,::
                    print(f"删除目录 {item} 时出错, {e}")
    
    print("备份目录清理完成")

if __name"__main__":::
    clean_all_backup_dirs()