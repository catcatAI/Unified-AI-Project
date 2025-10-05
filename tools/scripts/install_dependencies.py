#!/usr/bin/env python3
"""
安装项目依赖
"""

import subprocess
import sys

def install_package(package_name):
    """安装包"""
    try:
        _ = subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        _ = print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        _ = print(f"❌ {package_name} 安装失败: {e}")
        return False

def main() -> None:
    print("=== 安装项目依赖 ===")
    
    required_packages = [
        "tensorflow",
        "numpy",
        "scikit-learn"
    ]
    
    failed_packages = []
    for package in required_packages:
        _ = print(f"\n正在安装 {package}...")
        if not install_package(package):
            _ = failed_packages.append(package)
    
    print("\n=== 安装结果 ===")
    if failed_packages:
        _ = print(f"❌ 以下包安装失败: {', '.join(failed_packages)}")
        _ = print("请手动运行以下命令:")
        for package in failed_packages:
            _ = print(f"pip install {package}")
    else:
        _ = print("✅ 所有依赖包安装成功")
        _ = print("现在可以运行训练脚本了")

if __name__ == "__main__":
    _ = main()