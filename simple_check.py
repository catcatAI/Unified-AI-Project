import os

# 检查当前目录
print(f"当前工作目录: {os.getcwd()}")

# 检查备份目录
print("\n检查备份目录:")
for item in os.listdir('.'):
    if 'backup' in item.lower() and os.path.isdir(item):
        print(f"  找到备份目录: {item}")

# 检查apps/backend目录
print("\n检查apps/backend目录:")
if os.path.exists('apps/backend'):
    for item in os.listdir('apps/backend'):
        if 'backup' in item.lower() and os.path.isdir(f'apps/backend/{item}'):
            print(f"  找到备份目录: apps/backend/{item}")