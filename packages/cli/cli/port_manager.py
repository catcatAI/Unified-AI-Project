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
import logging

logger = logging.getLogger(__name__)


class PortManager:
    PORT_CONFIG = {
        "FRONTEND_DASHBOARD": 3000,
        "DESKTOP_APP": 3001,
        "BACKEND_API": 8000,
        "BACKEND_DEV": 8000,
        "BACKEND_TEST": 8001,
    }
    PID_FILE_DIR = Path.home() / ".unified-ai" / "pids"

    def __init__(self):
        self.PID_FILE_DIR.mkdir(parents=True, exist_ok=True)

    def get_port(self, service_name: str) -> Optional[int]:
        return self.PORT_CONFIG.get(service_name.upper())

    def check_port_in_use(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return False
        except OSError:
            return True

    def find_process_by_port(self, port: int) -> Optional[psutil.Process]:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port:
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
        return None

    def kill_process_by_port(self, port: int) -> bool:
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
        try:
            pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
            with open(pid_file, 'w') as f:
                f.write(str(pid))
            return True
        except Exception as e:
            print(f"Failed to save PID for {service_name}: {e}")
            return False

    def load_pid(self, service_name: str) -> Optional[int]:
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
        pid = self.load_pid(service_name)
        if pid:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
                pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                if pid_file.exists():
                    pid_file.unlink()
                return True
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                    pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                    if pid_file.exists():
                        pid_file.unlink()
                    return True
                except psutil.NoSuchProcess:
                    pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                    if pid_file.exists():
                        pid_file.unlink()
                    return True
            except psutil.NoSuchProcess:
                pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
                if pid_file.exists():
                    pid_file.unlink()
                return True
            except Exception as e:
                print(f"Failed to kill existing process for {service_name}: {e}")
        port = self.get_port(service_name)
        if port and self.check_port_in_use(port):
            return self.kill_process_by_port(port)

        return False

    def get_all_ports(self) -> Dict[str, int]:
        return self.PORT_CONFIG.copy()

    def print_port_info(self):
        print("Unified AI Project Port Configuration:")
        print("=" * 40)
        for service, port in self.PORT_CONFIG.items():
            in_use = " (IN USE)" if self.check_port_in_use(port) else ""
            print(f"{service:20} {port}{in_use}")
        print("=" * 40)


def main():
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
