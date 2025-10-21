import os
import shutil

# 定义源目录和目标目录
source_dir = r"D:\Projects\Unified-AI-Project\all_test_backups\scattered_tests"
target_dir = r"D:\Projects\Unified-AI-Project\tests"

# 确保目标目录存在
os.makedirs(target_dir, exist_ok=True)

# 定义特定文件的移动规则
file_mapping = {
    "test_hsp_fixture.py": os.path.join(target_dir, "hsp"),
    "run_hsp_tests.py": os.path.join(target_dir, "hsp"),
    "test_api.py": os.path.join(target_dir, "integration"),
    "test_code_model_upgrade.py": os.path.join(target_dir, "ai"),
    "simple_test.py": os.path.join(target_dir, "ai"),
}

# 移动特定文件
for file_name, dest_dir in file_mapping.items():
    source_path = os.path.join(source_dir, file_name)
    dest_path = os.path.join(dest_dir, file_name)
    
    # 确保目标目录存在
    os.makedirs(dest_dir, exist_ok=True)
    
    # 如果源文件存在,则移动它
    if os.path.exists(source_path):
        try:
            shutil.move(source_path, dest_path)
            print(f"成功移动 {file_name} 到 {dest_dir}")
        except Exception as e:
            print(f"移动 {file_name} 失败: {e}")
    else:
        print(f"源文件 {file_name} 不存在")

# 移动剩余的文件到tests根目录
for file_name in os.listdir(source_dir):
    source_path = os.path.join(source_dir, file_name)
    dest_path = os.path.join(target_dir, file_name)
    
    # 如果是文件,则移动它
    if os.path.isfile(source_path):
        try:
            shutil.move(source_path, dest_path)
            print(f"成功移动 {file_name} 到 {target_dir}")
        except Exception as e:
            print(f"移动 {file_name} 失败: {e}")