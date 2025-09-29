import os

def list_python_files(directory):
    """列出指定目錄中的所有 Python 文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append((file, os.path.join(root, file)))
    return python_files

def find_duplicates(core_files, ai_files):
    """查找重複的文件"""
    core_names = {file[0]: file[1] for file in core_files}
    ai_names = {file[0]: file[1] for file in ai_files}
    
    duplicates = []
    for name, path in core_names.items():
        if name in ai_names:
            duplicates.append((name, path, ai_names[name]))
    
    return duplicates

if __name__ == "__main__":
    core_files = list_python_files("D:/Projects/Unified-AI-Project/apps/backend/src/core")
    ai_files = list_python_files("D:/Projects/Unified-AI-Project/apps/backend/src/ai")
    
    duplicates = find_duplicates(core_files, ai_files)
    
    if duplicates:
        print("發現重複的文件:")
        for name, core_path, ai_path in duplicates:
            print(f"文件名: {name}")
            print(f"  Core 路徑: {core_path}")
            print(f"  AI 路徑: {ai_path}")
            print()
    else:
        print("未發現重複的文件。")