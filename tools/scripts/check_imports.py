import subprocess

def run_command_in_project_root(command):
    """在项目根目录中运行命令并返回输出"""
    full_command = f'cmd /c "cd /d d:\\Projects\\Unified-AI-Project && {command}"'
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def run_command_in_backend(command):
    """在后端目录中运行命令并返回输出"""
    full_command = f'cmd /c "cd /d d:\\Projects\\Unified-AI-Project\\apps\\backend && {command}"'
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def main() -> None:
    print("Checking module imports in project environment...")
    
    # 测试openai导入
    print("\n1. Testing openai import...")
    stdout, stderr, returncode = run_command_in_project_root('python -c "import openai; print(\'OpenAI imported successfully\')"')
    if returncode == 0:
        print("✓ OpenAI import successful")
        print(stdout)
    else:
        print("✗ OpenAI import failed")
        print(f"Error: {stderr}")
    
    # 测试msgpack导入
    print("\n2. Testing msgpack import...")
    stdout, stderr, returncode = run_command_in_project_root('python -c "import msgpack; print(\'MsgPack imported successfully\')"')
    if returncode == 0:
        print("✓ MsgPack import successful")
        print(stdout)
    else:
        print("✗ MsgPack import failed")
        print(f"Error: {stderr}")
    
    # 测试src模块导入
    print("\n3. Testing src module import...")
    # 现在我们直接在项目根目录运行Python命令,Python路径已正确设置
    stdout, stderr, returncode = run_command_in_project_root('python -c "import sys; sys.path.insert(0, \'.\'); from apps.backend.src.services.multi_llm_service import MultiLLMService; print(\'MultiLLMService imported successfully\')"')
    if returncode == 0:
        print("✓ MultiLLMService import successful")
        print(stdout)
    else:
        print("✗ MultiLLMService import failed")
        print(f"Error: {stderr}")

if __name__ == "__main__":
    main()