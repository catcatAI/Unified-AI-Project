#!/usr/bin/env python3
"""Fix imports that were placed inside docstrings."""
import ast
import os
import subprocess

def main():
    # Get modified files
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        timeout=15
    )
    files=[f.strip() for f in result.stdout.strip().split('\n') if f.strip() and f.endswith('.py')]
    
    fixed=0
    for filepath in files:
        content = open(filepath, 'r', encoding='utf-8').read()
        
        if 'from core.utils import safe_error' not in content:
            continue
        
        lines = content.split('\n')
        import_line_idx = -1
        
        for i, line in enumerate(lines):
            if line.strip() == 'from core.utils import safe_error':
                import_line_idx = i
                break
        
        if import_line_idx < 0:
            continue
        
        # Check if import is inside a docstring (between """ and """)
        # Count """ before this line
        docstring_count=0
        in_docstring=False
        for j in range(import_line_idx):
            stripped = lines[j].strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring=True
                    remainder = stripped[3:]
                    delim = stripped[:3]
                    if delim in remainder:
                        in_docstring=False
                else:
                    in_docstring=False
        
        if in_docstring:
            # Import is inside docstring! Move it after the docstring end.
            # Find the closing """
            end_idx = -1
            for j in range(import_line_idx + 1, len(lines)):
                stripped = lines[j].strip()
                if '"""' in stripped or "'''" in stripped:
                    end_idx = j
                    break
            
            if end_idx < 0:
                print(f"  SKIP {filepath}: can't find closing docstring")
                continue
            
            # Remove the import line
            del lines[import_line_idx]
            
            # Find where to insert: after the closing """
            insert_idx = end_idx  # after the closing docstring line
            
            # Find the first non-blank line after closing docstring
            # to determine if we need a blank line
            has_code_after=False
            for j in range(insert_idx + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#') and not lines[j].strip().startswith('"""') and not lines[j].strip().startswith("'''"):
                    has_code_after=True
                    break
            
            if has_code_after:
                lines.insert(insert_idx + 1, 'from core.utils import safe_error')
                # Add blank line after if next line is not blank
                if insert_idx + 2 < len(lines) and lines[insert_idx + 2].strip():
                    lines.insert(insert_idx + 2, '')
            else:
                # No code after docstring - insert before the next code
                lines.insert(insert_idx + 1, 'from core.utils import safe_error')
            
            new_content='\n'.join(lines)
            
            # Verify it compiles
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                print(f"  ERROR {filepath}: syntax error after fix: {e}")
                continue
            
            open(filepath, 'w', encoding='utf-8').write(new_content)
            print(f"  FIXED {filepath}: moved import outside docstring")
            fixed += 1
        else:
            pass  # Import is already at top level, OK
    
    print(f"\nDone: {fixed} files fixed")

if __name__ == '__main__':
    main()
