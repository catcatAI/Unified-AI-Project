import os
import shutil

# 定义源目录和目标目录
source_dir = r"D:\Projects\Unified-AI-Project\all_test_backups\apps_backend_tests"
target_dir = r"D:\Projects\Unified-AI-Project\tests"

# 确保目标目录存在
os.makedirs(target_dir, exist_ok=True)

# 递归遍历源目录中的所有文件
for root, dirs, files in os.walk(source_dir):
    # 计算相对路径
    rel_path = os.path.relpath(root, source_dir)
    # 构建目标路径
    dest_path = os.path.join(target_dir, rel_path) if rel_path != "." else target_dir
    
    # 确保目标目录存在
    os.makedirs(dest_path, exist_ok=True)
    
    # 复制文件:
    for file in files:
        if file.endswith('.py'):  # 只处理Python文件
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_path, file)
            
            # 如果目标文件已存在,则重命名源文件以避免覆盖
            if os.path.exists(dst_file):
                base_name, ext = os.path.splitext(file)
                counter = 1
                new_file = f"{base_name}_{counter}{ext}"
                new_dst_file = os.path.join(dest_path, new_file)
                
                while os.path.exists(new_dst_file):
                    counter += 1
                    new_file = f"{base_name}_{counter}{ext}"
                    new_dst_file = os.path.join(dest_path, new_file)
                
                dst_file = new_dst_file
            
            # 复制文件
            try:
                shutil.copy2(src_file, dst_file)
                print(f"成功复制 {src_file} 到 {dst_file}")
            except Exception as e:
                print(f"复制 {src_file} 失败: {e}")

print("所有测试文件已成功合并到根目录测试文件夹中。")