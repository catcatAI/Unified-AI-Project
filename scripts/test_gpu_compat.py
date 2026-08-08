"""
GPU Compatibility Test — Multiple approaches to bypass torch
Tests: pyopencl, wgpu (Vulkan/DX12), kompute, subprocess torch
"""
import subprocess
import sys
import os
import time

def test_wgpu():
    """Test wgpu (WebGPU via Vulkan/DX12)"""
    try:
        import wgpu
        import wgpu.backends.wgpu_native  # or wgpu.backends.dx12
        # Request adapter
        adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
        if adapter:
            device = adapter.request_device()
            return True, f"wgpu device: {device}"
        return False, "No wgpu adapter"
    except ImportError:
        return False, "wgpu not installed"
    except Exception as e:
        return False, str(e)

def test_kompute():
    """Test kompute (Vulkan compute)"""
    try:
        import kp
        mgr = kp.Manager()
        return True, f"kompute manager created, devices: {len(mgr.devices)}"
    except ImportError:
        return False, "kompute not installed"
    except Exception as e:
        return False, str(e)

def test_torch_subprocess():
    """Test torch in subprocess with timeout"""
    script = '''
import sys
print("Starting torch import...", flush=True)
try:
    import torch
    print(f"torch {torch.__version__} imported", flush=True)
    print(f"CUDA: {torch.cuda.is_available()}", flush=True)
    if torch.cuda.is_available():
        dev = torch.cuda.get_device_name(0)
        print(f"GPU: {dev}", flush=True)
    # Quick CPU test
    x = torch.randn(100, 100)
    y = torch.mm(x, x.t())
    print(f"Matrix multiply: {y.shape}", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    sys.exit(1)
'''
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr[:300]
    except subprocess.TimeoutExpired:
        return False, "20s timeout"
    except Exception as e:
        return False, str(e)

def test_numpy_gpu():
    """Test if numpy can use any GPU acceleration"""
    try:
        import numpy as np
        # Check if numpy was built with GPU support
        config = np.__config__
        has_blas = hasattr(config, 'blas_opt_info')
        has_lapack = hasattr(config, 'lapack_opt_info')
        return True, f"numpy {np.__version__}, BLAS: {has_blas}, LAPACK: {has_lapack}"
    except Exception as e:
        return False, str(e)

def check_available_packages():
    """Check what GPU-related packages are available"""
    packages = [
        "pyopencl", "wgpu", "kompute", "pycuda", "scikit-cuda",
        "cupy", "jax", "torch", "tensorflow", "onnxruntime",
        "vulkan", "pyvulkan", "moderngl", "vispy",
    ]
    available = []
    unavailable = []
    for pkg in packages:
        try:
            __import__(pkg)
            available.append(pkg)
        except ImportError:
            unavailable.append(pkg)
    return available, unavailable

def main():
    print("=" * 60)
    print("GPU Compatibility Test — Bypassing torch import hang")
    print("=" * 60)
    
    # Check available packages
    print("\n--- Available GPU Packages ---")
    available, unavailable = check_available_packages()
    print(f"Available: {', '.join(available) if available else 'none'}")
    print(f"Missing: {', '.join(unavailable)}")
    
    # Run tests
    tests = [
        ("wgpu (Vulkan/DX12)", test_wgpu),
        ("kompute (Vulkan)", test_kompute),
        ("torch (subprocess 20s)", test_torch_subprocess),
        ("numpy GPU support", test_numpy_gpu),
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        success, info = test_func()
        results[name] = {"success": success, "info": info}
        status = "✓" if success else "✗"
        print(f"{status} {info}")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if results.get("wgpu (Vulkan/DX12)", {}).get("success"):
        print("1. USE wgpu: Best option for GPU compute on this system")
        print("   Install: pip install wgpu[all]")
        print("   API: WebGPU standard, works with Vulkan/DX12/Metal")
    elif results.get("kompute (Vulkan)", {}).get("success"):
        print("1. USE kompute: Vulkan compute wrapper")
        print("   Install: pip install kompute")
        print("   API: Simple tensor operations via Vulkan")
    else:
        print("1. Install GPU packages first:")
        print("   pip install wgpu[all]  # For Vulkan/DX12")
        print("   pip install pyopencl    # For OpenCL (needs ICD)")
    
    if results.get("torch (subprocess 20s)", {}).get("success"):
        print("2. torch works in subprocess — use multiprocessing")
    else:
        print("2. torch blocked — focus on numpy or wgpu backend")
    
    print("\n3. For SNN training:")
    print("   - Small models (<1000 neurons): numpy is fine")
    print("   - Medium models (1K-10K neurons): use wgpu/kompute")
    print("   - Large models (>10K neurons): need proper GPU backend")

if __name__ == "__main__":
    main()
