#!/usr/bin/env python3
"""
检查项目中的备份目录情况
"""

from pathlib import Path

def check_backup_dirs():
    """检查备份目录"""
    project_root: str = Path(__file__).parent.parent
    backend_dir = project_root / "apps" / "backend"
    
    print("=== 检查项目备份目录 ===")
    
    # 检查根目录备份
    root_backup = project_root / "backup"
    if root_backup.exists():
        _ = print(f"根目录备份目录: {root_backup}")
        backup_items = list(root_backup.iterdir())
        _ = print(f"  包含 {len(backup_items)} 个项目")
        for item in backup_items[:5]:  # 只显示前5个
            _ = print(f"    - {item.name}")
        if len(backup_items) > 5:
            _ = print(f"    ... 还有 {len(backup_items) - 5} 个项目")
    
    # 检查backend目录备份
    backend_backup = backend_dir / "backup"
    if backend_backup.exists():
        _ = print(f"\nBackend备份目录: {backend_backup}")
        backup_items = list(backend_backup.iterdir())
        _ = print(f"  包含 {len(backup_items)} 个项目")
        for item in backup_items[:5]:  # 只显示前5个
            _ = print(f"    - {item.name}")
        if len(backup_items) > 5:
            _ = print(f"    ... 还有 {len(backup_items) - 5} 个项目")
    
    # 检查归档目录
    archive_dir = project_root / "backup_archive"
    if archive_dir.exists():
        _ = print(f"\n归档目录: {archive_dir}")
        archive_items = list(archive_dir.iterdir())
        _ = print(f"  包含 {len(archive_items)} 个项目")
        for item in archive_items[:5]:  # 只显示前5个
            _ = print(f"    - {item.name}")
        if len(archive_items) > 5:
            _ = print(f"    ... 还有 {len(archive_items) - 5} 个项目")

if __name__ == "__main__":
    _ = check_backup_dirs()