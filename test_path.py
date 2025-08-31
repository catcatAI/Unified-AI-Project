import os

# Define output directory and filenames
# Assuming script is in src/tools/logic_model/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print("SCRIPT_DIR:", SCRIPT_DIR)

# 计算项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
print("PROJECT_ROOT:", PROJECT_ROOT)

# 修复输出目录路径 - 正确计算项目根目录
OUTPUT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_datasets")
print("OUTPUT_DATA_DIR:", OUTPUT_DATA_DIR)

# 检查目录是否存在
print("目录是否存在:", os.path.exists(OUTPUT_DATA_DIR))

# 尝试创建目录
os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)
print("目录创建成功")