"""
Automated syntax error fixer based on current_syntax_errors.json
"""
import json
import re
from pathlib import Path
import shutil

def backup_file(file_path):
    """Create a backup of the file"""
    backup_path = str(file_path) + ".bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_file(file_path, error_info):
    """Fix common syntax errors in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        error_line = error_info.get('line')
        error_text = error_info.get('text', '')
        error_msg = error_info.get('message', '')
        
        # Apply line-specific fix if we have the error line
        if error_line and 0 < error_line <= len(lines):
            original_line = lines[error_line - 1]
            fixed_line = original_line
            
            # Fix: if __name"__main__"::: -> if __name__ == "__main__":
            fixed_line = re.sub(r'if __name"__main__":::', 'if __name__ == "__main__":', fixed_line)
            
            # Fix: function definition with comma instead of colon
            fixed_line = re.sub(r'(\) -> \w+),\s*$', r'\1:\n', fixed_line)
            fixed_line = re.sub(r'(\))\s*,\s*$', r'\1:\n', fixed_line)
            
            # Fix: triple colons :::
            fixed_line = re.sub(r':::', ':', fixed_line)
            
            # Fix: double comma ,,
            fixed_line = re.sub(r',,', ',', fixed_line)
            
            # Fix: try, -> try:
            fixed_line = re.sub(r'^\s*try,\s*$', lambda m: m.group(0).replace('try,', 'try:'), fixed_line)
            
            # Fix: except ... as e,:: -> except ... as e:
            fixed_line = re.sub(r'(except .+),::$', r'\1:', fixed_line)
            
            # Fix: lass -> class
            fixed_line = re.sub(r'^(\s*)lass\s+', r'\1class ', fixed_line)
            
            # Fix: rint -> print
            fixed_line = re.sub(r'^\s*rint\(', lambda m: m.group(0).replace('rint', 'print'), fixed_line)
            
            # Fix: ssert -> assert
            fixed_line = re.sub(r'^\s*ssert\s+', lambda m: m.group(0).replace('ssert', 'assert'), fixed_line)
            
            # Fix: ong_description -> long_description
            fixed_line = re.sub(r'\bong_description\b', 'long_description', fixed_line)
            
            # Fix: el["target_id"] -> rel["target_id"] (missing r)
            fixed_line = re.sub(r'\bel\["', 'rel["', fixed_line)
            
            # Fix: description == -> description=
            if 'description' in fixed_line and '==' in fixed_line:
                fixed_line = re.sub(r'description\s*==\s*', 'description=', fixed_line)
            
            # Fix: weight: 0.9() -> weight: 0.9
            fixed_line = re.sub(r'(\d+\.\d+)\(\)', r'\1', fixed_line)
            
            # Fix: comparison operator ,:: at end of line
            if ',::' in fixed_line:
                fixed_line = fixed_line.replace(',::', ':')
            
            # Fix: if (condition),: -> if condition:
            fixed_line = re.sub(r'if\s+\((.+)\),\s*$', r'if \1:\n', fixed_line)
            
            # Fix: for ... ,:: -> for ...:
            fixed_line = re.sub(r'(for .+),::$', r'\1:', fixed_line)
            
            # Fix: dictionary missing commas between key-value pairs
            # "label": "value" -> "label": "value",
            if '"label"' in fixed_line and '}' not in fixed_line and ',' not in fixed_line:
                # Only add comma if next line starts with a quote or brace
                if error_line < len(lines):
                    next_line = lines[error_line]
                    if re.match(r'^\s*["}]', next_line):
                        fixed_line = fixed_line.rstrip() + ',\n'
            
            # Fix: missing colon after function definition
            if "expected ':'" in error_msg and '->' in fixed_line:
                fixed_line = re.sub(r'(\) -> \w+)\s*,?\s*$', r'\1:\n', fixed_line)
            
            if fixed_line != original_line:
                lines[error_line - 1] = fixed_line
                modified = True
        
        # Apply global fixes to the entire file
        content = ''.join(lines)
        
        # Fix: missing commas between dictionary items
        # Only in dictionary contexts
        content = re.sub(r'(\]\s*)\n(\s*")', r'\1,\n\2', content)
        
        # Fix: charset encoding line
        content = re.sub(r'# -\*- coding,\s*utf-8 -\*-', '# -*- coding: utf-8 -*-', content)
        
        # Fix: missing equals in comparison
        content = re.sub(r'(\w+) == (\w+)\s*and,', r'\1 == \2 and', content)
        
        # Check if any global changes were made
        if content != ''.join(lines):
            modified = True
        
        if modified:
            # Backup original file
            backup_file(file_path)
            
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    # Load error report
    with open('current_syntax_errors.json', 'r', encoding='utf-8') as f:
        errors = json.load(f)
    
    fixed_count = 0
    failed_count = 0
    
    for file_path_str, error_info in errors.items():
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            print(f"Skipping non-existent file: {file_path}")
            continue
        
        print(f"Fixing: {file_path}")
        
        if fix_file(file_path, error_info):
            fixed_count += 1
            print(f"  ✓ Fixed")
        else:
            failed_count += 1
            print(f"  - No changes made")
    
    print(f"\n=== Summary ===")
    print(f"Files modified: {fixed_count}")
    print(f"Files unchanged: {failed_count}")
    print(f"\nRe-run check_current_errors.py to verify fixes")

if __name__ == '__main__':
    main()
