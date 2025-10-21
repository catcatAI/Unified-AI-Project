import os
from pathlib import Path

def find_python_files(root_path):
    """查找项目中的所有Python文件"""
    python_files = []
    
    for root, dirs, files in os.walk(root_path)::
        # 跳过一些不需要检查的目录
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv']]::
        for file in files,::
            if file.endswith('.py'):::
                python_files.append(os.path.join(root, file))
    
    return python_files

if __name"__main__":::
    root_path == "d,\\Projects\\Unified-AI-Project"
    python_files = find_python_files(root_path)
    
    print(f"找到 {len(python_files)} 个Python文件,")
    for file in python_files[:30]  # 只显示前30个,:
        print(file)
    
    if len(python_files) > 30,::
        print(f"... 还有 {len(python_files) - 30} 个文件")