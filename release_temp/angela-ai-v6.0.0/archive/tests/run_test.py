import subprocess
import sys
import os

# 设置工作目录
os.chdir(r'D:\Projects\Unified-AI-Project')

# 运行测试
result = subprocess.run([
    sys.executable, '-m', 'pytest', 
    'apps/backend/tests/hsp/test_basic.py::test_basic', 
    '-v', '--tb=short'
], capture_output=True, text=True)

print("Return code:", result.returncode)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)