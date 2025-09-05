import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

def validate_refactor():
    """验证重构是否成功"""
    print("=== Unified-AI-Project 重构最终验证 ===")
    
    # 1. 验证AI目录结构
    print("\n1. 验证AI目录结构:")
    ai_dir = SRC_DIR / "ai"
    if not ai_dir.exists():
        print("  ✗ AI目录不存在")
        return False
    
    # 检查关键AI子目录
    ai_subdirs = ["agents", "memory", "learning", "dialogue", "personality", "emotion", "trust", "discovery"]
    for subdir in ai_subdirs:
        if not (ai_dir / subdir).exists():
            print(f"  ✗ AI子目录 {subdir} 不存在")
            return False
        print(f"  ✓ AI子目录 {subdir} 存在")
    
    # 2. 验证Core目录结构
    print("\n2. 验证Core目录结构:")
    core_dir = SRC_DIR / "core"
    if not core_dir.exists():
        print("  ✗ Core目录不存在")
        return False
    
    # 检查关键Core子目录
    core_subdirs = ["services", "managers", "tools", "hsp", "shared"]
    for subdir in core_subdirs:
        if not (core_dir / subdir).exists():
            print(f"  ✗ Core子目录 {subdir} 不存在")
            return False
        print(f"  ✓ Core子目录 {subdir} 存在")
    
    # 3. 验证原始目录已清理
    print("\n3. 验证原始目录已清理:")
    old_dirs = ["core_ai", "services", "tools", "hsp", "shared"]
    for old_dir in old_dirs:
        old_dir_path = SRC_DIR / old_dir
        # 检查目录是否存在且不为空（忽略只有__init__.py的情况）
        if old_dir_path.exists():
            # 获取目录中的所有文件和文件夹
            items = list(old_dir_path.iterdir())
            # 过滤掉__init__.py文件
            non_init_items = [item for item in items if item.name != "__init__.py"]
            # 如果还有其他文件或文件夹，说明未清理完成
            if non_init_items:
                print(f"  ✗ 原始目录 {old_dir} 未清理完成，包含: {[item.name for item in non_init_items]}")
                return False
            elif items:
                print(f"  ✓ 原始目录 {old_dir} 已基本清理（仅剩__init__.py）")
            else:
                print(f"  ✓ 原始目录 {old_dir} 已完全清理")
        else:
            print(f"  ✓ 原始目录 {old_dir} 已完全清理")
    
    # 4. 验证关键文件存在
    print("\n4. 验证关键文件存在:")
    key_files = [
        ("Core Services", SRC_DIR / "core_services.py"),
        ("HSP Connector", SRC_DIR / "core" / "hsp" / "connector.py"),
        ("Dialogue Manager", SRC_DIR / "ai" / "dialogue" / "dialogue_manager.py"),
        ("Agent Manager", SRC_DIR / "core" / "managers" / "agent_manager.py")
    ]
    
    for file_desc, file_path in key_files:
        if not file_path.exists():
            print(f"  ✗ {file_desc} 文件不存在: {file_path}")
            return False
        print(f"  ✓ {file_desc} 文件存在")
    
    # 5. 验证自动修复工具存在
    print("\n5. 验证自动修复工具存在:")
    auto_fix_tools = [
        ("增强版自动修复工具", PROJECT_ROOT / "scripts" / "enhanced_auto_fix.py"),
        ("导入修复工具", BACKEND_ROOT / "scripts" / "auto_fix_imports.py"),
        ("完整修复工具", BACKEND_ROOT / "scripts" / "auto_fix_complete.py"),
        ("项目一键修复工具", PROJECT_ROOT / "scripts" / "auto_fix_project.py")
    ]
    
    for tool_desc, tool_path in auto_fix_tools:
        if not tool_path.exists():
            print(f"  ✗ {tool_desc} 不存在: {tool_path}")
            return False
        print(f"  ✓ {tool_desc} 存在")
    
    print("\n=== 重构验证通过 ===")
    print("项目目录结构重构已完成，所有验证项通过。")
    return True

def main():
    if validate_refactor():
        print("\n🎉 项目重构成功完成！")
        print("下一步：运行自动修复工具更新所有文件的导入语句")
        print("命令：python scripts/enhanced_auto_fix.py --all")
    else:
        print("\n❌ 项目重构验证失败，请检查上述错误。")
        sys.exit(1)

if __name__ == "__main__":
    main()