import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

def check_refactor_status():
    """检查重构状态"""
    print("=== Unified-AI-Project 重构状态检查 ===")
    
    # 1. 检查目录结构
    print("\n1. 目录结构检查:")
    
    # 检查AI目录
    ai_dir = SRC_DIR / "ai"
    if ai_dir.exists():
        print(f"  ✓ AI目录存在: {ai_dir.name}")
        # 检查AI子目录
        expected_ai_subdirs = ["agents", "memory", "learning", "dialogue", "personality", "emotion", "trust", "discovery"]
        for subdir in expected_ai_subdirs:
            if (ai_dir / subdir).exists():
                print(f"    ✓ {subdir} 子目录存在")
            else:
                print(f"    ✗ {subdir} 子目录不存在")
    else:
        print(f"  ✗ AI目录不存在: {ai_dir.name}")
    
    # 检查Core目录
    core_dir = SRC_DIR / "core"
    if core_dir.exists():
        print(f"  ✓ Core目录存在: {core_dir.name}")
        # 检查Core子目录
        expected_core_subdirs = ["services", "managers", "tools", "hsp", "shared"]
        for subdir in expected_core_subdirs:
            if (core_dir / subdir).exists():
                print(f"    ✓ {subdir} 子目录存在")
            else:
                print(f"    ✗ {subdir} 子目录不存在")
    else:
        print(f"  ✗ Core目录不存在: {core_dir.name}")
    
    # 检查原始目录是否已清理
    print("\n2. 原始目录清理检查:")
    old_dirs = ["core_ai", "services", "tools", "hsp", "shared"]
    all_cleaned = True
    for old_dir in old_dirs:
        old_dir_path = SRC_DIR / old_dir
        if old_dir_path.exists() and any(old_dir_path.iterdir()):
            print(f"  ⚠ 原始目录未完全清理: {old_dir}")
            all_cleaned = False
        else:
            print(f"  ✓ 原始目录已清理: {old_dir}")
    
    if all_cleaned:
        print("\n✓ 所有原始目录已清理")
    else:
        print("\n⚠ 部分原始目录未清理")
    
    # 3. 检查关键文件是否存在
    print("\n3. 关键文件检查:")
    key_files = [
        ("Core Services", SRC_DIR / "core_services.py"),
        ("Base Agent", SRC_DIR / "ai" / "agents" / "base" / "__init__.py"),
        ("HSP Connector", SRC_DIR / "core" / "hsp" / "connector.py"),
        ("Dialogue Manager", SRC_DIR / "ai" / "dialogue" / "dialogue_manager.py")
    ]
    
    for file_desc, file_path in key_files:
        if file_path.exists():
            print(f"  ✓ {file_desc} 文件存在")
        else:
            print(f"  ✗ {file_desc} 文件不存在: {file_path}")
    
    # 4. 检查自动修复工具
    print("\n4. 自动修复工具检查:")
    auto_fix_tools = [
        ("增强版自动修复工具", PROJECT_ROOT / "scripts" / "enhanced_auto_fix.py"),
        ("导入修复工具", BACKEND_ROOT / "scripts" / "auto_fix_imports.py"),
        ("完整修复工具", BACKEND_ROOT / "scripts" / "auto_fix_complete.py"),
        ("项目一键修复工具", PROJECT_ROOT / "scripts" / "auto_fix_project.py")
    ]
    
    for tool_desc, tool_path in auto_fix_tools:
        if tool_path.exists():
            print(f"  ✓ {tool_desc} 存在")
        else:
            print(f"  ✗ {tool_desc} 不存在: {tool_path}")
    
    print("\n=== 重构状态检查完成 ===")

def main():
    check_refactor_status()

if __name__ == "__main__":
    main()