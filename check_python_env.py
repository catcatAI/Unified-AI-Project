import sys
import os
from pathlib import Path

print("Python版本:", sys.version)
print("当前工作目录:", os.getcwd())
print("Python路径:")
for p in sys.path:
    print("  ", p)

# 检查文件是否存在
project_root = Path(__file__).parent
fix_script_path = project_root / "tools" / "unified-fix.py"
print(f"\n检查文件: {fix_script_path}")
print(f"文件存在: {fix_script_path.exists()}")

if fix_script_path.exists():
    print(f"文件大小: {fix_script_path.stat().st_size} 字节")
    
    # 尝试读取前100行
    try:
        with open(fix_script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:100]
        print(f"前100行读取成功，共 {len(lines)} 行")
    except Exception as e:
        print(f"读取文件失败: {e}")