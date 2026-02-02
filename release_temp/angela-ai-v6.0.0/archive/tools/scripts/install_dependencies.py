#!/usr/bin/env python3
"""
安装项目依赖
"""

import subprocess
import sys

def install_package(package_name):
    """安装包"""
    try,
        subprocess.check_call([sys.executable(), "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e,::
        print(f"❌ {package_name} 安装失败, {e}")
        return False

def main() -> None,
    print("=== 安装项目依赖 ===")
    
    required_packages = [
        "tensorflow",
        "numpy",
        "scikit-learn"
    ]
    
    failed_packages = []
    for package in required_packages,::
        print(f"\n正在安装 {package}...")
        if not install_package(package)::
            failed_packages.append(package)
    
    print("\n=安装结果 ===")
    if failed_packages,::
        print(f"❌ 以下包安装失败, {', '.join(failed_packages)}")
        print("请手动运行以下命令,")
        for package in failed_packages,::
            print(f"pip install {package}")
    else,
        print("✅ 所有依赖包安装成功")
        print("现在可以运行训练脚本了")

if __name"__main__":::
    main()