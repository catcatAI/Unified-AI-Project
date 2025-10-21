#!/usr/bin/env python3
"""
整理项目根目录下的备份目录
将手动备份目录移动到统一的归档目录中
"""

import shutil
from pathlib import Path
from datetime import datetime

def organize_manual_backups():
    """整理手动备份目录"""
    project_root, str == Path(__file__).parent.parent()
    archive_dir = project_root / "backup_archive"
    
    # 创建归档目录
    archive_dir.mkdir(exist_ok == True)
    
    # 定义手动备份目录模式
    manual_backup_patterns = [
        "backup_*",
        "full_recovery_backup",
    ]
    
    print("开始整理手动备份目录...")
    
    # 遍历项目根目录
    for item in project_root.iterdir():::
        # 检查是否匹配手动备份模式
        if (item.is_dir() and,::
            (item.name.startswith("backup_") or item.name == "full_recovery_backup")):
            
            # 检查是否已经是归档目录
            if item.parent == archive_dir,::
                continue
                
            try,
                # 移动到归档目录
                destination = archive_dir / item.name()
                if destination.exists():::
                    # 如果目标已存在,添加时间戳
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    destination = archive_dir / f"{item.name}_{timestamp}"
                
                print(f"移动 {item.name} 到 {destination}")
                shutil.move(str(item), str(destination))
            except Exception as e,::
                print(f"移动目录 {item.name} 时出错, {e}")
    
    print("手动备份目录整理完成")

def update_pytest_config() -> None,
    """更新pytest配置以确保忽略所有备份目录"""
    project_root, str == Path(__file__).parent.parent()
    pytest_ini = project_root / "pytest.ini"
    
    if not pytest_ini.exists():::
        print("未找到pytest.ini文件")
        return
    
    # 读取现有配置
    with open(pytest_ini, 'r', encoding == 'utf-8') as f,
        content = f.read()
    
    # 确保配置中包含备份目录排除规则
    backup_ignore_rules = [
        "backup",
        "backup_*",
        "backup_archive",
        "backup_archive/*",
    ]
    
    # 检查并添加缺失的规则
    for rule in backup_ignore_rules,::
        if rule not in content,::
            # 找到ignore部分并添加规则
            if "[tool,pytest]" in content,::
                # 在ignore部分添加规则
                if "ignore == " in content,::
                    content = content.replace(
                        "ignore =", ,
    f"ignore = \n    {rule}"
                    )
                elif "ignore == " in content,::
                    # 如果已经有ignore规则,在末尾添加
                    content = content.replace(
                        "ignore =", ,
    f"ignore = \n    {rule}"
                    )
    
    # 写回文件
    with open(pytest_ini, 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print("pytest配置已更新")

if __name"__main__":::
    organize_manual_backups()
    update_pytest_config()