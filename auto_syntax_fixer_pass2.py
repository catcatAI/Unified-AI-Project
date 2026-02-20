"""
Second-pass automated syntax error fixer for remaining complex errors
"""
import json
import re
from pathlib import Path
import shutil


def fix_file_pass2(file_path, error_info):
    """Fix remaining complex syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix unterminated triple-quoted strings - look for odd number of """
        # This is complex, so let's fix known patterns
        triple_quote_count = content.count('"""')
        if triple_quote_count % 2 != 0:
            # Find and fix unterminated strings
            lines = content.split('\n')
            in_docstring = False
            fixed_lines = []
            for i, line in enumerate(lines):
                if '"""' in line:
                    count = line.count('"""')
                    if count == 1:
                        in_docstring = not in_docstring
                    # If count is 2, it's a single-line docstring
                fixed_lines.append(line)
            
            # If still in docstring at end, close it
            if in_docstring:
                # Find the last """ and add closing
                for i in range(len(fixed_lines) - 1, -1, -1):
                    if '"""' in fixed_lines[i]:
                        # Add closing """ after a reasonable distance
                        insert_pos = min(i + 10, len(fixed_lines))
                        fixed_lines.insert(insert_pos, '"""')
                        break
                content = '\n'.join(fixed_lines)
        
        # Fix: unexpected indent - remove leading spaces from specific lines
        content = re.sub(r'^\s+(rint\()', r'\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(ssert\s)', r'\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(ound_)', r'f\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(yped_)', r't\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(esult)', r'r\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(ong_)', r'l\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(ut_)', r'o\1', content, flags=re.MULTILINE)
        content = re.sub(r'^\s+(f \()', r'if (', content, flags=re.MULTILINE)
        
        # Fix missing characters at line start
        content = re.sub(r'^(\s*)rint\(', r'\1print(', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)ssert\s', r'\1assert ', content, flags=re.MULTILINE)
        content = re.sub(r'\bound_rel', 'found_rel', content)
        content = re.sub(r'\bout_ids', 'out_ids', content)
        content = re.sub(r'\bout_docs', 'out_docs', content)
        content = re.sub(r'\byped_dict', 'typed_dict', content)
        content = re.sub(r'\besult\[', 'result[', content)
        content = re.sub(r'\bong_description', 'long_description', content)
        
        # Fix: invalid syntax patterns
        # Fix: dict["key"] {"value"} -> dict["key"] = {"value"}
        content = re.sub(r'(\w+\[.+\])\s*\{', r'\1 = {', content)
        
        # Fix: if (condition),: -> if condition:
        content = re.sub(r'if\s+\(([^)]+)\)\s*,\s*:', r'if \1:', content)
        
        # Fix: for item in items,:: -> for item in items:
        content = re.sub(r'(for .+ in .+)\s*,\s*:', r'\1:', content)
        
        # Fix: def func(),: -> def func():
        content = re.sub(r'(def \w+\([^)]*\))\s*,\s*:', r'\1:', content)
        
        # Fix: class Name,: -> class Name:
        content = re.sub(r'(class \w+)\s*,\s*:', r'\1:', content)
        
        # Fix: except ... ,:: -> except ...:
        content = re.sub(r'(except [^:]+)\s*,\s*:', r'\1:', content)
        
        # Fix: try,: -> try:
        content = re.sub(r'^(\s*)try\s*,\s*:', r'\1try:', content, flags=re.MULTILINE)
        
        # Fix: comparison == instead of assignment =
        content = re.sub(r'(\w+)\s*==\s*==\s*', r'\1 == ', content)
        content = re.sub(r'^\s*(\w+)\s*==\s*([^=])', r'\1 = \2', content, flags=re.MULTILINE)
        
        # Fix: missing 'r' in 'rel'
        content = re.sub(r'\bel\["', 'rel["', content)
        
        # Fix: unmatched ')' - look for patterns like func())
        # This is hard to fix automatically, skip for now
        
        # Fix: perhaps forgot comma - add commas in dict/list contexts
        # Look for patterns like: ] newline whitespace "
        content = re.sub(r'(\])\n(\s+)"', r'\1,\n\2"', content)
        
        # Fix double colons at end
        content = re.sub(r':::\s*$', ':', content, flags=re.MULTILINE)
        content = re.sub(r',::$', ':', content, flags=re.MULTILINE)
        
        # Fix double comma
        content = re.sub(r',,', ',', content)
        
        # Fix spacing around operators
        content = re.sub(r'\s+,\s+', ', ', content)
        
        # Check if any changes were made
        if content != original_content:
            # Backup original file
            backup_path = str(file_path) + ".bak2"
            shutil.copy2(file_path, backup_path)
            
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
            continue
        
        if fix_file_pass2(file_path, error_info):
            fixed_count += 1
            print(f"✓ {file_path}")
        else:
            failed_count += 1
    
    print(f"\n=== Pass 2 Summary ===")
    print(f"Files modified: {fixed_count}")
    print(f"Files unchanged: {failed_count}")
    print(f"\nRe-run check_current_errors.py to verify fixes")


if __name__ == '__main__':
    main()
