import subprocess
import sys
import os

def run_command_in_venv(command):
    """在虚拟环境中运行命令并返回输出"""
    full_command = f'cmd /c "cd /d d:\\Projects\\Unified-AI-Project\\apps\\backend && venv\\Scripts\\activate.bat && {command}"'
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def main():
    print("Checking module imports in virtual environment...")
    
    # 测试openai导入
    print("\n1. Testing openai import...")
    stdout, stderr, returncode = run_command_in_venv('python -c "import openai; print(\'OpenAI imported successfully\')"')
    if returncode == 0:
        print("✓ OpenAI import successful")
        print(stdout)
    else:
        print("✗ OpenAI import failed")
        print(f"Error: {stderr}")
    
    # 测试msgpack导入
    print("\n2. Testing msgpack import...")
    stdout, stderr, returncode = run_command_in_venv('python -c "import msgpack; print(\'MsgPack imported successfully\')"')
    if returncode == 0:
        print("✓ MsgPack import successful")
        print(stdout)
    else:
        print("✗ MsgPack import failed")
        print(f"Error: {stderr}")
    
    # 测试src模块导入
    print("\n3. Testing src module import...")
    stdout, stderr, returncode = run_command_in_venv('python -c "import sys; sys.path.insert(0, \'.\'); sys.path.insert(0, \'apps/backend/src\'); from apps.backend.src.services.multi_llm_service import MultiLLMService; print(\'MultiLLMService imported successfully\')"')
    if returncode == 0:
        print("✓ MultiLLMService import successful")
        print(stdout)
    else:
        print("✗ MultiLLMService import failed")
        print(f"Error: {stderr}")

if __name__ == "__main__":
    main()