#!/usr/bin/env bash
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
# Run a command against the local Intel Arc (B570) XPU stack.
#
# The runtime under .xpu_runtime/root is a self-contained extract of:
#   - libze_intel_gpu 26.27 (Debian sid) — matches torch 2.14.1+xpu kernels
#     (the Ubuntu/Intel 25.18 build decodes only zebin minor <= 39, torch
#     ships minor 70),
#   - libze_loader 1.32 (1.17 broke device property queries -> segfault),
#   - libigc/libigdfcl 2.40.14 (+ bundled libopencl-clang.so.16),
#   - libstdc++6 16.2, libigdgmm 22.10 (driver 26.27 dependencies).
# libigc's single GLIBC_2.43 verneed (sqrtf) is patched to the GLIBC_2.2.5
# node — noble ships glibc 2.39; see .xpu_runtime/shim.c for the fallback.
#
# NEOReadDebugKeys/OverrideCsrAllocationSize are deliberately NOT set. They
# used to be (B570's capability table reports requiredPreemptionSurfaceSize=0,
# which aborts CSR creation in command_stream_receiver.cpp; 64K overrides it),
# but 2026-10-29 bisection showed they are the fault trigger on this stack:
#   control (neither) 0/3 clean | CSR pair alone 2/3 faulted | this wrapper
#   (CSR pair + everything below) 3/3 faulted, 173/1810/4057 xe CAT errors
#   -> UR_DEVICE_LOST mid-training, protocol: token vocab d512/L192/limit 500.
# Device init and CSR creation both succeed without them on libze 26.27.
#
# Usage: scripts/xpu_run.sh <command> [args...]
#   e.g. scripts/xpu_run.sh ./.venv/bin/python scripts/train_token_snn.py ...
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZE="$REPO_ROOT/.xpu_runtime/root/usr/lib/x86_64-linux-gnu"
export LD_LIBRARY_PATH="$ZE:$ZE/intel-opencl${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# Intel OpenCL ICD (igdrcl 26.27, matches libze 26.27): oneDNN routes large
# GEMMs through an OpenCL device query and hard-fails without it
# ("OpenCL device not found" -> "could not create a primitive"). The ICD
# entry lives in the private root so the system /etc stays untouched.
export OCL_ICD_VENDORS="$REPO_ROOT/.xpu_runtime/root/etc/OpenCL/vendors"
# Level-Zero-v2 opt-out: sustained-load ccs resets + UR_DEVICE_LOST are a
# known 26.27 failure family; a 20-min soak ran clean with v2 off
# (riceharvest/awesome-b70 bug table, upstream llama.cpp #27595/#27198).
export SYCL_UR_USE_LEVEL_ZERO_V2=0
export UR_LOADER_USE_LEVEL_ZERO_V2=0
exec "$@"
