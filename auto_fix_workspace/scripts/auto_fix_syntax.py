import os
import re
import subprocess

def fix_file_syntax(file_path):
    """修復文件中的語法錯誤和縮進問題"""
    print(f"Processing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存原始內容
        original_content = content
        
        # 修復函數調用後面的冒號問題
        # 例如: logger.info("message"):
        content = re.sub(r'(\w+\s*\([^)]*\))\s*:', r'\1', content)
        
        # 修復 super() 調用
        content = re.sub(r'super\s*\.', 'super().', content)
        
        # 修復不正確的縮進
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 移除行尾的多餘空格
            line = line.rstrip()
            
            # 修復縮進問題 - 將不正確的縮進統一為4個空格
            # 這裡我們只處理明顯的縮進錯誤
            if line.startswith('    ') and line[4:].startswith('    ') and not line[8:].startswith(' '):
                # 修正8個空格縮進為4個空格的情況（當不是繼續縮進時）
                if not any(keyword in line for keyword in ['class ', 'def ', 'if ', 'for ', 'while ', 'try:', 'except', 'else:', 'elif ']):
                    line = line[4:]  # 移除4個空格
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # 修復函數調用後的括號問題
        content = re.sub(r'(\w+)\s*\(\s*\)\s*:', r'\1()', content)
        content = re.sub(r'(\w+)\s*\(\s*([^)]*)\s*\)\s*:', r'\1(\2)', content)
        
        # 修復類型註解中的問題
        content = re.sub(r'(\w+)\s*:\s*Any\s*:', r'\1: Any', content)
        content = re.sub(r'(\w+)\s*:\s*str\s*:', r'\1: str', content)
        content = re.sub(r'(\w+)\s*:\s*int\s*:', r'\1: int', content)
        content = re.sub(r'(\w+)\s*:\s*bool\s*:', r'\1: bool', content)
        content = re.sub(r'(\w+)\s*:\s*Dict\[.*\]\s*:', r'\1: Dict[...]', content)
        content = re.sub(r'(\w+)\s*:\s*List\[.*\]\s*:', r'\1: List[...]', content)
        
        # 修復註釋中的冒號
        content = re.sub(r'(#.*)\s*:', r'\1', content)
        
        # 如果內容有變化，則寫入文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed syntax issues in {file_path}")
            return True
        else:
            print(f"No issues found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def get_modified_files():
    """獲取所有修改過的Python文件"""
    try:
        # 使用git獲取修改過的文件
        result = subprocess.run(['git', 'diff', '--name-only'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        files = result.stdout.strip().split('\n')
        # 過濾出Python文件
        py_files = [f for f in files if f.endswith('.py') and os.path.exists(f)]
        return py_files
    except Exception as e:
        print(f"Error getting modified files: {e}")
        return []

def main():
    """主函數"""
    print("Starting automatic syntax fix...")
    
    # 獲取所有修改過的Python文件
    modified_files = get_modified_files()
    
    if not modified_files:
        print("No modified Python files found.")
        return
    
    print(f"Found {len(modified_files)} modified Python files.")
    
    # 修復每個文件
    fixed_count = 0
    for file_path in modified_files:
        if fix_file_syntax(file_path):
            fixed_count += 1
    
    print(f"Fixed syntax issues in {fixed_count} files.")
    print("Automatic syntax fix completed.")

if __name__ == "__main__":
    main()