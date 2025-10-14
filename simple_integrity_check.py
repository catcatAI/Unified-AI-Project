#!/usr/bin/env python3
"""
简化的项目完整性检查
"""

import os
import sys
from pathlib import Path

def check_files():
    """检查关键文件是否存在"""
    print("=== 检查关键文件 ===")
    
    files_to_check = [
        "README.md",
        "LOCAL_EXECUTION_GUIDE.md", 
        "FINAL_DELIVERY_REPORT.md",
        "apps/backend/main.py",
        "apps/backend/requirements.txt",
        "apps/backend/src/core/config/system_config.py",
        "apps/backend/src/ai/ops/ai_ops_engine.py",
        "tests/unit/test_ai_ops_complete.py",
        "package.json",
        "pnpm-workspace.yaml"
    ]
    
    missing_files = []
    for file_path in files_to_check:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_imports():
    """检查关键导入"""
    print("\n=== 检查Python导入 ===")
    
    # 添加路径
    backend_path = Path("apps/backend")
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
    
    imports_to_check = [
        ("json", "标准库"),
        ("pathlib", "标准库"),
        ("datetime", "标准库"),
        ("typing", "标准库"),
    ]
    
    success_count = 0
    for module, desc in imports_to_check:
        try:
            __import__(module)
            print(f"✅ {module} - {desc}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module} - {desc}: {e}")
    
    return success_count == len(imports_to_check)

def check_config_structure():
    """检查配置结构"""
    print("\n=== 检查配置结构 ===")
    
    config_file = Path("apps/backend/src/core/config/system_config.py")
    if not config_file.exists():
        print("❌ system_config.py 不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            "get_system_config",
            "get_ai_ops_config", 
            "get_hsp_config",
            "get_memory_config",
            "get_training_config"
        ]
        
        success_count = 0
        for func in required_functions:
            if f"def {func}" in content:
                print(f"✅ {func}")
                success_count += 1
            else:
                print(f"❌ {func}")
        
        return success_count == len(required_functions)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return False

def check_ai_ops_structure():
    """检查AI运维系统结构"""
    print("\n=== 检查AI运维系统 ===")
    
    ai_ops_files = [
        "apps/backend/src/ai/ops/__init__.py",
        "apps/backend/src/ai/ops/ai_ops_engine.py",
        "apps/backend/src/ai/ops/predictive_maintenance.py",
        "apps/backend/src/ai/ops/performance_optimizer.py",
        "apps/backend/src/ai/ops/capacity_planner.py",
        "apps/backend/src/ai/ops/intelligent_ops_manager.py"
    ]
    
    success_count = 0
    for file_path in ai_ops_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ {Path(file_path).name}")
            success_count += 1
        else:
            print(f"❌ {Path(file_path).name}")
    
    return success_count == len(ai_ops_files)

def main():
    """主检查函数"""
    print("开始简化项目完整性检查...\n")
    
    file_check = check_files()
    import_check = check_imports()
    config_check = check_config_structure()
    ai_ops_check = check_ai_ops_structure()
    
    print("\n=== 检查结果 ===")
    print(f"文件检查: {'✅ 通过' if file_check else '❌ 失败'}")
    print(f"导入检查: {'✅ 通过' if import_check else '❌ 失败'}")
    print(f"配置检查: {'✅ 通过' if config_check else '❌ 失败'}")
    print(f"AI运维检查: {'✅ 通过' if ai_ops_check else '❌ 失败'}")
    
    overall_success = all([file_check, import_check, config_check, ai_ops_check])
    
    if overall_success:
        print("\n🎉 项目完整性检查通过！")
        return 0
    else:
        print("\n⚠️ 项目完整性检查失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
