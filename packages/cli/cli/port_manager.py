#!/usr/bin/env python3
"""
Unified Port Manager - 统一管理所有应用的端口配置
"""

import json
import logging
import os
import socket
import sys
from pathlib import Path
from typing import Dict, List, Optional

import psutil

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
                sock.bind(("localhost", port))
                return False
        except OSError:
            return True

    def find_process_by_port(self, port: int) -> Optional[psutil.Process]:
        for proc in psutil.process_iter(["pid", "name", "connections"]):
            try:
                for conn in proc.info["connections"]:
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
            with open(pid_file, "w") as f:
                f.write(str(pid))
            return True
        except Exception as e:
            print(f"Failed to save PID for {service_name}: {e}")
            return False

    def load_pid(self, service_name: str) -> Optional[int]:
        try:
            pid_file = self.PID_FILE_DIR / f"{service_name.lower()}.pid"
            if pid_file.exists():
                with open(pid_file, "r") as f:
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


def main(argv=None):
    # argv is injectable so the no-argument behaviour the pnpm scripts rely on
    # is testable without spawning a subprocess.
    argv = list(sys.argv[1:] if argv is None else argv)
    pm = PortManager()

    if not argv:
        print("Usage: python3 port_manager.py [command] [service_name]")
        print("Commands:")
        print("  info          - Show port information")
        print("  check [port]  - Check one port, or every service port when omitted")
        print("  kill <port>   - Kill process on port (port is required)")
        print("  kill-service <service> - Kill existing service process (name required)")
        print("  get-port [service]      - Get port (all services when omitted)")
        return

    command = argv[0]

    if command == "info":
        pm.print_port_info()
    elif command == "check":
        # `pnpm port-check` runs this with no arguments, which used to print a
        # usage line and return — a "check" that checks nothing. No argument now
        # means "check every configured service port".
        if len(argv) < 2:
            for service, port in sorted(pm.get_all_ports().items()):
                in_use = pm.check_port_in_use(port)
                print(f"{service:20} {port} {'in use' if in_use else 'available'}")
            return
        port = int(argv[1])
        in_use = pm.check_port_in_use(port)
        print(f"Port {port} is {'in use' if in_use else 'available'}")
    elif command == "kill":
        # No default port on purpose: killing "the" port without being told which
        # one could take down the running backend.
        if len(argv) < 2:
            print("Usage: python3 port_manager.py kill <port>  (a port is required)")
            return
        port = int(argv[1])
        success = pm.kill_process_by_port(port)
        if success:
            print(f"Successfully killed process on port {port}")
        else:
            print(f"Failed to kill process on port {port}")
    elif command == "kill-service":
        # Without a service name there is nothing safe to kill — list what could
        # be targeted instead of silently doing nothing.
        if len(argv) < 2:
            print("Usage: python3 port_manager.py kill-service <service>")
            print("Known services: " + ", ".join(sorted(pm.get_all_ports())))
            return
        service_name = argv[1]
        success = pm.kill_existing_process(service_name)
        if success:
            print(f"Successfully killed existing process for {service_name}")
        else:
            print(f"Failed to kill existing process for {service_name}")
    elif command == "get-port":
        # `pnpm port-get` runs with no service; list them all.
        if len(argv) < 2:
            for service, port in sorted(pm.get_all_ports().items()):
                print(f"{service}: {port}")
            return
        service_name = argv[1]
        port = pm.get_port(service_name)
        if port:
            print(f"Port for {service_name}: {port}")
        else:
            print(f"Unknown service: {service_name}")
    else:
        print(f"Unknown command: {command}")
        print("Usage: python3 port_manager.py [command] [service_name]")


if __name__ == "__main__":
    main()
