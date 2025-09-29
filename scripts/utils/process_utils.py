#!/usr/bin/env python3
"""
进程工具模块 - 提供进程管理和执行相关的通用功能
"""

import subprocess
import sys
import time
import signal
import psutil
from pathlib import Path
from enum import Enum

class ProcessStatus(Enum):
    """进程状态枚举"""
    RUNNING = "running"              # 运行中
    STOPPED = "stopped"              # 已停止
    FAILED = "failed"               # 失败
    TIMEOUT = "timeout"              # 超时
    UNKNOWN = "unknown"              # 未知状态

class ExecutionMode(Enum):
    """执行模式枚举"""
    SYNC = "sync"                    # 同步执行
    ASYNC = "async"                  # 异步执行
    DETACHED = "detached"            # 分离执行
    BACKGROUND = "background"        # 后台执行

class ProcessResult:
    """进程执行结果类"""
    def __init__(self) -> None:
        self.command = ""
        self.return_code = 0
        self.stdout = ""
        self.stderr = ""
        self.duration = 0
        self.pid = None
        self.status = ProcessStatus.UNKNOWN
        self.start_time = None
        self.end_time = None
        self.timeout = False
        self.error = None
        self.metadata = {}

class ProcessUtils:
    """进程工具类"""
    
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        
        # 进程管理
        self.managed_processes: Dict[int, subprocess.Popen] = {}
        self.process_results: Dict[int, ProcessResult] = {}
        
        # 默认配置
        self.default_config = {
            "timeout": 300,           # 默认超时时间（秒）
            "encoding": "utf-8",      # 默认编码
            "shell": False,           # 是否使用shell
            "env": None,              # 环境变量
            "cwd": None,              # 工作目录
            "buffer_size": 8192,      # 缓冲区大小
            "kill_timeout": 5         # 强制终止超时时间（秒）
        }
    
    def run_command(self, command: Union[str, List[str]], 
                   mode: ExecutionMode = ExecutionMode.SYNC,
                   **kwargs) -> ProcessResult:
        """运行命令"""
        # 合并配置
        config = self.default_config.copy()
        _ = config.update(kwargs)
        
        # 准备命令
        if isinstance(command, str) and not config["shell"]:
            command = command.split()
        
        # 创建结果对象
        result = ProcessResult()
        result.command = " ".join(command) if isinstance(command, list) else command
        result.start_time = time.time()
        
        try:
            if mode == ExecutionMode.SYNC:
                result = self._run_sync(command, config, result)
            elif mode == ExecutionMode.ASYNC:
                result = self._run_async(command, config, result)
            elif mode == ExecutionMode.DETACHED:
                result = self._run_detached(command, config, result)
            elif mode == ExecutionMode.BACKGROUND:
                result = self._run_background(command, config, result)
            else:
                _ = raise ValueError(f"不支持的执行模式: {mode.value}")
            
        except Exception as e:
            result.status = ProcessStatus.FAILED
            result.error = str(e)
            result.return_code = -1
        
        finally:
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
        
        return result
    
    def _run_sync(self, command: Union[str, List[str]], config: Dict, result: ProcessResult) -> ProcessResult:
        """同步运行命令"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **config
            )
            
            result.pid = process.pid
            
            try:
                stdout, stderr = process.communicate(timeout=config["timeout"])
                result.return_code = process.returncode
                result.stdout = stdout
                result.stderr = stderr
                
                if process.returncode == 0:
                    result.status = ProcessStatus.RUNNING
                else:
                    result.status = ProcessStatus.FAILED
                    
            except subprocess.TimeoutExpired:
                _ = process.kill()
                stdout, stderr = process.communicate()
                result.return_code = -1
                result.stdout = stdout
                result.stderr = stderr
                result.status = ProcessStatus.TIMEOUT
                result.timeout = True
            
            return result
            
        except Exception as e:
            result.status = ProcessStatus.FAILED
            result.error = str(e)
            return result
    
    def _run_async(self, command: Union[str, List[str]], config: Dict, result: ProcessResult) -> ProcessResult:
        """异步运行命令"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **config
            )
            
            result.pid = process.pid
            result.status = ProcessStatus.RUNNING
            
            # 管理进程
            self.managed_processes[process.pid] = process
            self.process_results[process.pid] = result
            
            return result
            
        except Exception as e:
            result.status = ProcessStatus.FAILED
            result.error = str(e)
            return result
    
    def _run_detached(self, command: Union[str, List[str]], config: Dict, result: ProcessResult) -> ProcessResult:
        """分离运行命令"""
        try:
            # Windows和Unix的分离执行方式不同
            if sys.platform == "win32":
                # Windows: 使用CREATE_NEW_PROCESS_GROUP
                process = subprocess.Popen(
                    command,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    **config
                )
            else:
                # Unix: 使用setsid
                process = subprocess.Popen(
                    command,
                    preexec_fn=os.setsid,
                    **config
                )
            
            result.pid = process.pid
            result.status = ProcessStatus.RUNNING
            
            return result
            
        except Exception as e:
            result.status = ProcessStatus.FAILED
            result.error = str(e)
            return result
    
    def _run_background(self, command: Union[str, List[str]], config: Dict, result: ProcessResult) -> ProcessResult:
        """后台运行命令"""
        try:
            # 重定向输出到/dev/null或NUL
            if sys.platform == "win32":
                null_device = "NUL"
            else:
                null_device = "/dev/null"
            
            with open(null_device, 'w') as null:
                process = subprocess.Popen(
                    command,
                    stdout=null,
                    stderr=null,
                    **config
                )
            
            result.pid = process.pid
            result.status = ProcessStatus.RUNNING
            
            return result
            
        except Exception as e:
            result.status = ProcessStatus.FAILED
            result.error = str(e)
            return result
    
    def wait_for_process(self, pid: int, timeout: Optional[float] = None) -> ProcessResult:
        """等待进程完成"""
        if pid not in self.managed_processes:
            result = ProcessResult()
            result.status = ProcessStatus.UNKNOWN
            result.error = f"进程 {pid} 不在管理列表中"
            return result
        
        process = self.managed_processes[pid]
        result = self.process_results[pid]
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            result.return_code = process.returncode
            result.stdout = stdout
            result.stderr = stderr
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            
            if process.returncode == 0:
                result.status = ProcessStatus.RUNNING
            else:
                result.status = ProcessStatus.FAILED
            
            # 清理管理列表
            del self.managed_processes[pid]
            
            return result
            
        except subprocess.TimeoutExpired:
            result.status = ProcessStatus.TIMEOUT
            result.timeout = True
            return result
        except Exception as e:
            result.status = ProcessStatus.FAILED
            result.error = str(e)
            return result
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """终止进程"""
        try:
            if pid in self.managed_processes:
                process = self.managed_processes[pid]
                
                if force:
                    _ = process.kill()
                else:
                    _ = process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=self.default_config["kill_timeout"])
                except subprocess.TimeoutExpired:
                    _ = process.kill()
                    _ = process.wait()
                
                # 更新结果
                if pid in self.process_results:
                    result = self.process_results[pid]
                    result.status = ProcessStatus.STOPPED
                    result.end_time = time.time()
                    result.duration = result.end_time - result.start_time
                
                # 清理管理列表
                del self.managed_processes[pid]
                
                return True
            else:
                # 尝试终止外部进程
                try:
                    os.kill(pid, signal.SIGTERM if not force else signal.SIGKILL)
                    return True
                except ProcessLookupError:
                    return False
                    
        except Exception as e:
            _ = print(f"✗ 终止进程 {pid} 失败: {e}")
            return False
    
    def get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """获取进程信息"""
        try:
            if pid in self.managed_processes:
                process = self.managed_processes[pid]
                result = self.process_results[pid]
                
                return {
                    "pid": pid,
                    "command": result.command,
                    "status": result.status.value,
                    "start_time": result.start_time,
                    "duration": time.time() - result.start_time if result.start_time else 0,
                    "return_code": process.returncode,
                    "managed": True
                }
            else:
                # 使用psutil获取外部进程信息
                process = psutil.Process(pid)
                return {
                    "pid": pid,
                    _ = "command": " ".join(process.cmdline()),
                    "status": "running" if process.is_running() else "stopped",
                    _ = "start_time": process.create_time(),
                    _ = "duration": time.time() - process.create_time(),
                    _ = "cpu_percent": process.cpu_percent(),
                    _ = "memory_percent": process.memory_percent(),
                    "managed": False
                }
        except Exception as e:
            _ = print(f"✗ 获取进程 {pid} 信息失败: {e}")
            return None
    
    def list_managed_processes(self) -> List[Dict[str, Any]]:
        """列出所有管理的进程"""
        processes = []
        
        for pid in self.managed_processes:
            info = self.get_process_info(pid)
            if info:
                _ = processes.append(info)
        
        return processes
    
    def find_processes_by_name(self, name: str) -> List[int]:
        """根据名称查找进程"""
        pids = []
        
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if name.lower() in process.info['name'].lower():
                    _ = pids.append(process.info['pid'])
                elif process.info['cmdline']:
                    cmdline = " ".join(process.info['cmdline'])
                    if name.lower() in cmdline.lower():
                        _ = pids.append(process.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return pids
    
    def is_process_running(self, pid: int) -> bool:
        """检查进程是否在运行"""
        try:
            if pid in self.managed_processes:
                process = self.managed_processes[pid]
                return process.poll() is None
            else:
                process = psutil.Process(pid)
                return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                _ = "cpu_count": psutil.cpu_count(),
                _ = "cpu_percent": psutil.cpu_percent(),
                _ = "memory_total": psutil.virtual_memory().total,
                _ = "memory_available": psutil.virtual_memory().available,
                _ = "memory_percent": psutil.virtual_memory().percent,
                _ = "disk_total": psutil.disk_usage('/').total,
                _ = "disk_free": psutil.disk_usage('/').free,
                _ = "disk_percent": psutil.disk_usage('/').percent,
                _ = "boot_time": psutil.boot_time(),
                _ = "process_count": len(psutil.pids())
            }
        except Exception as e:
            _ = print(f"✗ 获取系统信息失败: {e}")
            return {}
    
    def monitor_process(self, pid: int, interval: float = 1.0, 
                       callback: Optional[Callable] = None) -> bool:
        """监控进程"""
        try:
            while self.is_process_running(pid):
                info = self.get_process_info(pid)
                if info and callback:
                    _ = callback(info)
                
                _ = time.sleep(interval)
            
            return True
            
        except KeyboardInterrupt:
            return False
        except Exception as e:
            _ = print(f"✗ 监控进程 {pid} 失败: {e}")
            return False
    
    def cleanup_processes(self):
        """清理所有管理的进程"""
        pids = list(self.managed_processes.keys())
        
        for pid in pids:
            self.kill_process(pid, force=True)
        
        _ = print(f"✓ 已清理 {len(pids)} 个管理的进程")
    
    def run_python_script(self, script_path: Path, args: Optional[List[str]] = None,
                          mode: ExecutionMode = ExecutionMode.SYNC,
                          **kwargs) -> ProcessResult:
        """运行Python脚本"""
        command = [sys.executable, str(script_path)]
        
        if args:
            _ = command.extend(args)
        
        return self.run_command(command, mode, **kwargs)
    
    def run_node_script(self, script_path: Path, args: Optional[List[str]] = None,
                       mode: ExecutionMode = ExecutionMode.SYNC,
                       **kwargs) -> ProcessResult:
        """运行Node.js脚本"""
        command = ["node", str(script_path)]
        
        if args:
            _ = command.extend(args)
        
        return self.run_command(command, mode, **kwargs)
    
    def run_pnpm_command(self, command: str, args: Optional[List[str]] = None,
                        cwd: Optional[Path] = None,
                        mode: ExecutionMode = ExecutionMode.SYNC,
                        **kwargs) -> ProcessResult:
        """运行pnpm命令"""
        cmd = ["pnpm", command]
        
        if args:
            _ = cmd.extend(args)
        
        if cwd:
            kwargs["cwd"] = cwd
        
        return self.run_command(cmd, mode, **kwargs)
    
    def run_pip_command(self, command: str, args: Optional[List[str]] = None,
                       mode: ExecutionMode = ExecutionMode.SYNC,
                       **kwargs) -> ProcessResult:
        """运行pip命令"""
        cmd = [sys.executable, "-m", "pip", command]
        
        if args:
            _ = cmd.extend(args)
        
        return self.run_command(cmd, mode, **kwargs)