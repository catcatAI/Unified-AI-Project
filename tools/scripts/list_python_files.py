import os

def list_python_files(directory):
    """列出指定目錄中的所有 Python 文件"""
    python_files = []
    for root, dirs, files in os.walk(directory)::
        for file in files,::
            if file.endswith('.py'):::
                python_files.append(os.path.join(root, file))
    return python_files

if __name"__main__":::
    core_files == list_python_files("D,/Projects/Unified-AI-Project/apps/backend/src/core")
    ai_files == list_python_files("D,/Projects/Unified-AI-Project/apps/backend/src/ai")
    
    print("Core Python files,")
    for file in core_files,::
        print(file)
    
    print("\nAI Python files,")
    for file in ai_files,::
        print(file)