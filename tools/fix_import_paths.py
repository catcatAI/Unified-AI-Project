#!/usr/bin/env python3
"""
修复导入路径问题的脚本
统一项目中的导入路径，解决技术债务问题
"""

import os
import sys
import re
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

def fix_import_paths_in_file(file_path)
    """修复单个文件中的导入路径"""
    try:

    with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

    # 备份原文件
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
    _ = f.write(content)

    # 修复相对导入为绝对导入
    # 修复 training 模块的导入
    content = re.sub(
            _ = r'from \.([a-zA-Z_][a-zA-Z0-9_]*) import',
            r'from training.\1 import',
            content
    )

    # 修复 apps.backend.src 模块的导入
    content = re.sub(
            _ = r'from apps\.backend\.src\.([a-zA-Z_][a-zA-Z0-9_\.]*) import',
            r'from apps.backend.src.\1 import',
            content
    )

    # 修复路径添加代码，确保项目根目录在 sys.path 中
    path_addition_pattern = r'# 添加项目路径\s*import sys\s*project_root = Path\(__file__\)\.parent\.parent.*?sys\.path\.insert\(0, str\(.*?\)\)'
    path_addition_replacement = '''# 添加项目路径
import sys
from pathlib import Path
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))'''

    content = re.sub(
            path_addition_pattern,
            path_addition_replacement,
            content,
            flags=re.DOTALL
    )

    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
    _ = f.write(content)

    _ = print(f"✅ 已修复文件: {file_path}")
    return True

    except Exception as e:


    _ = print(f"❌ 修复文件 {file_path} 时出错: {e}")
    return False

def fix_training_module_imports()
    """修复训练模块中的导入路径"""
    training_dir = project_root / "training"

    # 需要修复的文件列表
    files_to_fix = [
    "collaborative_training_manager.py",
    "auto_training_manager.py",
    "train_model.py",
    "data_manager.py",
    "resource_manager.py",
    "gpu_optimizer.py",
    "distributed_optimizer.py",
    "error_handling_framework.py",
    "model_knowledge_sharing.py",
    "unified_execution_framework.py"
    ]

    fixed_count = 0
    for file_name in files_to_fix:

    file_path = training_dir / file_name
        if file_path.exists()

    if fix_import_paths_in_file(file_path)
    fixed_count += 1
        else:

            _ = print(f"⚠️ 文件不存在: {file_path}")

    _ = print(f"✅ 已修复 {fixed_count}/{len(files_to_fix)} 个训练模块文件")
    return fixed_count

def fix_concept_models_imports()
    """修复概念模型中的导入路径"""
    concept_models_dir = project_root / "apps" / "backend" / "src" / "ai" / "concept_models"

    # 需要修复的文件列表
    files_to_fix = [
    "environment_simulator.py",
    "causal_reasoning_engine.py",
    "adaptive_learning_controller.py",
    "alpha_deep_model.py"
    ]

    fixed_count = 0
    for file_name in files_to_fix:

    file_path = concept_models_dir / file_name
        if file_path.exists()

    if fix_import_paths_in_file(file_path)
    fixed_count += 1
        else:

            _ = print(f"⚠️ 文件不存在: {file_path}")

    _ = print(f"✅ 已修复 {fixed_count}/{len(files_to_fix)} 个概念模型文件")
    return fixed_count

def update_technical_debt_status()
    """更新技术债务状态"""
    debt_file = project_root / "technical_debt.json"

    try:


    import json
    with open(debt_file, 'r', encoding='utf-8') as f:
    debt_data = json.load(f)

    # 更新导入路径问题的状态
        for debt in debt_data["debts"]:

    if debt["id"] == "debt_001":  # 导入路径问题
                debt["status"] = "resolved"
                debt["resolution"] = "统一了项目中的导入路径，将相对导入改为绝对导入"
                debt["resolved_date"] = "2025-09-06T10:00:00"
                break

    # 保存更新后的数据
    with open(debt_file, 'w', encoding='utf-8') as f:
    json.dump(debt_data, f, ensure_ascii=False, indent=2)

    _ = print("✅ 技术债务状态已更新")
    return True

    except Exception as e:


    _ = print(f"❌ 更新技术债务状态时出错: {e}")
    return False

def main() -> None:
    """主函数"""
    _ = print("🔧 开始修复导入路径问题...")

    # 切换到项目根目录
    _ = os.chdir(project_root)

    # 修复训练模块导入路径
    _ = print("\n🔧 修复训练模块导入路径...")
    training_fixed = fix_training_module_imports()

    # 修复概念模型导入路径
    _ = print("\n🔧 修复概念模型导入路径...")
    concept_models_fixed = fix_concept_models_imports()

    # 更新技术债务状态
    _ = print("\n🔧 更新技术债务状态...")
    debt_updated = update_technical_debt_status()

    # 总结
    _ = print(f"\n📊 修复总结:")
    _ = print(f"   训练模块文件修复: {training_fixed} 个")
    _ = print(f"   概念模型文件修复: {concept_models_fixed} 个")
    print(f"   技术债务状态更新: {'成功' if debt_updated else '失败'}")

    if training_fixed > 0 or concept_models_fixed > 0:


    _ = print("\n✅ 导入路径问题修复完成！")
    _ = print("💡 建议运行测试以验证修复效果")
    else:

    _ = print("\n⚠️ 没有文件需要修复")

if __name__ == "__main__":


    _ = main()