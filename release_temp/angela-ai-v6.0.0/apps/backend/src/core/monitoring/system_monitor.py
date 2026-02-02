from typing import Any

import psutil


class SystemMonitor:
    """Monitors system resources like CPU and memory usage."""

    def __init__(self):
        """Initializes the SystemMonitor."""
        print("SystemMonitor initialized.")

    def get_cpu_usage(self, interval: float = 0.1) -> float:
        """Returns the current system-wide CPU utilization as a percentage.

        Args:
            interval (float): The interval in seconds to sample CPU usage.

        Returns:
            float: CPU utilization percentage.

        """
        return psutil.cpu_percent(interval=interval)

    def get_memory_usage(self) -> dict[str, Any]:
        """Returns system memory usage statistics.

        Returns:
            Dict[str, Any]: A dictionary containing memory usage details (total, available, percent, used, free).

        """
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free,
        }

    def get_disk_usage(self, path: str = "/") -> dict[str, Any]:
        """Returns disk usage statistics for a given path.

        Args:
            path (str): The disk path to check (e.g., '/' for root on Unix, 'C:/' on Windows).

        Returns:
            Dict[str, Any]: A dictionary containing disk usage details (total, used, free, percent).

        """
        disk = psutil.disk_usage(path)
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }


if __name__ == "__main__":
    # Example Usage
    monitor = SystemMonitor()

    print("\n--- CPU Usage ---")
    print(f"CPU Usage: {monitor.get_cpu_usage()}%")

    print("\n--- Memory Usage ---")
    mem_info = monitor.get_memory_usage()
    print(f"Total Memory: {mem_info['total'] / (1024**3):.2f} GB")
    print(f"Used Memory: {mem_info['used'] / (1024**3):.2f} GB")
    print(f"Memory Percentage: {mem_info['percent']}%")

    print("\n--- Disk Usage (C:/) ---")
    try:
        disk_info = monitor.get_disk_usage("C:/")
        print(f"Total Disk: {disk_info['total'] / (1024**3):.2f} GB")
        print(f"Used Disk: {disk_info['used'] / (1024**3):.2f} GB")
        print(f"Free Disk: {disk_info['free'] / (1024**3):.2f} GB")
        print(f"Disk Percentage: {disk_info['percent']}%")
    except Exception as e:
        print(f"Could not get disk usage for C:/: {e}")
