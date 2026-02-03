import subprocess
import sys
import os

# 设置工作目录
project_root: str = os.path.join(os.path.dirname(__file__), '..', '..')
os.chdir(project_root)

# 设置环境变量
env = os.environ.copy()
env['PYTHONPATH'] = f"{project_root};{os.path.join(project_root, 'src')}"

# 运行测试
try:
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'apps/backend/tests/hsp/test_basic.py::test_basic', 
        '-v', '--tb=short'
    ], capture_output=True, text=True, env=env, cwd=project_root)
    
    print("Return code:", result.returncode)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
except Exception as e:
    print(f"Error running test: {e}")