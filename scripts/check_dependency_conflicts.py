#!/usr/bin/env python3
"""
依赖冲突检查脚本
"""

import subprocess
import sys

def check_dependency_conflicts():
    """检查依赖冲突"""
    _ = print("检查依赖冲突...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "check"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            _ = print("未发现依赖冲突")
        else:
            _ = print("发现依赖冲突:")
            _ = print(result.stdout)
            return False
    except Exception as e:
        _ = print(f"检查依赖冲突时出错: {e}")
        return False
    return True

if __name__ == "__main__":
    _ = check_dependency_conflicts()