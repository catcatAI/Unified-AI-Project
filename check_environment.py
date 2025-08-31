#!/usr/bin/env python3
"""
检查Python环境和依赖项
"""

import sys
import importlib

def check_python_version():
    """检查Python版本"""
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    return sys.version_info

def check_package(package_name):
    """检查包是否已安装"""
    try:
        package = importlib.import_module(package_name)
        print(f"✅ {package_name} 已安装 - 版本: {getattr(package, '__version__', '未知')}")
        return True
    except ImportError:
        print(f"❌ {package_name} 未安装")
        return False

def main():
    print("=== Python环境检查 ===")
    check_python_version()
    
    print("\n=== 依赖包检查 ===")
    required_packages = [
        "tensorflow",
        "numpy",
        "sklearn"
    ]
    
    missing_packages = []
    for package in required_packages:
        if not check_package(package):
            missing_packages.append(package)
    
    print("\n=== 检查结果 ===")
    if missing_packages:
        print(f"缺少以下包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        print("pip install tensorflow numpy scikit-learn")
    else:
        print("✅ 所有必需的包都已安装")

if __name__ == "__main__":
    main()