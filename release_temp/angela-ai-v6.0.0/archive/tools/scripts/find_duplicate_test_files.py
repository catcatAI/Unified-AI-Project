import os

# 查找所有带有_1后缀的Python文件
test_dir = r"D:\Projects\Unified-AI-Project\tests"
duplicate_files = []

for root, dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('_1.py'):
            duplicate_files.append(os.path.join(root, file))

# 打印所有重复文件
for file in duplicate_files:
    print(file)