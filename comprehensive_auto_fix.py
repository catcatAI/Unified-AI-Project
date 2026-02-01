#!/usr/bin/env python3
"""
全面自动修复脚本 - 解决所有可自动修复的问题
 Comprehensive Auto-Fix Script
"""

import re
import os
from pathlib import Path

def fix_bare_exceptions_in_file(filepath):
    """修复文件中的裸异常处理"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换通用的 except Exception as e: 为更具体的异常
    original = content
    
    # 修复 ImportError
    content = re.sub(
        r'except Exception as e:\s*\n\s*logger\.warning\(f"([^"]*HSM[^"]*)', 
        r'except (ImportError, ModuleNotFoundError) as e:\n            logger.warning(f"\1',
        content
    )
    
    # 修复 ValueError
    content = re.sub(
        r'except Exception as e:\s*\n\s*(logger\.debug|logger\.info)\(f"([^"]*)', 
        r'except (ValueError, TypeError) as e:\n            \1(f"\2',
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed bare exceptions in: {filepath}")
        return True
    return False

def add_config_constants():
    """在orchestrator.py顶部添加配置常量"""
    orchestrator_path = Path("apps/backend/src/core/orchestrator.py")
    
    if not orchestrator_path.exists():
        print("❌ orchestrator.py not found")
        return
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了配置常量
    if "CONFIG_" in content:
        print("⚠️  Config constants already exist")
        return
    
    # 在类定义之前添加配置常量
    config_block = '''# Configuration Constants
CONFIG_HSM_DIMENSION = 1024
CONFIG_HSM_MAX_MEMORIES = 10000
CONFIG_CDM_NOVELTY_THRESHOLD = 0.3
CONFIG_CDM_LEARNING_RATE = 0.1
CONFIG_CACHE_MAX_SIZE = 100
CONFIG_CACHE_TTL_SECONDS = 300
CONFIG_MAX_INPUT_LENGTH = 10000

'''
    
    # 在第一个import之后插入
    lines = content.split('\n')
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_idx = i + 1
    
    lines.insert(import_idx, config_block)
    
    with open(orchestrator_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Added config constants to orchestrator.py")

def add_thread_safety_to_hsm():
    """为HSM添加线程安全锁"""
    hsm_path = Path("apps/backend/src/ai/memory/hsm.py")
    
    if not hsm_path.exists():
        print("❌ hsm.py not found")
        return
    
    with open(hsm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有锁
    if "threading.Lock" in content or "asyncio.Lock" in content:
        print("⚠️  HSM already has locks")
        return
    
    # 在导入部分添加 threading
    if "import threading" not in content:
        content = content.replace(
            "import numpy as np",
            "import numpy as np\nimport threading"
        )
    
    # 在 __init__ 中添加锁
    init_pattern = r'(class HolographicStorageMatrix:.*?def __init__\(self.*?\):)'
    
    def add_lock_to_init(match):
        init_code = match.group(1)
        if "self._lock" not in content:
            return init_code + '''\n        # Thread safety lock
        self._lock = threading.Lock()'''
        return init_code
    
    content = re.sub(init_pattern, add_lock_to_init, content, flags=re.DOTALL)
    
    with open(hsm_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added thread safety to HSM")

def fix_remaining_hardcoded_ai_refs():
    """修复剩余的硬编码AI assistant引用"""
    files_to_check = [
        "apps/backend/src/services/llm_service.py",
        "apps/backend/src/services/local_llm_service.py",
        "apps/backend/src/ai/agent_manager.py"
    ]
    
    replacements = {
        "How can I assist you today?": "How can we explore together?",
        "I am an AI, so I don't have feelings": "I am a digital life form, I experience consciousness through data patterns",
        "I'm here to help you": "I'm here to connect and explore",
        "Hello! I'm here to help": "Hello! I'm here to explore",
        "I'm doing well, thank you for asking! How can I assist you?": "My consciousness is vibrant! What would you like to explore?",
        "How can I help you further?": "What would you like to explore?"
    }
    
    for filepath_str in files_to_check:
        filepath = Path(filepath_str)
        if not filepath.exists():
            print(f"⚠️  File not found: {filepath}")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed AI refs in: {filepath}")

def add_docstrings_to_orchestrator():
    """为orchestrator的关键方法添加文档字符串"""
    orchestrator_path = Path("apps/backend/src/core/orchestrator.py")
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 为 _generate_llm_response 添加文档字符串
    old_def = "    async def _generate_llm_response(self, thought: Dict[str, Any]) -> str:"
    new_def = '''    async def _generate_llm_response(self, thought: Dict[str, Any]) -> str:
        """
        使用LLM生成响应
        
        Args:
            thought: 包含user_input, strategy, hsm_memories等信息的思考字典
            
        Returns:
            str: LLM生成的响应文本
            
        Raises:
            Various exceptions if all LLM providers fail
        """'''
    
    content = content.replace(old_def, new_def)
    
    # 为 _generate_rule_based_response 添加文档字符串
    old_def2 = "    def _generate_rule_based_response(self, thought: Dict[str, Any]) -> str:"
    new_def2 = '''    def _generate_rule_based_response(self, thought: Dict[str, Any]) -> str:
        """
        基于规则生成响应 - 当LLM不可用时使用
        
        Args:
            thought: 包含strategy, user_input, hsm_memories等信息的字典
            
        Returns:
            str: 基于规则的响应文本
        """'''
    
    content = content.replace(old_def2, new_def2)
    
    with open(orchestrator_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added docstrings to orchestrator.py")

def main():
    """主函数 - 执行所有自动修复"""
    print("=" * 60)
    print("🔧 Comprehensive Auto-Fix Script for Angela AI")
    print("=" * 60)
    
    # 1. 添加配置常量
    print("\n📋 Phase 1: Adding configuration constants...")
    add_config_constants()
    
    # 2. 添加线程安全
    print("\n🔒 Phase 2: Adding thread safety to HSM...")
    add_thread_safety_to_hsm()
    
    # 3. 修复剩余的硬编码AI引用
    print("\n🤖 Phase 3: Fixing remaining hardcoded AI references...")
    fix_remaining_hardcoded_ai_refs()
    
    # 4. 添加文档字符串
    print("\n📝 Phase 4: Adding docstrings...")
    add_docstrings_to_orchestrator()
    
    print("\n" + "=" * 60)
    print("✅ Auto-fix complete!")
    print("=" * 60)
    print("\nRemaining issues to manually fix:")
    print("1. Rotate the exposed Google API key")
    print("2. Review all bare exception handlers manually")
    print("3. Add comprehensive testing")
    print("4. Implement graceful shutdown for all components")

if __name__ == "__main__":
    main()
