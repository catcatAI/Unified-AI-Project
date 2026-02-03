import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from apps.backend.src.tools.tool_registry import get_all_tools

def check():
    tools = get_all_tools()
    print("Registered Tools:")
    for name, tool in tools.items():
        print(f" - {name}: {tool.__class__.__name__}")

if __name__ == "__main__":
    check()
