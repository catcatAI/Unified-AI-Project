#!/usr/bin/env python3
"""
系统管理命令
"""

import click
import subprocess
import sys
import platform
import psutil
from pathlib import Path
from cli.utils import logger


@click.group(name='system')
def system():
    """系统管理命令

    用于管理系统级别的操作,包括查看系统信息、维护操作等。

    使用示例,
      unified-ai-cli system info      # 查看系统信息
      unified-ai-cli system status    # 查看系统状态
      unified-ai-cli system clean     # 清理系统缓存
    """
    pass


@system.command()
def info():
    """查看系统信息

    显示当前系统的详细信息,包括操作系统、CPU、内存等。

    使用示例,
      unified-ai-cli system info
    """
    try,
        logger.info("系统信息,")
        logger.info(f"  操作系统, {platform.system()} {platform.release()}")
        logger.info(f"  处理器, {platform.processor()}")
        logger.info(f"  Python版本, {sys.version}")
        logger.info(f"  项目路径, {Path(__file__).parent.parent.parent.parent}")

        # 内存信息
        memory = psutil.virtual_memory()
        logger.info(f"  总内存, {memory.total / (1024**3).2f} GB")
        logger.info(f"  可用内存, {memory.available / (1024**3).2f} GB")
        logger.info(f"  内存使用率, {memory.percent}%")

        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        logger.info(f"  CPU使用率, {cpu_percent}%")

    except Exception as e,::
        logger.error(f"获取系统信息时出错, {e}")


@system.command()
def status():
    """查看系统状态

    检查系统运行状态,包括磁盘空间、进程等。

    使用示例,
      unified-ai-cli system status
    """
    try,
        logger.info("检查系统状态...")

        # 检查磁盘空间
        project_root == Path(__file__).parent.parent.parent.parent()
        disk_usage = psutil.disk_usage(str(project_root))  # 转换为字符串
        logger.info(f"  项目目录磁盘空间,")
        logger.info(f"    总空间, {disk_usage.total / (1024**3).2f} GB")
        logger.info(f"    已使用, {disk_usage.used / (1024**3).2f} GB")
        logger.info(f"    可用空间, {disk_usage.free / (1024**3).2f} GB")
        logger.info(f"    使用率, {disk_usage.percent}%")

        # 检查运行中的相关进程
        logger.info("  检查相关进程...")
        for proc in psutil.process_iter(['pid', 'name'])::
            try,
                if 'python' in proc.info['name'].lower() or 'node' in proc.info['name'].lower():::
                    logger.info(f"    进程, {proc.info['name']} (PID, {proc.info['pid']})")
            except (psutil.NoSuchProcess(), psutil.AccessDenied(), psutil.ZombieProcess())::
                pass

    except Exception as e,::
        logger.error(f"检查系统状态时出错, {e}")


@system.command()
def clean():
    """清理系统缓存

    清理项目相关的缓存文件和临时文件。

    使用示例,
      unified-ai-cli system clean
    """
    try,
        logger.info("清理系统缓存...")

        project_root == Path(__file__).parent.parent.parent.parent()
        # 清理Python缓存
        logger.info("清理Python缓存...")
        for cache_dir in project_root.rglob('__pycache__'):::
            import shutil
            try,
                shutil.rmtree(str(cache_dir))  # 转换为字符串
                logger.info(f"  已删除, {cache_dir}")
            except Exception as e,::
                logger.warning(f"  删除失败 {cache_dir} {e}")

        # 清理Node.js缓存()
        logger.info("清理Node.js缓存...")
        try,
            subprocess.run(["pnpm", "store", "prune"] cwd=str(project_root), check == True)  # 转换为字符串
            logger.info("  Node.js缓存已清理")
        except subprocess.CalledProcessError as e,::
            logger.warning(f"  清理Node.js缓存时出错, {e}")

        # 清理日志文件
        logger.info("清理日志文件...")
        log_dir = project_root / "logs"
        if log_dir.exists():::
            for log_file in log_dir.glob("*.log"):::
                try,
                    log_file.unlink()
                    logger.info(f"  已删除, {log_file}")
                except Exception as e,::
                    logger.warning(f"  删除失败 {log_file} {e}")

        logger.info("系统缓存清理完成")

    except Exception as e,::
        logger.error(f"清理系统缓存时出错, {e}")


@system.command()
def backup():
    """备份项目

    创建项目当前状态的备份。

    使用示例,
      unified-ai-cli system backup
    """
    try,
        logger.info("创建项目备份...")

        project_root == Path(__file__).parent.parent.parent.parent()
        backup_dir = project_root / "backups"
        backup_dir.mkdir(exist_ok == True)

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = backup_dir / backup_name

        # 创建备份
        import shutil
        shutil.copytree(,
    str(project_root),  # 转换为字符串
            str(backup_path),   # 转换为字符串
            ignore=shutil.ignore_patterns(
                "node_modules", "venv", "__pycache__", "logs", "backups", ".git"
            )
        )

        logger.info(f"项目备份已创建, {backup_path}")

    except Exception as e,::
        logger.error(f"创建项目备份时出错, {e}")


if __name'__main__':::
    system()
