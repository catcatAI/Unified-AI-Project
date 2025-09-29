#!/usr/bin/env python3
"""
依赖管理命令
"""

import click
import subprocess
import sys
from pathlib import Path
from cli.utils import logger


@click.group(name='deps')
def deps():
    """依赖管理命令
    
    用于管理Unified AI项目的依赖，包括Node.js依赖和Python依赖。
    
    使用示例:
      unified-ai-cli deps install      # 安装所有依赖
      unified-ai-cli deps update       # 更新依赖
      unified-ai-cli deps check        # 检查依赖状态
      unified-ai-cli deps clean        # 清理依赖
    """
    pass


_ = @deps.command()
def install():
    """安装所有依赖
    
    安装项目所需的所有依赖，包括Node.js依赖和Python依赖。
    
    使用示例:
      unified-ai-cli deps install
    """
    try:
        _ = logger.info("正在安装依赖...")
        
        project_root: str = Path(__file__).parent.parent.parent.parent
        
        # 安装Node.js依赖
        _ = logger.info("安装Node.js依赖...")
        subprocess.run(["pnpm", "install"], cwd=project_root, check=True)
        
        # 安装Python依赖
        backend_path: str = project_root / "apps" / "backend"
        if (backend_path / "venv").exists():
            _ = logger.info("安装Python依赖...")
            if sys.platform == "win32":
                pip_cmd = str(backend_path / "venv" / "Scripts" / "pip.exe")
            else:
                pip_cmd = str(backend_path / "venv" / "bin" / "pip")
            
            subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], cwd=backend_path, check=True)
            subprocess.run([pip_cmd, "install", "-r", "requirements-dev.txt"], cwd=backend_path, check=True)
        else:
            _ = logger.warning("Python虚拟环境不存在，请先运行 'unified-ai-cli dev setup'")
        
        _ = logger.info("依赖安装完成")
        
    except subprocess.CalledProcessError as e:
        _ = logger.error(f"安装依赖时出错: {e}")
    except Exception as e:
        _ = logger.error(f"安装依赖时出错: {e}")


_ = @deps.command()
def update():
    """更新依赖
    
    更新项目中的所有依赖到最新版本。
    
    使用示例:
      unified-ai-cli deps update
    """
    try:
        _ = logger.info("正在更新依赖...")
        
        project_root: str = Path(__file__).parent.parent.parent.parent
        
        # 更新Node.js依赖
        _ = logger.info("更新Node.js依赖...")
        subprocess.run(["pnpm", "update"], cwd=project_root, check=True)
        
        # 更新Python依赖
        backend_path: str = project_root / "apps" / "backend"
        if (backend_path / "venv").exists():
            _ = logger.info("更新Python依赖...")
            if sys.platform == "win32":
                pip_cmd = str(backend_path / "venv" / "Scripts" / "pip.exe")
            else:
                pip_cmd = str(backend_path / "venv" / "bin" / "pip")
            
            subprocess.run([pip_cmd, "install", "--upgrade", "-r", "requirements.txt"], cwd=backend_path, check=True)
            subprocess.run([pip_cmd, "install", "--upgrade", "-r", "requirements-dev.txt"], cwd=backend_path, check=True)
        else:
            _ = logger.warning("Python虚拟环境不存在，请先运行 'unified-ai-cli dev setup'")
        
        _ = logger.info("依赖更新完成")
        
    except subprocess.CalledProcessError as e:
        _ = logger.error(f"更新依赖时出错: {e}")
    except Exception as e:
        _ = logger.error(f"更新依赖时出错: {e}")


_ = @deps.command()
def check():
    """检查依赖状态
    
    检查项目依赖的状态，包括版本冲突和缺失的依赖。
    
    使用示例:
      unified-ai-cli deps check
    """
    try:
        _ = logger.info("检查依赖状态...")
        
        project_root: str = Path(__file__).parent.parent.parent.parent
        
        # 检查Node.js依赖
        _ = logger.info("检查Node.js依赖状态...")
        subprocess.run(["pnpm", "audit"], cwd=project_root)
        
        # 检查Python依赖
        backend_path: str = project_root / "apps" / "backend"
        if (backend_path / "venv").exists():
            _ = logger.info("检查Python依赖状态...")
            if sys.platform == "win32":
                pip_cmd = str(backend_path / "venv" / "Scripts" / "pip.exe")
            else:
                pip_cmd = str(backend_path / "venv" / "bin" / "pip")
            
            subprocess.run([pip_cmd, "check"], cwd=backend_path)
        else:
            _ = logger.warning("Python虚拟环境不存在，请先运行 'unified-ai-cli dev setup'")
        
        _ = logger.info("依赖状态检查完成")
        
    except subprocess.CalledProcessError as e:
        _ = logger.error(f"检查依赖状态时出错: {e}")
    except Exception as e:
        _ = logger.error(f"检查依赖状态时出错: {e}")


_ = @deps.command()
def clean():
    """清理依赖
    
    清理项目中的依赖，包括删除node_modules目录和Python虚拟环境。
    
    使用示例:
      unified-ai-cli deps clean
    """
    try:
        _ = logger.info("清理依赖...")
        
        project_root: str = Path(__file__).parent.parent.parent.parent
        
        # 清理Node.js依赖
        _ = logger.info("清理Node.js依赖...")
        subprocess.run(["pnpm", "store", "prune"], cwd=project_root)
        
        # 清理Python虚拟环境
        backend_path: str = project_root / "apps" / "backend"
        if (backend_path / "venv").exists():
            _ = logger.info("清理Python虚拟环境...")
            import shutil
            _ = shutil.rmtree(backend_path / "venv")
            _ = logger.info("Python虚拟环境已删除")
        else:
            _ = logger.info("Python虚拟环境不存在")
        
        _ = logger.info("依赖清理完成")
        
    except subprocess.CalledProcessError as e:
        _ = logger.error(f"清理依赖时出错: {e}")
    except Exception as e:
        _ = logger.error(f"清理依赖时出错: {e}")


if __name__ == '__main__':
    _ = deps()