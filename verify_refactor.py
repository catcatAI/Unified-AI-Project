import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

def check_directory_structure():
    """检查目录结构是否正确"""
    print("=== 检查目录结构 ===")
    
    # 检查AI目录
    ai_dir = SRC_DIR / "ai"
    if ai_dir.exists():
        print(f"✓ AI目录存在: {ai_dir}")
        # 检查AI子目录
        ai_subdirs = ["agents", "memory", "learning", "dialogue", "personality", "emotion", "trust", "discovery"]
        for subdir in ai_subdirs:
            if (ai_dir / subdir).exists():
                print(f"  ✓ {subdir} 子目录存在")
            else:
                print(f"  ✗ {subdir} 子目录不存在")
    else:
        print(f"✗ AI目录不存在: {ai_dir}")
    
    # 检查Core目录
    core_dir = SRC_DIR / "core"
    if core_dir.exists():
        print(f"✓ Core目录存在: {core_dir}")
        # 检查Core子目录
        core_subdirs = ["services", "managers", "tools", "hsp", "shared"]
        for subdir in core_subdirs:
            if (core_dir / subdir).exists():
                print(f"  ✓ {subdir} 子目录存在")
            else:
                print(f"  ✗ {subdir} 子目录不存在")
    else:
        print(f"✗ Core目录不存在: {core_dir}")
    
    # 检查原始目录是否已清理
    old_dirs = ["core_ai", "services", "tools", "hsp", "shared"]
    for old_dir in old_dirs:
        old_dir_path = SRC_DIR / old_dir
        if old_dir_path.exists() and any(old_dir_path.iterdir()):
            print(f"⚠ 原始目录未完全清理: {old_dir_path}")
        else:
            print(f"✓ 原始目录已清理: {old_dir_path}")

def check_import_statements():
    """检查导入语句"""
    print("\n=== 检查导入语句 ===")
    
    # 检查一些关键文件的导入语句
    key_files = [
        SRC_DIR / "core_services.py",
        SRC_DIR / "ai" / "agents" / "base" / "base_agent.py",
        SRC_DIR / "core" / "hsp" / "connector.py",
        SRC_DIR / "ai" / "dialogue" / "dialogue_manager.py"
    ]
    
    for file_path in key_files:
        if file_path.exists():
            print(f"检查文件: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查是否有旧的导入语句
                old_imports = ["from apps.backend.src.ai.", "import apps.backend.src.ai.", "from apps.backend.src.core.services.", "import apps.backend.src.core.services."]
                found_old = False
                for old_import in old_imports:
                    if old_import in content:
                        print(f"  ⚠ 发现旧导入语句: {old_import}")
                        found_old = True
                        
                if not found_old:
                    print(f"  ✓ 未发现旧导入语句")
            except Exception as e:
                print(f"  ✗ 读取文件时出错: {e}")
        else:
            print(f"文件不存在: {file_path}")

def main():
    print("Unified-AI-Project 重构验证工具")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"后端根目录: {BACKEND_ROOT}")
    print(f"源代码目录: {SRC_DIR}")
    
    check_directory_structure()
    check_import_statements()
    
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    main()