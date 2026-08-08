"""
Direct GPU Usage Test — Bypasses torch entirely
Tests OpenCL, CUDA (via ctypes), and other GPU APIs directly
"""
import subprocess
import sys
import time
import json
import os

def test_opencl():
    """Test OpenCL via pyopencl"""
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
        results = []
        for p in platforms:
            for d in p.get_devices():
                results.append({
                    "platform": p.name,
                    "device": d.name,
                    "type": cl.device_type.to_string(d.type),
                    "compute_units": d.max_compute_units,
                    "clock_freq_mhz": d.max_clock_frequency,
                    "global_mem_gb": d.global_mem_size / (1024**3),
                    "local_mem_kb": d.local_mem_size / 1024,
                    "max_work_group_size": d.max_work_group_size,
                })
        return True, results
    except ImportError:
        return False, "pyopencl not installed"
    except Exception as e:
        return False, str(e)

def test_cuda_direct():
    """Test CUDA via direct DLL loading (no torch)"""
    try:
        # Try to load nvcuda.dll directly
        import ctypes
        import ctypes.util
        
        # Search for nvidia OpenCL DLL
        nvidia_paths = [
            r"C:\Windows\System32\nvcuda.dll",
            r"C:\Windows\System32\DriverStore\FileRepository\*\nvcuda.dll",
        ]
        
        # Also check for Intel OpenCL
        intel_paths = [
            r"C:\Windows\System32\IntelOpenCL64.dll",
            r"C:\Windows\System32\DriverStore\FileRepository\*\igdcl64.dll",
        ]
        
        # Try loading nvcuda
        for path in nvidia_paths:
            if os.path.exists(path):
                try:
                    dll = ctypes.windll.LoadLibrary(path)
                    return True, f"nvcuda.dll loaded from {path}"
                except:
                    pass
        
        # Check if nvidia-smi exists
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True, f"CUDA GPU detected: {result.stdout.strip()}"
        
        return False, "No CUDA GPU found"
    except FileNotFoundError:
        return False, "nvidia-smi not found"
    except Exception as e:
        return False, str(e)

def test_intel_gpu():
    """Test Intel GPU via igdcl64.dll"""
    try:
        import ctypes
        import glob
        
        # Find Intel OpenCL DLL
        patterns = [
            r"C:\Windows\System32\IntelOpenCL64.dll",
            r"C:\Windows\System32\DriverStore\FileRepository\igdcl*",
        ]
        
        for pattern in patterns:
            matches = glob.glob(pattern)
            for dll_path in matches:
                if os.path.isfile(dll_path):
                    try:
                        dll = ctypes.windll.LoadLibrary(dll_path)
                        return True, f"Intel GPU DLL loaded: {dll_path}"
                    except:
                        pass
        
        return False, "Intel GPU DLL not found"
    except Exception as e:
        return False, str(e)

def test_subprocess_gpu():
    """Test GPU via subprocess (torch in separate process)"""
    try:
        script = """
import torch
print(f"torch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
    # Quick GPU test
    x = torch.randn(100, 100).cuda()
    y = torch.mm(x, x.t())
    print(f"GPU matrix multiply OK: {y.shape}")
else:
    print("No CUDA GPU")
    # Try CPU
    x = torch.randn(100, 100)
    y = torch.mm(x, x.t())
    print(f"CPU matrix multiply OK: {y.shape}")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr[:200]
    except subprocess.TimeoutExpired:
        return False, "torch import timed out"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("GPU Direct Usage Test — Bypassing torch")
    print("=" * 60)
    
    tests = [
        ("OpenCL (pyopencl)", test_opencl),
        ("CUDA (nvidia-smi)", test_cuda_direct),
        ("Intel GPU (DLL)", test_intel_gpu),
        ("torch (subprocess)", test_subprocess_gpu),
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        success, info = test_func()
        results[name] = {"success": success, "info": info}
        status = "✓" if success else "✗"
        print(f"{status} {info}")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, result in results.items():
        status = "✓" if result["success"] else "✗"
        print(f"{status} {name}: {result['info'][:60]}")
    
    # Save results
    with open("gpu_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to gpu_test_results.json")

if __name__ == "__main__":
    main()
