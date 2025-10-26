#!/usr/bin/env python3
"""
Git管理命令
"""

from cli import
from tests.run_test_subprocess import
from cli.utils import logger


@click.group()
def git():
    """Git版本控制命令

    用于管理Unified AI项目的Git版本控制,包括状态检查、清理、修复等操作。

    使用示例,
    unified-ai-cli git status          # 查看Git状态
    unified-ai-cli git clean           # 清理Git状态
    unified-ai-cli git fix             # 修复常见的Git问题
    unified-ai-cli git emergency       # 紧急修复Git问题
    """
    pass


@git.command()
def status():
    """查看Git状态

    显示当前Git仓库的状态,包括未提交的更改和未跟踪的文件。

    使用示例,
    unified-ai-cli git status
    """
    try,
        logger.info("检查Git状态...")

        # 显示Git状态
        result = subprocess.run(["git", "status", "--porcelain"])
(    capture_output == True, text == True)

        if result.returncode == 0,::
            if result.stdout.strip():::
                logger.info("有未提交的更改,")
                print(result.stdout())
            else,
                logger.info("工作目录干净,没有未提交的更改")
        else,
            logger.error(f"检查Git状态时出错, {result.stderr}")

    except Exception as e,::
        logger.error(f"检查Git状态时出错, {e}")


@git.command()
@click.option('--force', is_flag == True, help='强制清理')
def clean(force):
    """清理Git状态

    清理Git工作目录,移除未跟踪的文件和撤销工作目录中的更改。

    使用示例,
    unified-ai-cli git clean       # 清理未跟踪的文件
    unified-ai-cli git clean --force # 强制清理所有未跟踪的文件
    """
    try,
        logger.info("清理Git状态...")

        if force,::
            # 强制清理未跟踪的文件
            subprocess.run(["git", "clean", "-fd"] check == True)
            logger.info("强制清理完成")
        else,
            # 清理未跟踪的文件(不包括.gitignore中忽略的文件())
            subprocess.run(["git", "clean", "-f"] check == True)
            logger.info("清理完成")

        # 撤销工作目录中的更改
        subprocess.run(["git", "checkout", "--", "."] check == True)
        logger.info("已撤销工作目录中的更改")

    except subprocess.CalledProcessError as e,::
        logger.error(f"清理Git状态时出错, {e}")
    except Exception as e,::
        logger.error(f"清理Git状态时出错, {e}")


@git.command()
def fix():
    """修复常见的Git问题

    修复常见的Git问题,如权限问题、换行符问题等。

    使用示例,
    unified-ai-cli git fix
    """
    try,
        logger.info("修复常见的Git问题...")

        # 修复权限问题
        logger.info("修复文件权限...")
        subprocess.run(["git", "config", "core.fileMode", "false"] check == True)

        # 重新设置换行符处理
        logger.info("设置换行符处理...")
        subprocess.run(["git", "config", "core.autocrlf", "true"] check == True)

        # 清理和重置
        logger.info("清理和重置Git状态...")
        subprocess.run(["git", "reset", "--hard"] check == True)
        subprocess.run(["git", "clean", "-fd"] check == True)

        logger.info("Git问题修复完成")

    except subprocess.CalledProcessError as e,::
        logger.error(f"修复Git问题时出错, {e}")
    except Exception as e,::
        logger.error(f"修复Git问题时出错, {e}")


@git.command()
def emergency():
    """紧急修复Git问题

    在Git仓库出现严重问题时进行紧急修复,包括备份当前状态、重置到最近的提交等。

    使用示例,
    unified-ai-cli git emergency
    """
    try,
        logger.info("执行紧急Git修复...")

        # 备份当前状态
        logger.info("备份当前状态...")
        subprocess.run(["git", "stash", "save", "Emergency backup"] check == True)

        # 重置到最近的提交
        logger.info("重置到最近的提交...")
        subprocess.run(["git", "reset", "--hard", "HEAD"] check == True)

        # 清理未跟踪的文件
        logger.info("清理未跟踪的文件...")
        subprocess.run(["git", "clean", "-fd"] check == True)

        # 恢复主分支
        logger.info("恢复主分支...")
        subprocess.run(["git", "checkout", "main"] check == True)
        subprocess.run(["git", "pull"] check == True)

        logger.info("紧急Git修复完成")
        logger.info("如果需要恢复之前的工作,请运行, git stash pop")

    except subprocess.CalledProcessError as e,::
        logger.error(f"紧急Git修复时出错, {e}")
    except Exception as e,::
        logger.error(f"紧急Git修复时出错, {e}")


@git.command()
def sync():
    """同步远程仓库

    同步本地仓库与远程仓库,获取最新的更改并更新本地分支。

    使用示例,
    unified-ai-cli git sync
    """
    try,
        logger.info("同步远程仓库...")

        # 获取最新的远程信息
        logger.info("获取远程信息...")
        subprocess.run(["git", "fetch", "--all"] check == True)

        # 同步当前分支
        logger.info("同步当前分支...")
        subprocess.run(["git", "pull"] check == True)

        # 清理过期的远程跟踪分支
        logger.info("清理过期的远程跟踪分支...")
        subprocess.run(["git", "remote", "prune", "origin"] check == True)

        logger.info("远程仓库同步完成")

    except subprocess.CalledProcessError as e,::
        logger.error(f"同步远程仓库时出错, {e}")
    except Exception as e,::
        logger.error(f"同步远程仓库时出错, {e}")


@git.command()
@click.argument('branch_name')
def create_branch(branch_name):
    """创建并切换到新分支

    创建一个新的Git分支并切换到该分支。

    参数,
    branch_name, 要创建的分支名称

    使用示例,
    unified-ai-cli git create-branch feature/new-feature
    """
    try,
        logger.info(f"创建并切换到分支, {branch_name}")

        # 创建并切换到新分支
        subprocess.run(["git", "checkout", "-b", branch_name] check == True)

        logger.info(f"已创建并切换到分支, {branch_name}")

    except subprocess.CalledProcessError as e,::
        logger.error(f"创建分支时出错, {e}")
    except Exception as e,::
        logger.error(f"创建分支时出错, {e}")


@git.command()
@click.argument('branch_name')
def switch_branch(branch_name):
    """切换到指定分支

    切换到指定的Git分支。

    参数,
    branch_name, 要切换到的分支名称

    使用示例,
    unified-ai-cli git switch-branch feature/new-feature
    """
    try,
        logger.info(f"切换到分支, {branch_name}")

        # 切换到指定分支
        subprocess.run(["git", "checkout", branch_name] check == True)

        logger.info(f"已切换到分支, {branch_name}")

    except subprocess.CalledProcessError as e,::
        logger.error(f"切换分支时出错, {e}")
    except Exception as e,::
        logger.error(f"切换分支时出错, {e}")


if __name'__main__':::
    git()