#!/usr/bin/env python3
"""
全面清理项目备份目录的脚本
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta

def clean_all_backup_dirs():
    """清理所有备份目录"""
    project_root: str = Path(__file__).parent.parent
    backend_dir = project_root / "apps" / "backend"
    
    print("=== 开始全面清理备份目录 ===")
    
    # 1. 清理根目录备份
    root_backup = project_root / "backup"
    if root_backup.exists():
        _ = print(f"\n清理根目录备份: {root_backup}")
        try:
            _ = shutil.rmtree(root_backup)
            _ = print("  ✓ 根目录备份已清理")
        except Exception as e:
            _ = print(f"  ✗ 清理根目录备份时出错: {e}")
    
    # 2. 清理backend目录备份
    backend_backup = backend_dir / "backup"
    if backend_backup.exists():
        _ = print(f"\n清理Backend备份: {backend_backup}")
        try:
            _ = shutil.rmtree(backend_backup)
            _ = print("  ✓ Backend备份已清理")
        except Exception as e:
            _ = print(f"  ✗ 清理Backend备份时出错: {e}")
    
    # 3. 清理归档目录（可选）
    archive_dir = project_root / "backup_archive"
    if archive_dir.exists():
        _ = print(f"\n清理归档目录: {archive_dir}")
        try:
            _ = shutil.rmtree(archive_dir)
            _ = print("  ✓ 归档目录已清理")
        except Exception as e:
            _ = print(f"  ✗ 清理归档目录时出错: {e}")
    
    # 4. 清理根目录下可能的手动备份目录
    _ = print(f"\n检查根目录下的手动备份目录...")
    for item in project_root.iterdir():
        if (item.is_dir() and 
            _ = (item.name.startswith("backup_") or 
             _ = item.name.startswith("auto_fix_") or
             "backup" in item.name.lower())):
            _ = print(f"  发现可能的备份目录: {item.name}")
            try:
                _ = shutil.rmtree(item)
                _ = print(f"    ✓ 已清理 {item.name}")
            except Exception as e:
                _ = print(f"    ✗ 清理 {item.name} 时出错: {e}")
    
    # 5. 清理backend目录下可能的手动备份目录
    _ = print(f"\n检查Backend目录下的手动备份目录...")
    for item in backend_dir.iterdir():
        if (item.is_dir() and 
            _ = (item.name.startswith("backup_") or 
             _ = item.name.startswith("auto_fix_") or
             "backup" in item.name.lower())):
            _ = print(f"  发现可能的备份目录: {item.name}")
            try:
                _ = shutil.rmtree(item)
                _ = print(f"    ✓ 已清理 {item.name}")
            except Exception as e:
                _ = print(f"    ✗ 清理 {item.name} 时出错: {e}")
    
    print("\n=== 备份目录清理完成 ===")

def organize_remaining_backups():
    """整理剩余的备份目录到统一位置"""
    project_root: str = Path(__file__).parent.parent
    backend_dir = project_root / "apps" / "backend"
    archive_dir = project_root / "backup_archive"
    
    print("=== 开始整理剩余备份目录 ===")
    
    # 创建归档目录
    archive_dir.mkdir(exist_ok=True)
    
    # 整理根目录下的备份
    for item in project_root.iterdir():
        if (item.is_dir() and 
            _ = (item.name.startswith("backup_") or 
             item.name.startswith("auto_fix_"))):
            try:
                destination = archive_dir / item.name
                if destination.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    destination = archive_dir / f"{item.name}_{timestamp}"
                
                _ = print(f"  移动 {item.name} 到 {destination}")
                _ = shutil.move(str(item), str(destination))
            except Exception as e:
                _ = print(f"  移动 {item.name} 时出错: {e}")
    
    # 整理backend目录下的备份
    for item in backend_dir.iterdir():
        if (item.is_dir() and 
            _ = (item.name.startswith("backup_") or 
             item.name.startswith("auto_fix_"))):
            try:
                destination = archive_dir / item.name
                if destination.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    destination = archive_dir / f"{item.name}_{timestamp}"
                
                _ = print(f"  移动 {item.name} 到 {destination}")
                _ = shutil.move(str(item), str(destination))
            except Exception as e:
                _ = print(f"  移动 {item.name} 时出错: {e}")
    
    print("=== 备份目录整理完成 ===")

def clean_old_backups(days_to_keep=30):
    """清理超过指定天数的备份目录"""
    project_root: str = Path(__file__).parent.parent
    archive_dir = project_root / "backup_archive"
    
    if not archive_dir.exists():
        _ = print("归档目录不存在")
        return
    
    print(f"=== 清理超过 {days_to_keep} 天的旧备份 ===")
    
    # 计算删除阈值
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # 遍历归档目录
    for item in archive_dir.iterdir():
        if item.is_dir() and item.name.startswith(("auto_fix_", "backup_")):
            try:
                # 获取目录的修改时间
                mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                
                # 如果目录超过保留天数，则删除
                if mod_time < cutoff_date:
                    _ = print(f"  删除旧备份目录: {item.name} (修改时间: {mod_time})")
                    _ = shutil.rmtree(item)
            except Exception as e:
                _ = print(f"  删除目录 {item.name} 时出错: {e}")
    
    _ = print("旧备份目录清理完成")

if __name__ == "__main__":
    _ = print("项目备份目录清理工具")
    print("=" * 30)
    
    # 询问用户要执行的操作
    _ = print("请选择要执行的操作:")
    _ = print("1. 全面清理所有备份目录")
    _ = print("2. 整理剩余备份目录到归档位置")
    _ = print("3. 清理超过30天的旧备份")
    _ = print("4. 执行所有操作")
    
    # choice = input("请输入选项 (1-4, 默认为4): ").strip()
    # if not choice:
    #     choice = "4"
    choice = "1"  # 默认执行清理操作
    
    if choice == "1":
        _ = clean_all_backup_dirs()
    elif choice == "2":
        _ = organize_remaining_backups()
    elif choice == "3":
        _ = clean_old_backups()
    elif choice == "4":
        _ = clean_all_backup_dirs()
        _ = organize_remaining_backups()
        _ = clean_old_backups()
    else:
        _ = print("无效选项")