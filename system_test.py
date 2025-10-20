#!/usr/bin/env python3
"""
统一系统管理器测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入功能"""
    try:
        # 测试统一系统管理器导入
        from unified_system_manager import UnifiedSystemManager, SystemConfig
        print("✅ UnifiedSystemManager 导入成功")
        
        # 测试BaseAgent导入
        from apps.backend.src.ai.agents.base.base_agent import BaseAgent
        print("✅ BaseAgent 导入成功")
        
        # 测试训练系统导入
        from training.train_model import ModelTrainer
        print("✅ ModelTrainer 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    try:
        from unified_system_manager import UnifiedSystemManager, SystemConfig
        
        # 创建系统管理器实例
        config = SystemConfig()
        manager = UnifiedSystemManager(config)
        print("✅ UnifiedSystemManager 实例创建成功")
        
        # 获取系统摘要
        summary = manager.get_system_summary()
        print(f"✅ 系统摘要获取成功: {summary}")
        
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Unified AI Project 系统测试")
    print("=" * 50)
    
    # 测试导入
    if test_imports():
        print("\n✅ 所有导入测试通过")
    else:
        print("\n❌ 导入测试失败")
        return
    
    # 测试基本功能
    if test_basic_functionality():
        print("\n✅ 基本功能测试通过")
    else:
        print("\n❌ 基本功能测试失败")
        return
    
    print("\n🎉 所有测试通过！")

if __name__ == "__main__":
    main()