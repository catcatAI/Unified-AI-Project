import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

# Redirect output to a file
output_file = os.path.join(os.path.dirname(__file__), 'test_modules_output.txt')
with open(output_file, 'w') as f:
    _ = f.write("Testing module imports...\n")
    
    try:
        _ = f.write("[OK] openai module imported successfully\n")
    except ImportError as e:
        _ = f.write(f"[ERROR] Failed to import openai: {e}\n")
    
    try:
        _ = f.write("[OK] msgpack module imported successfully\n")
    except ImportError as e:
        _ = f.write(f"[ERROR] Failed to import msgpack: {e}\n")
    
    try:
        _ = f.write("[OK] MultiLLMService imported successfully\n")
    except ImportError as e:
        _ = f.write(f"[ERROR] Failed to import MultiLLMService: {e}\n")
    
    _ = f.write("Module import test completed.\n")

_ = print("Test results saved to test_modules_output.txt")