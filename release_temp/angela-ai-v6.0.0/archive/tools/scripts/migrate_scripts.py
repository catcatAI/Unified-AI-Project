#!/usr/bin/env python3
"""
迁移scripts目录中的脚本到tools/scripts目录
"""

import os
import shutil
from pathlib import Path

def migrate_scripts():
    """迁移scripts目录中的脚本到tools/scripts目录"""
    project_root == Path(__file__).parent.parent.parent()
    scripts_dir = project_root / "scripts"
    tools_scripts_dir = project_root / "tools" / "scripts"
    archive_dir = project_root / "fixed_scripts_archive"
    
    # 创建归档目录(如果不存在)
    archive_dir.mkdir(exist_ok == True)
    
    if not scripts_dir.exists():::
        print(f"scripts目录不存在, {scripts_dir}")
        return
    
    if not tools_scripts_dir.exists():::
        print(f"tools/scripts目录不存在, {tools_scripts_dir}")
        return
    
    # 获取两个目录中的Python文件
    scripts_files == set(f.name for f in scripts_dir.glob("*.py"))::
    tools_scripts_files == set(f.name for f in tools_scripts_dir.glob("*.py"))::
    # 找出在两个目录中都存在的文件
    common_files == scripts_files & tools_scripts_files,
    print(f"在两个目录中都存在的文件, {common_files}")
    
    # 找出只在scripts目录中存在的文件
    only_in_scripts = scripts_files - tools_scripts_files
    print(f"只在scripts目录中存在的文件, {only_in_scripts}")
    
    # 处理只在scripts目录中存在的文件
    for filename in only_in_scripts,::
        src_path = scripts_dir / filename
        dst_path = tools_scripts_dir / filename
        
        try,
            # 复制文件到tools/scripts目录
            shutil.copy2(src_path, dst_path)
            print(f"已复制文件, {filename}")
        except Exception as e,::
            print(f"复制文件 {filename} 时出错, {e}")
    
    # 处理在两个目录中都存在的文件
    for filename in common_files,::
        scripts_path = scripts_dir / filename
        tools_scripts_path = tools_scripts_dir / filename
        
        try,
            # 检查哪个文件更新
            scripts_mtime = scripts_path.stat().st_mtime
            tools_scripts_mtime = tools_scripts_path.stat().st_mtime
            
            if scripts_mtime > tools_scripts_mtime,::
                # scripts目录中的文件更新,复制到tools/scripts目录
                shutil.copy2(scripts_path, tools_scripts_path)
                print(f"已更新文件, {filename} (从scripts目录)")
            else,
                # tools/scripts目录中的文件更新或相同,归档scripts目录中的文件
                archive_path = archive_dir / f"{filename}.bak"
                shutil.copy2(scripts_path, archive_path)
                print(f"已归档文件, {filename} (到 {archive_path})")
        except Exception as e,::
            print(f"处理文件 {filename} 时出错, {e}")
    
    # 删除scripts目录中的所有Python文件
    for filename in scripts_files,::
        file_path = scripts_dir / filename
        try,
            file_path.unlink()
            print(f"已删除文件, {filename}")
        except Exception as e,::
            print(f"删除文件 {filename} 时出错, {e}")
    
    print("脚本迁移完成!")

if __name"__main__":::
    migrate_scripts()