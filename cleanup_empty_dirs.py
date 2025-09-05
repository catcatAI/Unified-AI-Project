import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

def remove_empty_dirs(directory: Path):
    """递归删除空目录"""
    if not directory.exists():
        return
    
    # 递归处理子目录
    for item in directory.iterdir():
        if item.is_dir():
            remove_empty_dirs(item)
    
    # 检查当前目录是否为空
    try:
        if not any(directory.iterdir()):
            print(f"删除空目录: {directory}")
            directory.rmdir()
    except Exception as e:
        print(f"删除目录 {directory} 时出错: {e}")

def cleanup_old_directories():
    """清理旧的目录结构"""
    print("=== 清理旧目录结构 ===")
    
    # 需要清理的旧目录
    old_dirs = ["core_ai", "services", "tools", "hsp", "shared"]
    
    for old_dir in old_dirs:
        old_dir_path = SRC_DIR / old_dir
        if old_dir_path.exists():
            print(f"清理目录: {old_dir}")
            # 删除所有子目录和文件
            for item in old_dir_path.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        print(f"  删除子目录: {item.name}")
                    else:
                        item.unlink()
                        print(f"  删除文件: {item.name}")
                except Exception as e:
                    print(f"  删除 {item} 时出错: {e}")
            
            # 删除空的主目录
            try:
                if not any(old_dir_path.iterdir()):
                    old_dir_path.rmdir()
                    print(f"  删除主目录: {old_dir}")
                else:
                    print(f"  主目录 {old_dir} 仍有文件，未删除")
            except Exception as e:
                print(f"  删除主目录 {old_dir} 时出错: {e}")
    
    print("=== 清理完成 ===")

def main():
    cleanup_old_directories()

if __name__ == "__main__":
    main()