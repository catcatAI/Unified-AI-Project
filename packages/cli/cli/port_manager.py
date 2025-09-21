#!/usr/bin/env python3
"""
Unified Port Manager - 统一管理所有应用的端口配置
"""

import os
import sys
import json
import psutil
import socket
from typing import Dict, List, Optional
from pathlib import Path

class PortManager:
    # 统一端口配置
    PORT_CONFIG = {
        "FRONTEND_DASHBOARD": 3000,
        "DESKTOP_APP": 3001,
        "BACKEND_API": 8000,
        "BACKEND_DEV": 8000,
        "BACKEND_TEST": 8001,
    }
    
    PID_FILE_DIR = Path.home() / ".unified-ai" / "pids"
    
    def __init__(self):
        """初始化端口管理器"""
        # 创建PID文件目录
        self.PID_FILE_DIR.mkdir(parents=True, exist_ok=True)
        
    def get_port(self, service_name: str) -> Optional[int]:
        """
        获取指定服务的端口号
        
        Args:
            service_name: 服务名称
            
        Returns:
            端口号或None
        """
        return self.PORT_CONFIG.get(service_name.upper())
    
    def check_port_in_use(self, port: int) -> bool:
        """
        检查端口是否被占用
        
        Args:
            port: 端口号
            
        Returns:
            True表示端口被占用，False表示端口未被占用
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return False
        except OSError:
            return True
    
    def find_process_by_port(self, port: int) -> Optional[psutil.Process]:
        """
        查找占用指定端口的进程
        
        Args:
            port: 端口号
            
        Returns:
            进程对象或None
        """
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port:
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
        return None
    
    def kill_process_by_port(self, port: int) -> bool:
        """
        杀死占用指定端口的进程
        
        Args:
            port: 端口号
            
        Returns:
            True表示成功杀死进程，False表示失败
        """
        proc = self.find_process_by_port(port)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                return True
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    return True
                except psutil.NoSuchProcess:
                    return True
            except psutil.NoSuchProcess:
                return True
            except Exception as e:
                print(f"Failed to kill process on port {port}: {e}")
                return False
        return False
    
    def save_pid(self, service_name: str, pid: int) -> bool:
        """
        保存服务的PID
        
        Args:
            service_name: 服务名称
            pid: 进程ID
            
        Returns:
            True表示保存成功，False表示保存失败
        """
        try:
            pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
            with open(pid_file, 'w') as f:
                f.write(str(pid))
            return True
        except Exception as e:
            print(f"Failed to save PID for {service_name}: {e}")
            return False
    
    def load_pid(self, service_name: str) -> Optional[int]:
        """
        加载服务的PID
        
        Args:
            service_name: 服务名称
            
        Returns:
            进程ID或None
        """
        try:
            pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    return int(f.read().strip())
            return None
        except Exception as e:
            print(f"Failed to load PID for {service_name}: {e}")
            return None
    
    def kill_existing_process(self, service_name: str) -> bool:
        """
        杀死已存在的服务进程
        
        Args:
            service_name: 服务名称
            
        Returns:
            True表示成功杀死进程，False表示失败
        """
        # 首先尝试通过PID文件杀死进程
        pid = self.load_pid(service_name)
        if pid:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
                # 删除PID文件
                pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                if pid_file.exists():
                    pid_file.unlink()
                return True
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    # 删除PID文件
                    pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                    if pid_file.exists():
                        pid_file.unlink()
                    return True
                except psutil.NoSuchProcess:
                    # 删除PID文件
                    pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                    if pid_file.exists():
                        pid_file.unlink()
                    return True
            except psutil.NoSuchProcess:
                # 删除PID文件
                pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                if pid_file.exists():
                    pid_file.unlink()
                return True
            except Exception as e:
                print(f"Failed to kill existing process for {service_name}: {e}")
        
        # 如果通过PID文件失败，尝试通过端口杀死进程
        port = self.get_port(service_name)
        if port and self.check_port_in_use(port):
            return self.kill_process_by_port(port)
        
        return False
    
    def get_all_ports(self) -> Dict[str, int]:
        """
        获取所有端口配置
        
        Returns:
            端口配置字典
        """
        return self.PORT_CONFIG.copy()
    
    def print_port_info(self):
        """打印端口信息"""
        print("Unified AI Project Port Configuration:")
        print("=" * 40)
        for service, port in self.PORT_CONFIG.items():
            in_use = " (IN USE)" if self.check_port_in_use(port) else ""
            print(f"{service:20}: {port}{in_use}")
        print("=" * 40)

def main():
    """主函数"""
    pm = PortManager()
    
    if len(sys.argv) < 2:
        print("Usage: python port_manager.py [command] [service_name]")
        print("Commands:")
        print("  info          - Show port information")
        print("  check [port]  - Check if port is in use")
        print("  kill [port]   - Kill process on port")
        print("  kill-service [service] - Kill existing service process")
        print("  get-port [service] - Get port for service")
        return
    
    command = sys.argv[1]
    
    if command == "info":
        pm.print_port_info()
    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: python port_manager.py check [port]")
            return
        port = int(sys.argv[2])
        in_use = pm.check_port_in_use(port)
        print(f"Port {port} is {'in use' if in_use else 'available'}")
    elif command == "kill":
        if len(sys.argv) < 3:
            print("Usage: python port_manager.py kill [port]")
            return
        port = int(sys.argv[2])
        success = pm.kill_process_by_port(port)
        if success:
            print(f"Successfully killed process on port {port}")
        else:
            print(f"Failed to kill process on port {port}")
    elif command == "kill-service":
        if len(sys.argv) < 3:
            print("Usage: python port_manager.py kill-service [service]")
            return
        service_name = sys.argv[2]
        success = pm.kill_existing_process(service_name)
        if success:
            print(f"Successfully killed existing process for {service_name}")
        else:
            print(f"Failed to kill existing process for {service_name}")
    elif command == "get-port":
        if len(sys.argv) < 3:
            print("Usage: python port_manager.py get-port [service]")
            return
        service_name = sys.argv[2]
        port = pm.get_port(service_name)
        if port:
            print(f"Port for {service_name}: {port}")
        else:
            print(f"Unknown service: {service_name}")
    else:
        print(f"Unknown command: {command}")
        print("Usage: python port_manager.py [command] [service_name]")

if __name__ == "__main__":
    main()