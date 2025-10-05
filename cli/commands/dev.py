import click
import subprocess
import sys
from pathlib import Path
import logging
from cli.utils import environment

logger = logging.getLogger(__name__)

@click.group()
def dev():
    """开发环境管理命令

    用于管理Unified AI项目的开发环境，包括启动、停止、重启和设置开发环境。

    使用示例:
      unified-ai-cli dev start     # 启动开发环境
      unified-ai-cli dev stop      # 停止开发环境
      unified-ai-cli dev restart   # 重启开发环境
      unified-ai-cli dev setup     # 设置开发环境
    """
    pass


@dev.command()
@click.option('--backend', is_flag=True, help='仅启动后端服务')
@click.option('--frontend', is_flag=True, help='仅启动前端服务')
@click.option('--desktop', is_flag=True, help='仅启动桌面应用')
@click.option('--all', is_flag=True, help='启动所有服务')
def start(backend, frontend, desktop, all):
    """启动开发环境

    启动Unified AI项目的开发环境，包括后端服务、前端仪表板和桌面应用。

    使用示例:
      unified-ai-cli dev start           # 启动所有服务
      unified-ai-cli dev start --backend # 仅启动后端服务
      unified-ai-cli dev start --frontend # 仅启动前端服务
      unified-ai-cli dev start --desktop # 仅启动桌面应用
    """
    try:
        logger.info("正在启动开发环境...")

        # 检查环境
        if not environment.check_environment():
            logger.error("环境检查失败，请运行 health-check 命令检查环境")
            return

        project_root = Path(__file__).parent.parent.parent.parent

        if all or (not backend and not frontend and not desktop):
            # 启动所有服务
            logger.info("启动后端服务...")
            _start_backend(project_root)

            logger.info("启动前端服务...")
            _start_frontend(project_root)

            logger.info("启动桌面应用...")
            _start_desktop(project_root)
        else:
            if backend:
                logger.info("启动后端服务...")
                _start_backend(project_root)

            if frontend:
                logger.info("启动前端服务...")
                _start_frontend(project_root)

            if desktop:
                logger.info("启动桌面应用...")
                _start_desktop(project_root)

        logger.info("开发环境启动完成")
        logger.info("后端API: http://localhost:8000")
        logger.info("前端仪表板: http://localhost:3000")

    except Exception as e:
        logger.error(f"启动开发环境时出错: {e}")
        sys.exit(1)


def _start_backend(project_root):
    """启动后端服务"""
    backend_path = project_root / "apps" / "backend"

    # 激活虚拟环境并启动服务
    if sys.platform == "win32":
        cmd = f"cd /d {backend_path} && venv\\Scripts\\activate.bat && python start_chroma_server.py"
        subprocess.Popen(cmd, shell=True)

        # 等待ChromaDB启动
        import time
        time.sleep(2)

        cmd = f"cd /d {backend_path} && venv\\Scripts\\activate.bat && uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000"
        subprocess.Popen(cmd, shell=True)
    else:
        # Linux/MacOS实现
        pass


def _start_frontend(project_root):
    """启动前端服务"""
    cmd = f"cd {project_root} && pnpm --filter frontend-dashboard dev"
    subprocess.Popen(cmd, shell=True)


def _start_desktop(project_root):
    """启动桌面应用"""
    cmd = f"cd {project_root} && pnpm --filter desktop-app start"
    subprocess.Popen(cmd, shell=True)


@dev.command()
def stop():
    """停止开发环境

    停止所有正在运行的开发环境服务，包括后端、前端和桌面应用。

    使用示例:
      unified-ai-cli dev stop
    """
    try:
        logger.info("正在停止开发环境...")

        # 停止Python进程
        if sys.platform == "win32":
            subprocess.run("taskkill /f /im python.exe", shell=True, capture_output=True)
        else:
            subprocess.run("pkill -f python", shell=True, capture_output=True)

        # 停止Node.js进程
        if sys.platform == "win32":
            subprocess.run("taskkill /f /im node.exe", shell=True, capture_output=True)
        else:
            subprocess.run("pkill -f node", shell=True, capture_output=True)

        logger.info("开发环境已停止")

    except Exception as e:
        logger.error(f"停止开发环境时出错: {e}")


@dev.command()
def status():
    """查看开发环境状态

    检查各个开发环境服务的运行状态。

    使用示例:
      unified-ai-cli dev status
    """
    try:
        logger.info("检查开发环境状态...")

        # 检查后端服务
        backend_status = _check_backend_status()
        logger.info(f"后端服务: {'运行中' if backend_status else '未运行'}")

        # 检查前端服务
        frontend_status = _check_frontend_status()
        logger.info(f"前端服务: {'运行中' if frontend_status else '未运行'}")

        # 检查桌面应用
        desktop_status = _check_desktop_status()
        logger.info(f"桌面应用: {'运行中' if desktop_status else '未运行'}")

    except Exception as e:
        logger.error(f"检查开发环境状态时出错: {e}")


def _check_backend_status():
    """检查后端服务状态"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def _check_frontend_status():
    """检查前端服务状态"""
    try:
        import requests
        response = requests.get("http://localhost:3000", timeout=5)
        return response.status_code == 200
    except:
        return False


def _check_desktop_status():
    """检查桌面应用状态"""
    # 简单实现，实际可能需要更复杂的检查
    return False


@dev.command()
def setup():
    """设置开发环境

    初始化和设置开发环境，包括创建虚拟环境、安装依赖等。

    使用示例:
      unified-ai-cli dev setup
    """
    try:
        logger.info("设置开发环境...")

        project_root = Path(__file__).parent.parent.parent.parent

        # 创建Python虚拟环境
        backend_path = project_root / "apps" / "backend"
        if not (backend_path / "venv").exists():
            logger.info("创建Python虚拟环境...")
            subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=backend_path, check=True)

        # 安装Python依赖
        logger.info("安装Python依赖...")
        if sys.platform == "win32":
            pip_cmd = str(backend_path / "venv" / "Scripts" / "pip.exe")
        else:
            pip_cmd = str(backend_path / "venv" / "bin" / "pip")

        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], cwd=backend_path, check=True)
        subprocess.run([pip_cmd, "install", "-r", "requirements-dev.txt"], cwd=backend_path, check=True)

        # 安装Node.js依赖
        logger.info("安装Node.js依赖...")
        subprocess.run(["pnpm", "install"], cwd=project_root, check=True)

        logger.info("开发环境设置完成")

    except Exception as e:
        logger.error(f"设置开发环境时出错: {e}")
        sys.exit(1)


@dev.command()
def restart():
    """重启开发环境

    重启所有开发环境服务。

    使用示例:
      unified-ai-cli dev restart
    """
    logger.info("重启开发环境...")
    stop()
    start(False, False, False, True)  # 重启所有服务