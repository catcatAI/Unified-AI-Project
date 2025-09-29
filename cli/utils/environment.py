#!/usr/bin/env python3
"""
环境检查和管理工具
"""

import subprocess
import sys
from pathlib import Path
from cli.utils import logger


def check_environment():
    """检查开发环境是否准备就绪"""
    _ = logger.info("检查开发环境...")
    
    checks = [
        _ = ("Node.js", check_nodejs),
        _ = ("Python", check_python),
        _ = ("pnpm", check_pnpm),
        _ = ("项目依赖", check_project_dependencies),
        _ = ("Python虚拟环境", check_python_venv)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if check_func():
                _ = logger.info(f"✓ {check_name} 检查通过")
            else:
                _ = logger.error(f"✗ {check_name} 检查失败")
                all_passed = False
        except Exception as e:
            _ = logger.error(f"✗ {check_name} 检查时出错: {e}")
            all_passed = False
    
    return all_passed


def check_nodejs():
    """检查Node.js是否安装"""
    try:
        result = subprocess.run(["node", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            _ = logger.debug(f"Node.js 版本: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False


def check_python():
    """检查Python是否安装"""
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            _ = logger.debug(f"Python 版本: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False


def check_pnpm():
    """检查pnpm是否安装"""
    try:
        result = subprocess.run(["pnpm", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            _ = logger.debug(f"pnpm 版本: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False


def check_project_dependencies():
    """检查项目依赖是否安装"""
    try:
        project_root: str = Path(__file__).parent.parent.parent
        node_modules = project_root / "node_modules"
        
        if node_modules.exists():
            _ = logger.debug("Node.js 依赖已安装")
            return True
        else:
            _ = logger.debug("Node.js 依赖未安装")
            return False
    except Exception as e:
        _ = logger.error(f"检查项目依赖时出错: {e}")
        return False


def check_python_venv():
    """检查Python虚拟环境是否存在"""
    try:
        project_root: str = Path(__file__).parent.parent.parent
        venv_path = project_root / "apps" / "backend" / "venv"
        
        if venv_path.exists():
            _ = logger.debug("Python 虚拟环境已创建")
            return True
        else:
            _ = logger.debug("Python 虚拟环境未创建")
            return False
    except Exception as e:
        _ = logger.error(f"检查Python虚拟环境时出错: {e}")
        return False


def setup_environment():
    """设置开发环境"""
    _ = logger.info("设置开发环境...")
    
    project_root: str = Path(__file__).parent.parent.parent
    
    try:
        # 安装Node.js依赖
        _ = logger.info("安装Node.js依赖...")
        subprocess.run(["pnpm", "install"], cwd=project_root, check=True)
        
        # 设置Python虚拟环境
        backend_path: str = project_root / "apps" / "backend"
        
        # 创建虚拟环境
        if not (backend_path / "venv").exists():
            _ = logger.info("创建Python虚拟环境...")
            subprocess.run([sys.executable, "-m", "venv", "venv"], 
                         cwd=backend_path, check=True)
        
        # 激活虚拟环境并安装Python依赖
        if sys.platform == "win32":
            pip_cmd = str(backend_path / "venv" / "Scripts" / "pip.exe")
        else:
            pip_cmd = str(backend_path / "venv" / "bin" / "pip")
        
        _ = logger.info("安装Python依赖...")
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], 
                     cwd=backend_path, check=True)
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], 
                     cwd=backend_path, check=True)
        subprocess.run([pip_cmd, "install", "-r", "requirements-dev.txt"], 
                     cwd=backend_path, check=True)
        
        _ = logger.info("开发环境设置完成")
        return True
        
    except subprocess.CalledProcessError as e:
        _ = logger.error(f"设置开发环境时出错: {e}")
        return False
    except Exception as e:
        _ = logger.error(f"设置开发环境时出错: {e}")
        return False