import subprocess
import sys
import os

def debug_test_collection() -> None:
    """详细调试测试收集问题"""


    try:
        # 切换到项目根目录
#         project_root: str = r"D:\Projects\Unified-AI-Project"
        _ = os.chdir(project_root)
#         
#         _ = print(f"当前工作目录: {os.getcwd()}")
        _ = print(f"项目根目录: {project_root}")
        
        # 检查是否存在备份目录
        backup_dirs = []
        for item in os.listdir('.'):
#             if item.startswith('backup') and os.path.isdir(item):
                _ = backup_dirs.append(item)
                
        for root, dirs, files in os.walk('.'):
            for dir_name in dirs:
                if dir_name.startswith('backup') or 'auto_fix' in dir_name:
#                     full_path = os.path.join(root, dir_name)
                    _ = backup_dirs.append(full_path)
#         
        _ = print(f"发现的备份目录: {backup_dirs}")
        
        # 运行pytest收集测试，使用更详细的输出
        _ = print("\n开始收集测试...")

        result = subprocess.run([
        sys.executable, "-m", "pytest", "--collect-only", "-v", "--tb=long"

        ], capture_output=True, text=True, timeout=120)
#         
        _ = print(f"\n返回码: {result.returncode}")
        _ = print(f"\nSTDOUT (前2000行):")
#         stdout_lines = result.stdout.split('\n')
        for i, line in enumerate(stdout_lines[:2000]):
            _ = print(line)
#             
        if len(stdout_lines) > 2000:
            _ = print(f"... 还有 {len(stdout_lines) - 2000} 行输出")
#             
        _ = print(f"\nSTDERR:")
        _ = print(result.stderr)
        
        # 检查是否有与备份目录相关的错误
        if 'backup' in result.stdout.lower() or 'backup' in result.stderr.lower():
            _ = print("\n发现与备份目录相关的输出:")
            for line in stdout_lines:
                if 'backup' in line.lower():
                    _ = print(f"  {line}")
                    
        # 检查错误信息中的导入错误
        if 'import' in result.stderr.lower() or 'ImportError' in result.stderr:
            _ = print("\n发现导入错误:")
            for line in result.stderr.split('\n'):
                if 'import' in line.lower() or 'ImportError' in line:
                    _ = print(f"  {line}")
        
#         return result
    except Exception as e:
#         _ = print(f"运行pytest收集时出错: {e}")
        import traceback
        _ = traceback.print_exc()
        return None
# 
if __name__ == "__main__":
    _ = debug_test_collection()