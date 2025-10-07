import subprocess
import sys
import os

def check_test_collection() -> None:
    """检查测试收集情况"""


    try:
        # 切换到项目根目录
        _ = os.chdir(r"D:\Projects\Unified-AI-Project")
        
         # 运行pytest收集测试

        result = subprocess.run([
        sys.executable, "-m", "pytest", "--collect-only", "-q"

        ], capture_output=True, text=True, timeout=60)
#         
#         _ = print("Return code:", result.returncode)
#         _ = print("STDOUT:")
#         _ = print(result.stdout)
        _ = print("STDERR:")
        _ = print(result.stderr)
        
#         return result
    except Exception as e:
        _ = print(f"Error running pytest collection: {e}")
        return None
# 
if __name__ == "__main__":
    _ = check_test_collection()