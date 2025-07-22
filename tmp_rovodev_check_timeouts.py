#!/usr/bin/env python3
"""
檢查測試文件的超時設置並添加缺少的超時
"""
import os
import re
from pathlib import Path

def check_and_add_timeouts():
    """檢查並添加超時設置"""
    test_dir = Path("tests")
    files_updated = []
    files_checked = []
    
    # 超時設置規則
    timeout_rules = {
        'basic': 5,      # 基本單元測試
        'integration': 10,  # 集成測試
        'async': 10,     # 異步測試
        'api': 15,       # API測試
        'service': 15,   # 服務測試
    }
    
    # 特殊文件的超時設置
    special_files = {
        'test_main_api_server.py': 'api',
        'test_llm_interface.py': 'service', 
        'test_creative_writing_agent.py': 'integration',
        'test_data_analysis_agent.py': 'integration',
        'test_hsp_connector.py': 'integration',
        'test_mcp_connector.py': 'integration',
        'test_sandbox_executor.py': 'service',
        'test_vision_service.py': 'service',
        'test_audio_service.py': 'service',
    }
    
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                file_path = Path(root) / file
                files_checked.append(str(file_path))
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 跳過已經有超時設置的文件
                    if '@pytest.mark.timeout' in content:
                        print(f"✓ {file_path} - 已有超時設置")
                        continue
                    
                    # 檢查是否為pytest測試文件
                    if 'import pytest' not in content and 'def test_' not in content:
                        print(f"- {file_path} - 不是pytest測試文件")
                        continue
                    
                    # 確定超時類型
                    timeout_type = 'basic'
                    if file in special_files:
                        timeout_type = special_files[file]
                    elif 'integration' in str(file_path):
                        timeout_type = 'integration'
                    elif 'async def test_' in content or '@pytest.mark.asyncio' in content:
                        timeout_type = 'async'
                    elif 'api' in file.lower() or 'server' in file.lower():
                        timeout_type = 'api'
                    elif 'service' in file.lower():
                        timeout_type = 'service'
                    
                    timeout_seconds = timeout_rules[timeout_type]
                    
                    # 添加超時設置
                    lines = content.split('\n')
                    modified = False
                    
                    for i, line in enumerate(lines):
                        # 匹配測試函數定義
                        if re.match(r'^\s*(async\s+)?def\s+test_', line):
                            # 檢查前面是否已經有裝飾器
                            j = i - 1
                            has_timeout = False
                            while j >= 0 and (lines[j].strip().startswith('@') or not lines[j].strip()):
                                if '@pytest.mark.timeout' in lines[j]:
                                    has_timeout = True
                                    break
                                j -= 1
                            
                            if not has_timeout:
                                # 添加超時裝飾器
                                indent = len(line) - len(line.lstrip())
                                timeout_decorator = ' ' * indent + f'@pytest.mark.timeout({timeout_seconds})'
                                lines.insert(i, timeout_decorator)
                                modified = True
                    
                    if modified:
                        # 確保導入pytest
                        if 'import pytest' not in content:
                            # 找到第一個import語句後插入
                            for i, line in enumerate(lines):
                                if line.startswith('import ') or line.startswith('from '):
                                    lines.insert(i + 1, 'import pytest')
                                    break
                        
                        # 寫回文件
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(lines))
                        
                        files_updated.append(str(file_path))
                        print(f"✓ {file_path} - 已添加 {timeout_seconds}s 超時 ({timeout_type})")
                    else:
                        print(f"- {file_path} - 無需修改")
                        
                except Exception as e:
                    print(f"✗ {file_path} - 處理錯誤: {e}")
    
    print(f"\n總結:")
    print(f"檢查文件: {len(files_checked)}")
    print(f"更新文件: {len(files_updated)}")
    
    if files_updated:
        print(f"\n已更新的文件:")
        for file in files_updated:
            print(f"  - {file}")

if __name__ == '__main__':
    check_and_add_timeouts()