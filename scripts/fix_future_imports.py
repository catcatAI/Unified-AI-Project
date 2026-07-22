#!/usr/bin/env python3
"""Fix import ordering: from core.utils import safe_error must be AFTER from __future__ imports."""
import ast
import os
import subprocess

def main():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        timeout=15
    )
    files=[f.strip() for f in result.stdout.strip().split('\n') if f.strip() and f.endswith('.py')]
    
    fixed=0
    for filepath in sorted(files):
        content = open(filepath, 'r', encoding='utf-8').read()
        lines = content.split('\n')
        
        # Find positions
        future_idx = -1
        safe_idx = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('from __future__') and 'import' in stripped:
                future_idx = i
            elif stripped == 'from core.utils import safe_error':
                safe_idx = i
        
        if future_idx < 0 or safe_idx < 0:
            continue
        
        if safe_idx < future_idx:
            # Move safe_error import to after the future import
            # Remove it
            line_to_move = lines.pop(safe_idx)
            
            # Recalculate future_idx since list shifted
            future_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('from __future__') and 'import' in line.strip():
                    future_idx = i
                    break
            
            # Insert after the future import line
            insert_at = future_idx + 1
            # Add blank line if needed
            if insert_at < len(lines) and lines[insert_at].strip():
                lines.insert(insert_at, '')
                insert_at += 1
            lines.insert(insert_at, line_to_move)
            
            new_content='\n'.join(lines)
            
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                print(f"  ERROR {filepath}: {e}")
                continue
            
            open(filepath, 'w', encoding='utf-8').write(new_content)
            print(f"  FIXED {filepath}: moved safe_error after __future__ import")
            fixed += 1
    
    print(f"\nDone: {fixed} files fixed")

if __name__ == '__main__':
    main()
