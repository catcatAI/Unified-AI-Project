"""
這個腳本用於為 pytest 測試文件添加超時設置。

用法：
    python scripts/add_pytest_timeouts.py
"""
import os
import re
from pathlib import Path

# 測試文件的基本目錄
TEST_DIR = Path(__file__).parent.parent / 'tests'

# 不同類型測試的超時設置（秒）
TIMEOUTS = {
    'basic': 5,       # 基本單元測試
    'integration': 10,  # 集成測試
    'performance': 30,  # 性能測試
}

# 特殊文件或目錄的超時設置
SPECIAL_TIMEOUTS = {
    'test_ham_memory_manager.py': 'integration',
    'test_dialogue_manager.py': 'integration',
    'test_formula_engine.py': 'integration',
    'test_lightweight_code_model.py': 'integration',
    'test_tonal_repair_engine.py': 'integration',
    'test_creation_engine.py': 'integration',
    'test_evaluator.py': 'integration',
    'test_fragmenta_orchestrator.py': 'integration',
    'test_hsp_connector.py': 'integration',
    'test_hsp_integration.py': 'integration',
    'test_knowledge_update.py': 'integration',
    'test_self_improvement.py': 'integration',
    'test_cli.py': 'integration',
    'test_electron_app.py': 'integration',
    'test_search_engine.py': 'integration',
    'test_ai_virtual_input_service.py': 'integration',
    'test_audio_service.py': 'integration',
    'test_llm_interface.py': 'integration',
    'test_main_api_server.py': 'integration',
    'test_main_api_server_hsp.py': 'integration',
    'test_node_services.py': 'integration',
    'test_sandbox_executor.py': 'integration',
    'test_vision_service.py': 'integration',
    'test_startup_manager.py': 'integration',
    'test_code_understanding_tool.py': 'integration',
    'test_logic_model.py': 'integration',
    'test_math_model.py': 'integration',
    'test_translation_model.py': 'integration',
    'test_daily_language_model.py': 'integration',
    'test_content_analyzer_module.py': 'integration',
    'test_ham_lis_cache.py': 'integration',
    'test_meta_formulas.py': 'integration',
    'test_personality_manager.py': 'integration',
    'test_service_discovery_module.py': 'integration',
    'test_crisis_system.py': 'integration',
    'test_emotion_system.py': 'integration',
    'test_time_system.py': 'integration',
    'test_element_layer.py': 'integration',
    'test_vision_tone_inverter.py': 'integration',
    'test_resource_awareness_service.py': 'integration',
}

def get_timeout_for_file(file_path):
    """根據文件路徑返回適當的超時設置"""
    file_name = os.path.basename(file_path)
    
    # 檢查特殊文件設置
    if file_name in SPECIAL_TIMEOUTS:
        timeout_type = SPECIAL_TIMEOUTS[file_name]
        return TIMEOUTS.get(timeout_type, 5)  # 默認5秒
    
    # 根據路徑判斷
    path_parts = Path(file_path).parts
    if 'integration' in path_parts:
        return TIMEOUTS['integration']
    if 'performance' in path_parts:
        return TIMEOUTS['performance']
    
    return TIMEOUTS['basic']  # 默認基本超時

def add_timeout_to_file(file_path):
    """為測試文件添加超時裝飾器"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否已經有超時設置
        if '@pytest.mark.timeout' in content:
            print(f"Skipping {file_path} - already has timeout decorator")
            return False
        
        # 檢查是否為 pytest 測試文件
        if 'import pytest' not in content and '@pytest' not in content:
            print(f"Skipping {file_path} - not a pytest test file")
            return False
        
        timeout_seconds = get_timeout_for_file(file_path)
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # 匹配測試函數定義
            if re.match(r'^((async\s+)?def\s+test_|@pytest.mark.parametrize.*\n\s*def\s+test_)', line.strip()):
                # 檢查是否已經有裝飾器
                j = i - 1
                has_timeout = False
                while j >= 0 and (lines[j].strip().startswith('@') or not lines[j].strip()):
                    if '@pytest.mark.timeout' in lines[j]:
                        has_timeout = True
                        break
                    j -= 1
                
                if not has_timeout:
                    # 添加超時裝飾器
                    lines.insert(i, f'@pytest.mark.timeout({timeout_seconds})')
                    modified = True
        
        if modified:
            # 寫回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print(f"Updated {file_path} with {timeout_seconds}s timeout")
            return True
        
        print(f"No test functions found in {file_path}")
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函數"""
    # 查找所有測試文件
    test_files = []
    for root, _, files in os.walk(TEST_DIR):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    # 為每個測試文件添加超時
    updated_count = 0
    for test_file in test_files:
        if add_timeout_to_file(test_file):
            updated_count += 1
    
    print(f"\nUpdated {updated_count} test files with timeout decorators")

if __name__ == '__main__':
    main()
