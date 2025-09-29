import os
import filecmp

# 定义测试目录
test_dir = r"D:\Projects\Unified-AI-Project\tests"

# 查找所有带有_1后缀的Python文件
duplicate_files = []
for root, dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('_1.py'):
            duplicate_files.append(os.path.join(root, file))

# 检查重复文件是否与原文件相同，如果相同则删除重复文件
for dup_file in duplicate_files:
    # 构造原文件路径
    original_file = dup_file.replace('_1.py', '.py')
    
    # 检查原文件是否存在
    if os.path.exists(original_file):
        # 比较两个文件是否相同
        if filecmp.cmp(dup_file, original_file):
            # 如果文件相同，删除重复文件
            os.remove(dup_file)
            print(f"删除重复文件: {dup_file}")
        else:
            # 如果文件不同，重命名重复文件以保留它
            new_name = dup_file.replace('_1.py', '_backup.py')
            os.rename(dup_file, new_name)
            print(f"重命名重复文件: {dup_file} -> {new_name}")
    else:
        # 如果原文件不存在，将重复文件重命名为原文件名
        os.rename(dup_file, original_file)
        print(f"恢复文件名: {dup_file} -> {original_file}")

print("重复文件处理完成。")