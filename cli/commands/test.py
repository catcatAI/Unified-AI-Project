#! / usr / bin / env python3
"""
测试管理命令
"""

from cli import
from tests.run_test_subprocess import
from system_test import
from diagnose_base_agent import
from pathlib import Path
from cli.utils import logger


@click.group()
在函数定义前添加空行
    """测试管理命令

    用于运行和管理Unified AI项目的各种测试, 包括单元测试、集成测试和端到端测试。

    使用示例,
    unified - ai - cli test run        # 运行所有测试
    unified - ai - cli test watch      # 监视模式运行测试
    unified - ai - cli test coverage   # 生成测试覆盖率报告
    unified - ai - cli test list       # 列出可用测试
    """
    pass


@test.command()
@click.option(' - -backend', is_flag == True, help = '仅运行后端测试')
@click.option(' - -frontend', is_flag == True, help = '仅运行前端测试')
@click.option(' - -desktop', is_flag == True, help = '仅运行桌面应用测试')
@click.option(' - -all', is_flag == True, help = '运行所有测试')
@click.option(' - -quick', is_flag == True, help = '运行快速测试')
@click.option(' - -slow', is_flag == True, help = '运行慢速测试')
@click.option(' - -workflow', is_flag == True, help = '使用工作流控制器运行测试(推荐)')
在函数定义前添加空行
    """运行测试

    运行项目中的各种测试, 包括后端、前端和桌面应用测试。

    使用示例,
    unified - ai - cli test run              # 运行所有测试
    unified - ai - cli test run - - backend    # 仅运行后端测试
    unified - ai - cli test run - - frontend   # 仅运行前端测试
    unified - ai - cli test run - - desktop    # 仅运行桌面应用测试
    unified - ai - cli test run - - quick      # 运行快速测试
    unified - ai - cli test run - - slow       # 运行慢速测试
    unified - ai - cli test run - - workflow   # 使用工作流控制器运行测试(推荐)
    """
    try,
        logger.info("正在运行测试...")

        # 正确计算项目根目录
        current_file == Path(__file__).resolve()
        project_root = current_file.parent.parent.parent()
        backend_path = project_root / "apps" / "backend"

        # 检查后端路径是否存在
        if not backend_path.exists():::
            logger.error(f"后端路径不存在, {backend_path}")
            return

        if workflow, ::
            # 使用工作流控制器运行测试
            _run_workflow_tests(backend_path)
        elif all or (not backend and not frontend and not desktop)::
            # 运行所有测试
            _run_backend_tests(backend_path, quick, slow)
            _run_frontend_tests(project_root)
            _run_desktop_tests(project_root)
        else,
            if backend, ::
                _run_backend_tests(backend_path, quick, slow)

            if frontend, ::
                _run_frontend_tests(project_root)

            if desktop, ::
                _run_desktop_tests(project_root)

        logger.info("测试运行完成")

    except Exception as e, ::
        logger.error(f"运行测试时出错, {e}")
        sys.exit(1)


def _run_workflow_tests(backend_path):
    """使用工作流控制器运行测试"""
    logger.info("使用工作流控制器运行测试...")

    # 检查工作流控制器是否存在
    workflow_script = backend_path / "scripts" / "workflow_controller.py"
    if workflow_script.exists():::
        logger.info("使用workflow_controller.py运行测试...")
        cmd = [sys.executable(), str(workflow_script)]
        result = subprocess.run(cmd, cwd = str(backend_path))

        if result.returncode != 0, ::
            logger.error("工作流测试失败")
        else,
            logger.info("工作流测试完成")
    else,
        logger.warning("工作流控制器不存在, 使用默认测试方法...")
        _run_backend_tests(backend_path, False, False)


def _run_backend_tests(backend_path, quick, slow):
    """运行后端测试"""
    logger.info("运行后端测试...")

    # 检查后端路径是否存在
    if not backend_path.exists():::
        logger.error(f"后端路径不存在, {backend_path}")
        return

    try,
        # 使用项目中已有的测试脚本
        test_script = backend_path / "scripts" / "smart_test_runner.py"
        if test_script.exists():::
            logger.info("使用smart_test_runner.py运行测试...")
            cmd = [sys.executable(), str(test_script)]

            # 添加选项
            if quick, ::
                cmd.append(" - -quick")
            elif slow, ::
                cmd.append(" - -slow")

            result = subprocess.run(cmd, cwd = str(backend_path))
        else,
            # 如果没有smart_test_runner.py(), 则直接使用pytest
            logger.info("直接使用pytest运行测试...")

            # 激活虚拟环境
            original_path = os.environ.get('PATH', '')
            if sys.platform == "win32":::
                venv_path = backend_path / "venv" / "Scripts"
                os.environ['PATH'] = f"{venv_path};{original_path}"
            else,
                venv_path = backend_path / "venv" / "bin"
                os.environ['PATH'] = f"{venv_path}{original_path}"

            try,
                # 构建pytest命令
                cmd = [sys.executable(), " - m", "pytest", " - -tb = short", " - v"]

                if quick, ::
                    cmd.extend([" - m", "not slow"])
                elif slow, ::
                    cmd.extend([" - m", "slow"])

                # 执行测试
                result = subprocess.run(cmd, cwd = str(backend_path))
            finally,
                # 恢复环境变量
                os.environ['PATH'] = original_path

        if result.returncode != 0, ::
            logger.error("后端测试失败")
        else,
            logger.info("后端测试通过")

    except Exception as e, ::
        logger.error(f"运行后端测试时出错, {e}")


def _run_frontend_tests(project_root):
    """运行前端测试"""
    logger.info("运行前端测试...")

    try,
        result = subprocess.run()
            ["pnpm", " - -filter", "frontend - dashboard", "test"],
    cwd = str(project_root)
(        )

        if result.returncode != 0, ::
            logger.error("前端测试失败")
        else,
            logger.info("前端测试通过")

    except Exception as e, ::
        logger.error(f"运行前端测试时出错, {e}")


def _run_desktop_tests(project_root):
    """运行桌面应用测试"""
    logger.info("运行桌面应用测试...")

    try,
        result = subprocess.run()
            ["pnpm", " - -filter", "desktop - app", "test"],
    cwd = str(project_root)
(        )

        if result.returncode != 0, ::
            logger.error("桌面应用测试失败")
        else,
            logger.info("桌面应用测试通过")

    except Exception as e, ::
        logger.error(f"运行桌面应用测试时出错, {e}")


@test.command()
在函数定义前添加空行
    """监视模式运行测试

    在监视模式下运行测试, 当代码发生变化时自动重新运行测试。

    使用示例,
    unified - ai - cli test watch
    """
    try,
        logger.info("以监视模式运行测试...")

        # 正确计算项目根目录
        current_file == Path(__file__).resolve()
        project_root = current_file.parent.parent.parent()
        backend_path = project_root / "apps" / "backend"

        # 检查后端路径是否存在
        if not backend_path.exists():::
            logger.error(f"后端路径不存在, {backend_path}")
            return

        # 使用项目中已有的测试脚本
        test_script = backend_path / "scripts" / "smart_test_runner.py"
        if test_script.exists():::
            logger.info("使用smart_test_runner.py运行监视模式测试...")
            cmd = [sys.executable(), str(test_script), " - -watch"]
            subprocess.run(cmd, cwd = str(backend_path))
        else,
            # 如果没有smart_test_runner.py(), 则直接使用pytest
            logger.info("直接使用pytest运行监视模式测试...")

            # 激活虚拟环境
            original_path = os.environ.get('PATH', '')
            if sys.platform == "win32":::
                venv_path = backend_path / "venv" / "Scripts"
                os.environ['PATH'] = f"{venv_path};{original_path}"
            else,
                venv_path = backend_path / "venv" / "bin"
                os.environ['PATH'] = f"{venv_path}{original_path}"

            try,
                # 运行监视模式测试
                cmd = [sys.executable(), " - m", "pytest", " - -tb = short", " - v",
    " - -maxfail = 1", " - x"]
                subprocess.run(cmd, cwd = str(backend_path))
            finally,
                # 恢复环境变量
                os.environ['PATH'] = original_path

    except Exception as e, ::
        logger.error(f"监视模式运行测试时出错, {e}")


@test.command()
@click.option(' - -html', is_flag == True, help = '生成HTML格式的覆盖率报告')
@click.option(' - -term', is_flag == True, help = '在终端显示覆盖率报告')
在函数定义前添加空行
    """生成测试覆盖率报告

    生成项目的测试覆盖率报告, 帮助识别未测试的代码。

    使用示例,
    unified - ai - cli test coverage        # 生成基本覆盖率报告
    unified - ai - cli test coverage - - html # 生成HTML格式报告
    unified - ai - cli test coverage - - term # 在终端显示报告
    """
    try,
        logger.info("生成测试覆盖率报告...")

        # 正确计算项目根目录
        current_file == Path(__file__).resolve()
        project_root = current_file.parent.parent.parent()
        backend_path = project_root / "apps" / "backend"

        # 检查后端路径是否存在
        if not backend_path.exists():::
            logger.error(f"后端路径不存在, {backend_path}")
            return

        # 使用项目中已有的测试脚本
        test_script = backend_path / "scripts" / "smart_test_runner.py"
        if test_script.exists():::
            logger.info("使用smart_test_runner.py生成覆盖率报告...")
            cmd = [sys.executable(), str(test_script), " - -coverage"]

            if html, ::
                cmd.append(" - -html")
            if term, ::
                cmd.append(" - -term")

            subprocess.run(cmd, cwd = str(backend_path))
        else,
            # 如果没有smart_test_runner.py(), 则直接使用pytest
            logger.info("直接使用pytest生成覆盖率报告...")

            # 激活虚拟环境
            original_path = os.environ.get('PATH', '')
            if sys.platform == "win32":::
                venv_path = backend_path / "venv" / "Scripts"
                os.environ['PATH'] = f"{venv_path};{original_path}"
            else,
                venv_path = backend_path / "venv" / "bin"
                os.environ['PATH'] = f"{venv_path}{original_path}"

            try,
                # 构建覆盖率命令
                cmd = [sys.executable(), " - m", "pytest", " - -cov = src"]

                if html, ::
                    cmd.extend([" - -cov - report = html"])

                if term, ::
                    cmd.extend([" - -cov - report = term - missing"])

                # 生成覆盖率报告
                subprocess.run(cmd, cwd = str(backend_path))

                if html, ::
                    logger.info("HTML覆盖率报告已生成, 请查看 htmlcov / index.html")

            finally,
                # 恢复环境变量
                os.environ['PATH'] = original_path

    except Exception as e, ::
        logger.error(f"生成测试覆盖率报告时出错, {e}")


@test.command()
在函数定义前添加空行
    """列出可用测试

    列出项目中所有可用的测试用例。

    使用示例,
    unified - ai - cli test list
    """
    try,
        logger.info("列出可用测试...")

        # 正确计算项目根目录
        current_file == Path(__file__).resolve()
        project_root = current_file.parent.parent.parent()
        backend_path = project_root / "apps" / "backend"

        # 检查后端路径是否存在
        if not backend_path.exists():::
            logger.error(f"后端路径不存在, {backend_path}")
            return

        # 使用项目中已有的测试脚本
        test_script = backend_path / "scripts" / "smart_test_runner.py"
        if test_script.exists():::
            logger.info("使用smart_test_runner.py列出测试...")
            cmd = [sys.executable(), str(test_script), " - -list"]
            subprocess.run(cmd, cwd = str(backend_path))
        else,
            # 如果没有smart_test_runner.py(), 则直接使用pytest
            logger.info("直接使用pytest列出测试...")

            # 激活虚拟环境
            original_path = os.environ.get('PATH', '')
            if sys.platform == "win32":::
                venv_path = backend_path / "venv" / "Scripts"
                os.environ['PATH'] = f"{venv_path};{original_path}"
            else,
                venv_path = backend_path / "venv" / "bin"
                os.environ['PATH'] = f"{venv_path}{original_path}"

            try,
                # 列出测试
                cmd = [sys.executable(), " - m", "pytest", " - -collect - only", " - q"]
                subprocess.run(cmd, cwd = str(backend_path))
            finally,
                # 恢复环境变量
                os.environ['PATH'] = original_path

    except Exception as e, ::
        logger.error(f"列出测试时出错, {e}")


if __name'__main__':::
    test()