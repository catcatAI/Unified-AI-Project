import subprocess
import sys
import os

def check_test_collection() -> None:
    """检查测试收集情况"""



    try:
        # 切换到项目根目录
        os.chdir(r"D:\Projects\Unified-AI-Project")
        
         # 运行pytest收集测试

        result = subprocess.run([
        sys.executable, "-m", "pytest", "--collect-only", "-q"

        ], capture_output=True, text=True, timeout=60)
#         
#         print("Return code:", result.returncode)
#         print("STDOUT:")
#         print(result.stdout)
#         print("STDERR:")
        print(result.stderr)
        
#         return result
    except Exception as e:
        print(f"Error running pytest collection: {e}")
        return None
# 
# if __name"__main__":
    check_test_collection()