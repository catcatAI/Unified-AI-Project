
import psutil
import time
import os
import sys

def check_resources():
    print("=" * 60)
    print("🔍 System Resource Monitor")
    print("=" * 60)
    sys.stdout.flush()
    
    # Check overall system
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    print(f"Total System CPU: {cpu_percent}%")
    print(f"Total System Memory: {memory.percent}% (Used: {memory.used / (1024**3):.2f} GB / Total: {memory.total / (1024**3):.2f} GB)")
    print("-" * 60)
    sys.stdout.flush()
    
    # Check specific processes
    print(f"{'PID':<8} {'Name':<25} {'CPU%':<10} {'Memory (MB)':<15} {'Status':<10}")
    print("-" * 60)
    
    target_processes = ["python", "electron", "node", "uvicorn"]
    
    found_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            name = proc.info['name'].lower()
            if any(t in name for t in target_processes):
                found_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Measure CPU over time
    if found_processes:
        # Initial call to prime cpu_percent
        for p in found_processes:
             try:
                p.cpu_percent()
             except: pass
        
        time.sleep(2)
        
        for p in found_processes:
            try:
                # Re-fetch info
                with p.oneshot():
                    name = p.name()
                    pid = p.pid
                    cpu = p.cpu_percent()
                    mem = p.memory_info().rss / (1024 * 1024)
                    status = p.status()
                    
                print(f"{pid:<8} {name:<25} {cpu:<10.1f} {mem:<15.1f} {status:<10}")
                sys.stdout.flush()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"{p.pid:<8} {'(Terminated)':<25} {'-':<10} {'-':<15} {'-':<10}")
                
    else:
        print("No target processes found.")
        
    print("=" * 60)

if __name__ == "__main__":
    check_resources()
