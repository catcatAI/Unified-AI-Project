#!/usr/bin/env python3
"""
检查Angela AI v6.0自主系统完整性
检测遗漏的概念设计实现
"""

import ast
import os
from pathlib import Path

AUTONOMOUS_DIR = Path("apps/backend/src/core/autonomous")

def check_file_exists(filename):
    """检查文件是否存在"""
    filepath = AUTONOMOUS_DIR / filename
    exists = filepath.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {filename}")
    return exists

def check_class_in_file(filename, class_name):
    """检查文件中是否包含特定类"""
    filepath = AUTONOMOUS_DIR / filename
    if not filepath.exists():
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == class_name:
                    return True
        return False
    except:
        return False

def check_method_in_class(filename, class_name, method_name):
    """检查类中是否包含特定方法"""
    filepath = AUTONOMOUS_DIR / filename
    if not filepath.exists():
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == method_name:
                        return True
        return False
    except:
        return False

def main():
    print("=" * 70)
    print("🔍 Angela AI v6.0 自主系统完整性检查")
    print("=" * 70)
    print()
    
    # 检查核心文件
    print("📁 核心文件检查:")
    core_files = [
        "__init__.py",
        "physiological_tactile.py",
        "endocrine_system.py",
        "autonomic_nervous_system.py",
        "neuroplasticity.py",
        "emotional_blending.py",
        "action_executor.py",
        "desktop_interaction.py",
        "browser_controller.py",
        "audio_system.py",
        "desktop_presence.py",
        "live2d_integration.py",
        "biological_integrator.py",
        "digital_life_integrator.py",
        "memory_neuroplasticity_bridge.py",
        "extended_behavior_library.py",
        "multidimensional_trigger.py",
        "cyber_identity.py",
        "self_generation.py",
    ]
    
    all_exist = True
    for file in core_files:
        if not check_file_exists(file):
            all_exist = False
    
    print()
    
    # 检查关键类
    print("🏗️ 关键类检查:")
    key_classes = [
        ("physiological_tactile.py", "PhysiologicalTactileSystem"),
        ("physiological_tactile.py", "TrajectoryAnalyzer"),
        ("physiological_tactile.py", "AdaptationMechanism"),
        ("endocrine_system.py", "EndocrineSystem"),
        ("endocrine_system.py", "HormoneKinetics"),
        ("endocrine_system.py", "FeedbackLoop"),
        ("autonomic_nervous_system.py", "AutonomicNervousSystem"),
        ("neuroplasticity.py", "NeuroplasticitySystem"),
        ("neuroplasticity.py", "SkillAcquisition"),
        ("neuroplasticity.py", "HabitFormation"),
        ("neuroplasticity.py", "TraumaMemorySystem"),
        ("emotional_blending.py", "EmotionalBlendingSystem"),
        ("emotional_blending.py", "MultidimensionalStateMatrix"),
        ("action_executor.py", "ActionExecutor"),
        ("desktop_interaction.py", "DesktopInteraction"),
        ("browser_controller.py", "BrowserController"),
        ("audio_system.py", "AudioSystem"),
        ("desktop_presence.py", "DesktopPresence"),
        ("live2d_integration.py", "Live2DIntegration"),
        ("biological_integrator.py", "BiologicalIntegrator"),
        ("digital_life_integrator.py", "DigitalLifeIntegrator"),
        ("memory_neuroplasticity_bridge.py", "MemoryNeuroplasticityBridge"),
        ("extended_behavior_library.py", "ExtendedBehaviorLibrary"),
        ("multidimensional_trigger.py", "MultidimensionalTrigger"),
        ("cyber_identity.py", "CyberIdentity"),
        ("self_generation.py", "SelfGeneration"),
    ]
    
    for filename, class_name in key_classes:
        exists = check_class_in_file(filename, class_name)
        status = "✅" if exists else "❌"
        print(f"{status} {filename}::{class_name}")
    
    print()
    print("=" * 70)
    
    # 检查概念设计中的特定功能
    print("📋 概念设计功能检查:")
    
    # L1: 感觉系统
    print("\n🖐️ L1: 感觉系统层:")
    l1_features = [
        ("physiological_tactile.py", "TrajectoryAnalyzer", "analyze"),
        ("physiological_tactile.py", "AdaptationMechanism", "_apply_habituation"),
        ("physiological_tactile.py", "AdaptationMechanism", "_apply_dishabituation"),
    ]
    
    for filename, class_name, feature in l1_features:
        exists = check_method_in_class(filename, class_name, feature)
        status = "✅" if exists else "❌"
        print(f"  {status} {feature}")
    
    # L2: 神经内分泌层
    print("\n🧬 L2: 神经内分泌层:")
    l2_features = [
        ("endocrine_system.py", "HormoneKinetics", "calculate_occupancy"),
        ("endocrine_system.py", "HormoneKinetics", "update_receptor_regulation"),
        ("endocrine_system.py", "FeedbackLoop", "simulate_hpa_axis"),
        ("endocrine_system.py", "FeedbackLoop", "circadian_rhythm"),
    ]
    
    for filename, class_name, feature in l2_features:
        exists = check_method_in_class(filename, class_name, feature)
        status = "✅" if exists else "❌"
        print(f"  {status} {feature}")
    
    # L3: 认知情感层
    print("\n🧠 L3: 认知情感层:")
    l3_features = [
        ("neuroplasticity.py", "SkillAcquisition", "start_skill"),
        ("neuroplasticity.py", "HabitFormation", "reinforce"),
        ("neuroplasticity.py", "TraumaMemorySystem", "encode_trauma"),
        ("emotional_blending.py", "MultidimensionalStateMatrix", "set_alpha_dimension"),
        ("emotional_blending.py", "MultidimensionalStateMatrix", "compute_inter_influences"),
    ]
    
    for filename, class_name, feature in l3_features:
        exists = check_method_in_class(filename, class_name, feature)
        status = "✅" if exists else "❌"
        print(f"  {status} {feature}")
    
    print()
    print("=" * 70)
    
    if all_exist:
        print("✅ 所有核心文件已创建！")
    else:
        print("❌ 部分文件缺失，请检查！")
    
    print()
    print("📊 统计:")
    print(f"  - 核心文件: {len(core_files)}个")
    print(f"  - 关键类: {len(key_classes)}个")
    print(f"  - 详细功能: 需要人工检查代码实现")

if __name__ == "__main__":
    main()
