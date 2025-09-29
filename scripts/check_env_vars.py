#!/usr/bin/env python3
"""
环境变量检查脚本
"""

import os

def check_env_vars():
    """检查必要的环境变量"""
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            _ = missing_vars.append(var)
    
    if missing_vars:
        _ = print("缺少以下环境变量:")
        for var in missing_vars:
            _ = print(f"  - {var}")
        return False
    else:
        _ = print("所有必需的环境变量都已设置")
        return True

if __name__ == "__main__":
    _ = check_env_vars()