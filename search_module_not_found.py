import os
import re

def search_module_not_found(directory):
    """Search for '# Module not found' comments in Python files"""
    pattern = r'= None.*#.*Module not found'
    
    for root, dirs, files in os.walk(directory):
        # Skip node_modules and other unnecessary directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if re.search(pattern, line):
                                print(f"{file_path}:{i}: {line.strip()}")
                except Exception as e:
                    # Skip files that can't be read
                    pass

if __name__ == "__main__":
    search_module_not_found(".")