import os
import re

file_path = "D:\\Projects\\Unified-AI-Project\\apps\\backend\\src\\core\\hsp\\connector.py"

def clean_and_reindent_python_file(filepath):
    with open(filepath, 'rb') as f:
        content_bytes = f.read()

    # Decode as UTF-8, handling potential errors
    content = content_bytes.decode('utf-8', errors='ignore')

    # Normalize line endings to Unix style
    content = content.replace('\r\n', '\n')
    content = content.replace('\r', '\n')

    # Replace tabs with 4 spaces
    content = content.replace('\t', '    ')

    reindented_lines = []
    indent_level = 0
    for line in content.splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            reindented_lines.append('')
            continue

        # Adjust indent level based on keywords (simple heuristic)
        if stripped_line.startswith(('class ', 'def ', 'async def ', 'if ', 'for ', 'while ', 'with ', 'try:', 'except', 'finally', 'elif', 'else')):
            if stripped_line.endswith(':'):
                # If it's a new block, increase indent
                if not line.startswith(' ' * indent_level): # Only increase if not already indented
                    indent_level += 1
            else:
                # If it's an 'else' or 'elif' or 'except' for an existing block, decrease then re-indent
                if line.startswith(' ' * (indent_level * 4)): # Check if current line is indented at current level
                    indent_level -= 1
        elif stripped_line.startswith(('return ', 'pass', 'break', 'continue', 'raise')):
            # These usually signal end of a logical block, so decrease indent
            if line.startswith(' ' * (indent_level * 4)):
                indent_level -= 1
        
        # Ensure indent level doesn't go below zero
        indent_level = max(0, indent_level)

        reindented_lines.append(' ' * (indent_level * 4) + stripped_line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(reindented_lines))

    print(f"Cleaned and re-indented: {filepath}")

clean_and_reindent_python_file(file_path)
