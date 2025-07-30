"""
這個腳本用於為測試文件添加超時設置。
支持 unittest 和 pytest 風格的測試。

用法：
    python scripts/add_test_timeouts.py
"""
import os
import re
import ast
from pathlib import Path

# 測試文件的基本目錄
TEST_DIR = Path(__file__).parent.parent / 'tests'

# 不同類型測試的超時設置（秒）
TIMEOUTS = {
    'basic': 5,       # 基本單元測試
    'integration': 10,  # 集成測試
    'performance': 30,  # 性能測試
}

def is_pytest_test(file_path):
    """檢查文件是否包含 pytest 風格的測試"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return '@pytest.mark.' in content or 'import pytest' in content

def add_pytest_timeout(file_path, timeout_seconds):
    """為 pytest 測試文件添加超時裝飾器"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 匹配測試函數定義
        if re.match(r'^(async\s+)?def\s+test_', line):
            # 檢查是否已經有超時裝飾器
            has_timeout = False
            j = i - 1
            while j >= 0 and (lines[j].strip().startswith('@') or not lines[j].strip()):
                if '@pytest.mark.timeout' in lines[j]:
                    has_timeout = True
                    break
                j -= 1
            
            if not has_timeout:
                # 添加超時裝飾器
                lines.insert(i, f'@pytest.mark.timeout({timeout_seconds})\n')
                i += 1  # 因為我們添加了一行
                modified = True
        i += 1
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Updated {file_path} with {timeout_seconds}s timeout")
        return True
    
    print(f"No test functions found in {file_path}")
    return False

def add_unittest_timeout(file_path, timeout_seconds):
    """為 unittest 測試文件添加超時設置"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經有超時設置
    if 'timeout=' in content:
        print(f"Skipping {file_path} - already has timeout setting")
        return False
    
    # 解析 AST 找到測試方法
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Error parsing {file_path}: {e}")
        return False
    
    modified = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
            for item in node.body:
                if (isinstance(item, ast.FunctionDef) and 
                    item.name.startswith('test_')):
                    # 檢查是否已經有裝飾器
                    has_decorator = any(
                        isinstance(dec, ast.Call) and 
                        isinstance(dec.func, ast.Attribute) and 
                        dec.func.attr == 'timeout'
                        for dec in item.decorator_list
                    )
                    
                    if not has_decorator:
                        # 添加超時裝飾器
                        item.decorator_list.append(
                            ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='unittest', ctx=ast.Load()),
                                    attr='timeout',
                                    ctx=ast.Load()
                                ),
                                args=[ast.Num(n=timeout_seconds)],
                                keywords=[]
                            )
                        )
                        modified = True
    
    if modified:
        # 生成修改後的代碼
        import astunparse
        new_content = astunparse.unparse(tree)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Updated {file_path} with {timeout_seconds}s timeout")
        return True
    
    print(f"No test methods found in {file_path}")
    return False

def process_test_file(file_path):
    """處理單個測試文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 確定超時時間
        timeout_seconds = TIMEOUTS['integration']  # 默認使用集成測試超時
        
        if is_pytest_test(file_path):
            return add_pytest_timeout(file_path, timeout_seconds)
        else:
            return add_unittest_timeout(file_path, timeout_seconds)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函數"""
    # 安裝 astunparse 如果沒有安裝
    try:
        import astunparse
    except ImportError:
        print("Installing astunparse...")
        import subprocess
        subprocess.check_call(["pip", "install", "astunparse"])
        import astunparse
    
    # 查找所有測試文件
    test_files = []
    for root, _, files in os.walk(TEST_DIR):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    # 處理每個測試文件
    updated_count = 0
    for test_file in test_files:
        if process_test_file(test_file):
            updated_count += 1
    
    print(f"\nUpdated {updated_count} test files with timeout settings")

if __name__ == '__main__':
    main()
