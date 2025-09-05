import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

# 相对导入映射
RELATIVE_IMPORT_MAPPINGS = [
    # core_ai 相对导入修复
    (r'from\s+\.\s+core_ai\s*\.\s*agent_manager\s+import\s+AgentManager', r'from apps.backend.src.ai.agents.base import AgentManager'),
    (r'from\s+\.\s+core_ai\s*\.\s*dialogue\s*\.\s*dialogue_manager\s+import\s+DialogueManager', r'from apps.backend.src.ai.dialogue import dialogue_manager'),
    (r'from\s+\.\s+core_ai\s*\.\s*learning\s*\.\s*learning_manager\s+import\s+LearningManager', r'from apps.backend.src.ai.learning import learning_manager'),
    (r'from\s+\.\s+core_ai\s*\.\s*learning\s*\.\s*fact_extractor_module\s+import\s+FactExtractorModule', r'from apps.backend.src.ai.learning import fact_extractor_module'),
    (r'from\s+\.\s+core_ai\s*\.\s*learning\s*\.\s*content_analyzer_module\s+import\s+ContentAnalyzerModule', r'from apps.backend.src.ai.learning import content_analyzer_module'),
    (r'from\s+\.\s+core_ai\s*\.\s*service_discovery\s*\.\s*service_discovery_module\s+import\s+ServiceDiscoveryModule', r'from apps.backend.src.ai.discovery import service_discovery_module'),
    (r'from\s+\.\s+core_ai\s*\.\s*trust_manager\s*\.\s*trust_manager_module\s+import\s+TrustManager', r'from apps.backend.src.ai.trust import trust_manager_module'),
    (r'from\s+\.\s+core_ai\s*\.\s*memory\s*\.\s*ham_memory_manager\s+import\s+HAMMemoryManager', r'from apps.backend.src.ai.memory import ham_memory_manager'),
    (r'from\s+\.\s+core_ai\s*\.\s*personality\s*\.\s*personality_manager\s+import\s+PersonalityManager', r'from apps.backend.src.ai.personality import personality_manager'),
    (r'from\s+\.\s+core_ai\s*\.\s*emotion_system\s+import\s+EmotionSystem', r'from apps.backend.src.ai.emotion import emotion_system'),
    (r'from\s+\.\s+core_ai\s*\.\s*crisis_system\s+import\s+CrisisSystem', r'from apps.backend.src.ai.crisis import crisis_system'),
    (r'from\s+\.\s+core_ai\s*\.\s*time_system\s+import\s+TimeSystem', r'from apps.backend.src.ai.time import time_system'),
    (r'from\s+\.\s+core_ai\s*\.\s*formula_engine\s+import\s+FormulaEngine', r'from apps.backend.src.ai.formula_engine import formula_engine'),
    (r'from\s+\.\s+core_ai\s*\.\s*demo_learning_manager\s+import\s+DemoLearningManager', r'from apps.backend.src.ai.learning import demo_learning_manager'),
    
    # tools 相对导入修复
    (r'from\s+\.\s+tools\s*\.\s*tool_dispatcher\s+import\s+ToolDispatcher', r'from apps.backend.src.core.tools import tool_dispatcher'),
    
    # services 相对导入修复
    (r'from\s+\.\s+services\s*\.\s*multi_llm_service\s+import\s+MultiLLMService', r'from apps.backend.src.core.services import multi_llm_service'),
    (r'from\s+\.\s+services\s*\.\s*ai_virtual_input_service\s+import\s+AIVirtualInputService', r'from apps.backend.src.core.services import ai_virtual_input_service'),
    (r'from\s+\.\s+services\s*\.\s*audio_service\s+import\s+AudioService', r'from apps.backend.src.core.services import audio_service'),
    (r'from\s+\.\s+services\s*\.\s*vision_service\s+import\s+VisionService', r'from apps.backend.src.core.services import vision_service'),
    (r'from\s+\.\s+services\s*\.\s*resource_awareness_service\s+import\s+ResourceAwarenessService', r'from apps.backend.src.core.services import resource_awareness_service'),
    
    # hsp 相对导入修复
    (r'from\s+\.\s+hsp\s*\.\s*connector\s+import\s+HSPConnector', r'from apps.backend.src.core.hsp import connector'),
    
    # mcp 相对导入修复
    (r'from\s+\.\s+mcp\s*\.\s*connector\s+import\s+MCPConnector', r'from apps.backend.src.mcp import connector'),
    
    # shared 相对导入修复
    (r'from\s+\.\s+shared\s*\.\s*error\s+import\s+ProjectError', r'from apps.backend.src.core.shared import error'),
    
    # system 相对导入修复
    (r'from\s+\.\s+system\s+import\s+\(', r'from apps.backend.src.system import ('),
]

def fix_imports_in_file(file_path: Path):
    """修复文件中的相对导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        fixes_made = []
        
        # 应用相对导入映射
        for pattern, replacement in RELATIVE_IMPORT_MAPPINGS:
            matches = re.findall(pattern, content)
            if matches:
                old_content = content
                content = re.sub(pattern, replacement, content)
                if old_content != content:
                    fixes_made.append(f"相对导入修复: {pattern} -> {replacement}")
        
        # 如果内容有变化，写入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 修复了文件 {file_path}")
            for fix in fixes_made:
                print(f"  - {fix}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"✗ 修复文件 {file_path} 时出错: {e}")
        return False

def fix_core_services():
    """修复 core_services.py 文件"""
    core_services_path = SRC_DIR / "core_services.py"
    if core_services_path.exists():
        print("修复 core_services.py...")
        return fix_imports_in_file(core_services_path)
    return False

def main():
    print("=== 手动修复相对导入 ===")
    if fix_core_services():
        print("✓ core_services.py 修复成功")
    else:
        print("ℹ core_services.py 无需修复或修复失败")
    print("=== 修复完成 ===")

if __name__ == "__main__":
    main()