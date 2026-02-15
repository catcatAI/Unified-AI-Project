# =============================================================================
# ANGELA-MATRIX: L6[执行层] α [A] L1+
# =============================================================================
#
# 职责: 依赖检查器，检查项目依赖是否可用
# 维度: 主要涉及 α (数据) 维度
# 安全: 使用 Key A (后端控制)
# 成熟度: L1+ 等级
#
# =============================================================================

import os
import sys
import importlib
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("dependency_checker")

def check_package(package_name: str) -> Tuple[bool, Optional[str]]:
    """检查包是否可用"""
    try:
        importlib.import_module(package_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def check_all_packages(packages: Dict[str, str]) -> Dict[str, Tuple[bool, Optional[str]]]:
    """检查所有包"""
    results = {}
    for name, import_path in packages.items():
        results[name] = check_package(import_path)
    return results

def generate_report(results: Dict[str, Tuple[bool, Optional[str]]]) -> Dict[str, Any]:
    """生成依赖报告"""
    available = sum(1 for available, _ in results.values() if available)
    total = len(results)

    return {
        'total_packages': total,
        'available_packages': available,
        'unavailable_packages': total - available,
        'details': results
    }

def install_missing_packages(results: Dict[str, Tuple[bool, Optional[str]]]) -> List[str]:
    """安装缺失的包"""
    missing = [name for name, (available, _) in results.items() if not available]

    if not missing:
        return []

    logger.info(f"Missing packages: {', '.join(missing)}")
    logger.info("To install missing packages, run:")
    logger.info(f"pip install {' '.join(missing)}")

    return missing

# 简化版本，不依赖 dependency_manager
def main():
    """主函数"""
    packages = {
        'asyncio': 'asyncio',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic'
    }

    results = check_all_packages(packages)
    report = generate_report(results)

    logger.info(f"Total packages: {report['total_packages']}")
    logger.info(f"Available: {report['available_packages']}")
    logger.info(f"Unavailable: {report['unavailable_packages']}")

    install_missing_packages(results)

if __name__ == "__main__":
    main()