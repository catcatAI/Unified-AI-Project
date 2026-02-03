import os

def count_python_files(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                count += 1
    return count

if __name__ == "__main__":
    total_files = count_python_files('.')
    print(f"总共有 {total_files} 个Python文件")