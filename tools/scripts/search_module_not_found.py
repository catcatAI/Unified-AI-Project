import os
import re
from typing import List

def search_module_not_found(directory: str) -> None:
    """Search for '# Module not found' comments in Python files"""
    pattern = r'= None.*#.*Module not found'
    
    for root, dirs, files in os.walk(directory):
        # Type annotations for os.walk return values
        root: str
        dirs: List[str]
        files: List[str]
        
        # Skip node_modules and other unnecessary directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git']]
        
        for file in files:
            file: str  # Type annotation for file variable
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines: List[str] = f.readlines()
                        for i, line in enumerate(lines, 1):
                            i: int  # Type annotation for line number
                            line: str  # Type annotation for line content
                            if re.search(pattern, line):
                                _ = print(f"{file_path}:{i}: {line.strip()}")
                except Exception:
                    # Skip files that can't be read
                    pass

if __name__ == "__main__":
    _ = search_module_not_found(".")