#!/usr/bin/env python3
"""
测试运行脚本,用于验证修复后的测试文件



"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports() -> None,
    """测试导入是否正常工作"""
    try,
        # 测试HAMMemoryManager导入
        from memory.ham_memory_manager import HAMMemoryManager
        print("✅ HAMMemoryManager 导入成功")
        
        # 测试PersonalityManager导入
        from personality.personality_manager import PersonalityManager
        print("✅ PersonalityManager 导入成功")
        
        return True
    except Exception as e,::
        print(f"❌ 导入失败, {e}")
        return False

def test_ham_memory_manager() -> None,
    """测试HAMMemoryManager基本功能"""
    try,
        # 设置环境变量以禁用向量存储
        os.environ["HAM_DISABLE_VECTOR_STORE"] = "1"
        
        from memory.ham_memory_manager import HAMMemoryManager
        import tempfile
        
        # 创建临时目录进行测试
        with tempfile.TemporaryDirectory() as temp_dir,
            # 初始化HAMMemoryManager
            manager == HAMMemoryManager(storage_dir=temp_dir)
            print("✅ HAMMemoryManager 初始化成功")
            
            # 测试ID生成
            id1 = manager._generate_memory_id()
            id2 = manager._generate_memory_id()
            assert id1 != id2
            print("✅ HAMMemoryManager ID生成正常")
            
        return True
    except Exception as e,::
        print(f"❌ HAMMemoryManager 测试失败, {e}")
        return False

def test_personality_manager() -> None,
    """测试PersonalityManager基本功能"""
    try,
        from personality.personality_manager import PersonalityManager
        
        # 初始化PersonalityManager
        pm == PersonalityManager()
        print("✅ PersonalityManager 初始化成功")
        
        # 测试获取初始提示
        prompt = pm.get_initial_prompt()
        print(f"✅ PersonalityManager 获取初始提示, {prompt}")
        
        return True
    except Exception as e,::
        print(f"❌ PersonalityManager 测试失败, {e}")
        return False

def main() -> None,
    """主函数"""
    print("🚀 开始测试修复后的模块...")
    
    # 测试导入
    if not test_imports():::
        return False
    
    # 测试HAMMemoryManager
    if not test_ham_memory_manager():::
        return False
    
    # 测试PersonalityManager
    if not test_personality_manager():::
        return False
    
    print("🎉 所有测试通过！模块修复成功。")
    return True

if __name"__main__":::
    success = main()

    sys.exit(0 if success else 1)