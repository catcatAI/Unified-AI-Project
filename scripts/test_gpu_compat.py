"""
GPU Compatibility Test — Multiple approaches to bypass torch
Tests: pyopencl, wgpu (Vulkan/DX12), kompute, subprocess torch
"""

import os
import subprocess
import sys
import time


def check_wgpu():
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


def check_kompute():
    """Test kompute (Vulkan compute)"""
    try:
        import kp

        mgr = kp.Manager()
        return True, f"kompute manager created, devices: {len(mgr.devices)}"
    except ImportError:
        return False, "kompute not installed"
    except Exception as e:
        return False, str(e)


def check_torch_subprocess():
    """Test torch in subprocess with timeout"""
    script = """
import sys
print("Starting torch import...", flush=True)
try:
    import torch
    print(f"torch {torch.__version__} imported", flush=True)
    # "No CUDA" is not "no GPU": an Intel Arc answers through torch.xpu.
    print(f"CUDA: {torch.cuda.is_available()}", flush=True)
    print(f"XPU: {hasattr(torch, 'xpu') and torch.xpu.is_available()}", flush=True)
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        dev = "xpu"
        print(f"GPU: {torch.xpu.get_device_name(0)}", flush=True)
    elif torch.cuda.is_available():
        dev = "cuda"
        print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    else:
        dev = "cpu"
    x = torch.randn(100, 100, device=dev)
    y = torch.mm(x, x.t())
    print(f"Matrix multiply on {dev}: {y.shape}", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    sys.exit(1)
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr[:300]
    except subprocess.TimeoutExpired:
        return False, "20s timeout"
    except Exception as e:
        return False, str(e)


def check_numpy_gpu():
    """Test if numpy can use any GPU acceleration"""
    try:
        import numpy as np

        # Check if numpy was built with GPU support
        config = np.__config__
        has_blas = hasattr(config, "blas_opt_info")
        has_lapack = hasattr(config, "lapack_opt_info")
        return True, f"numpy {np.__version__}, BLAS: {has_blas}, LAPACK: {has_lapack}"
    except Exception as e:
        return False, str(e)


def check_available_packages():
    """Check what GPU-related packages are available"""
    packages = [
        "pyopencl",
        "wgpu",
        "kompute",
        "pycuda",
        "scikit-cuda",
        "cupy",
        "jax",
        "torch",
        "tensorflow",
        "onnxruntime",
        "vulkan",
        "pyvulkan",
        "moderngl",
        "vispy",
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
        ("wgpu (Vulkan/DX12)", check_wgpu),
        ("kompute (Vulkan)", check_kompute),
        ("torch (subprocess 20s)", check_torch_subprocess),
        ("numpy GPU support", check_numpy_gpu),
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
        print("1. wgpu is available (optional): WebGPU via Vulkan/DX12")
    elif results.get("kompute (Vulkan)", {}).get("success"):
        print("1. kompute is available (optional): Vulkan compute wrapper")
    else:
        print("1. No wgpu/kompute backend — that is fine: this project does not use them.")

    if results.get("torch (subprocess 20s)", {}).get("success"):
        print("2. torch works (xpu > cuda > cpu) — this is the backend token-SNN uses")
        print("   (scripts/train_token_snn.py --device auto)")
    else:
        print("2. torch blocked — SNN falls back to the numpy backend")

    print("\n3. For SNN training:")
    print("   - token-SNN: torch on the resolved device (xpu/cuda when available)")
    print("   - GARDEN TensorSNNCore: CPU by default — its sparse per-sample")
    print("     Hebbian updates measured slower on an Intel Arc XPU than on the CPU")


if __name__ == "__main__":
    main()
