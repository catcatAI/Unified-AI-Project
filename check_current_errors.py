"""
Quick syntax checker for remaining_errors.json files
"""
import json
import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """Check if a Python file has syntax errors"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return {
            'type': 'SyntaxError',
            'message': str(e),
            'line': e.lineno,
            'offset': e.offset,
            'text': e.text
        }
    except IndentationError as e:
        return {
            'type': 'IndentationError',
            'message': str(e),
            'line': e.lineno,
            'offset': e.offset,
            'text': e.text
        }
    except Exception as e:
        return {
            'type': 'OtherError',
            'message': str(e)
        }

def main():
    # Load remaining_errors.json
    with open('data_archive/remaining_errors.json', 'r', encoding='utf-8') as f:
        files = json.load(f)
    
    errors = {}
    checked = 0
    error_count = 0
    
    for file_path in files:
        # Convert path to absolute
        abs_path = Path(file_path.replace('.\\', ''))
        
        if not abs_path.exists():
            continue
            
        if not abs_path.suffix == '.py':
            continue
        
        checked += 1
        error = check_syntax(abs_path)
        
        if error:
            error_count += 1
            errors[str(abs_path)] = error
            
        if checked % 100 == 0:
            print(f"Checked {checked} files, found {error_count} errors...", file=sys.stderr)
    
    print(f"\nTotal files checked: {checked}")
    print(f"Total files with errors: {error_count}")
    print(f"\nFiles with syntax errors:")
    
    # Group by error type
    syntax_errors = []
    indent_errors = []
    other_errors = []
    
    for file_path, error in errors.items():
        if error['type'] == 'SyntaxError':
            syntax_errors.append((file_path, error))
        elif error['type'] == 'IndentationError':
            indent_errors.append((file_path, error))
        else:
            other_errors.append((file_path, error))
    
    print(f"\n=== SyntaxError ({len(syntax_errors)}) ===")
    for file_path, error in syntax_errors[:20]:  # Show first 20
        print(f"{file_path}:{error.get('line', '?')}")
        print(f"  {error['message']}")
    
    print(f"\n=== IndentationError ({len(indent_errors)}) ===")
    for file_path, error in indent_errors[:20]:  # Show first 20
        print(f"{file_path}:{error.get('line', '?')}")
        print(f"  {error['message']}")
    
    print(f"\n=== Other Errors ({len(other_errors)}) ===")
    for file_path, error in other_errors[:10]:
        print(f"{file_path}")
        print(f"  {error['message']}")
    
    # Save full report to JSON
    with open('current_syntax_errors.json', 'w', encoding='utf-8') as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)
    
    print(f"\nFull error report saved to current_syntax_errors.json")

if __name__ == '__main__':
    main()
