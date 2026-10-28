#!/usr/bin/env bash
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
# Clean-boot probe protocol for the Arc B570 ccs "Engine memory CAT error" /
# UR_RESULT_ERROR_DEVICE_LOST family.
#
# Why this exists: a single crash wedges the card for minutes, so experiments
# run after a crash measure the wreckage, not the stack. Run this immediately
# after a reboot, before any other XPU workload, to get an uncontaminated
# baseline. Observed on 2026-10-28 (kernel 7.0.0-38, xe 1.1.0, GuC 70.72.1,
# compute-runtime 26.27 via .xpu_runtime):
#   * queue depth, not load, is the leading suspect — 4096^2 matmul at ~100%
#     utilisation survived 60 s with torch.xpu.synchronize() every step, while
#     one sync every 5 s (unbounded in-flight queue) died within seconds;
#   * training-shaped loops (TransformerEncoder fwd/bwd/AdamW) still died
#     within 1.7-3.0 s on a device already degraded by earlier crashes, with
#     both ccs and bcs engine resets — so every stage here waits for a quiet
#     device and reports kernel events per stage.
#
# Usage:
#   scripts/xpu_probe.sh                 # safe stages only
#   scripts/xpu_probe.sh --with-crash    # adds the known-bad unbounded-queue
#                                        # stage LAST (it wedges the card)
#   scripts/xpu_probe.sh --skip-baseline # skip the tiny smoke test
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1
PY="$REPO_ROOT/.venv/bin/python"
RUN="$REPO_ROOT/scripts/xpu_run.sh"
WORKDIR="$(mktemp -d /tmp/xpu_probe.XXXXXX)"
WITH_CRASH=0
SKIP_BASELINE=0
for arg in "$@"; do
  case "$arg" in
    --with-crash) WITH_CRASH=1 ;;
    --skip-baseline) SKIP_BASELINE=1 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

# Per-stage kernel-event tally: journal is the ground truth, not the exit code.
events() {
  journalctl -k --since "$1" --no-pager 2>/dev/null |
    grep -oE "Engine memory CAT error|Timedout job|Engine reset: engine_class=[a-z]+|exec queue reset detected" |
    sort | uniq -c | tr '\n' ' ' | sed 's/  */ /g'
}

stage() {
  local name="$1" timeout_s="$2" since="$3"
  shift 3
  local out="$WORKDIR/$name.log"
  echo
  echo "=== stage: $name (timeout ${timeout_s}s) ==="
  timeout "$timeout_s" "$RUN" "$PY" "$@" >"$out" 2>&1
  local rc=$?
  grep -E "PASS|FAIL|setup ok|^t=" "$out" | tail -6
  if grep -qE "PASS" "$out"; then
    echo "[$name] RESULT: PASS (rc=$rc)"
  else
    echo "[$name] RESULT: FAIL (rc=$rc)"
  fi
  echo "[$name] kernel events: $(events "$since")"
}

# The probe payloads live next to the probe: /tmp does not survive a reboot,
# so they are generated here on first run.
BASELINE="$WORKDIR/baseline.py"
MATMUL="$WORKDIR/matmul_queue.py"
TRAIN="$WORKDIR/train_churn.py"
CRASH="$WORKDIR/crash_queue.py"

cat >"$BASELINE" <<'PY'
import torch
x = torch.randn(256, 256, device="xpu"); w = torch.randn(256, 256, device="xpu")
for _ in range(20):
    y = x @ w
torch.xpu.synchronize()
print("BASELINE PASS", float(y.sum()))
PY

# Bounded queue: one sync per step (the mitigation under test).
cat >"$MATMUL" <<'PY'
import sys, time, torch
torch.manual_seed(0)
SECONDS = float(sys.argv[1])
x = torch.randn(4096, 4096, device="xpu"); w = torch.randn(4096, 4096, device="xpu")
y = torch.empty(4096, 4096, device="xpu")
torch.xpu.synchronize()
t0 = time.time(); step = 0
while time.time() - t0 < SECONDS:
    torch.matmul(x, w, out=y)
    torch.xpu.synchronize()
    step += 1
    if step % 250 == 0:
        print(f"t={time.time()-t0:6.1f}s steps={step}", flush=True)
print(f"MATMUL PASS: {step} steps in {time.time()-t0:.1f}s ({step/(time.time()-t0):.1f} it/s)")
PY

cat >"$TRAIN" <<'PY'
import sys, time, torch
torch.manual_seed(0)
SECONDS = float(sys.argv[1])
SET_NONE = len(sys.argv) > 2 and sys.argv[2] == "churn"
model = torch.nn.TransformerEncoder(
    torch.nn.TransformerEncoderLayer(d_model=512, nhead=8, batch_first=True), num_layers=4
).to("xpu")
opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
x = torch.randn(64, 64, 512, device="xpu"); y = torch.randn(64, 64, 512, device="xpu")
torch.xpu.synchronize()
t0 = time.time(); step = 0; last = t0
while time.time() - t0 < SECONDS:
    loss = torch.nn.functional.mse_loss(model(x), y)
    opt.zero_grad(set_to_none=SET_NONE)
    loss.backward(); opt.step()
    torch.xpu.synchronize()
    step += 1
    now = time.time()
    if now - last >= 10.0:
        print(f"t={now-t0:6.1f}s steps={step} loss={loss.item():.4f}", flush=True)
        last = now
print(f"TRAIN PASS: {step} steps in {time.time()-t0:.1f}s")
PY

# Known-bad: no sync inside the loop, so the in-flight queue grows without
# bound. Expected to die; run last because it wedges the card.
cat >"$CRASH" <<'PY'
import time, torch
torch.manual_seed(0)
x = torch.randn(4096, 4096, device="xpu"); w = torch.randn(4096, 4096, device="xpu")
y = torch.empty(4096, 4096, device="xpu")
torch.xpu.synchronize()
t0 = time.time(); step = 0
while time.time() - t0 < 30:
    torch.matmul(x, w, out=y)
    step += 1
    if step % 100 == 0:
        torch.xpu.synchronize()
        print(f"t={time.time()-t0:5.1f}s steps={step}", flush=True)
print(f"CRASH-QUEUE SURVIVED: {step} steps")
PY

echo "=== xpu_probe: clean-boot protocol ==="
echo "kernel: $(uname -r)  time: $(date '+%F %T')"
journalctl -k -b --no-pager 2>/dev/null | grep -E "Using (GuC|HuC) firmware" | sed 's/.*drm\] //' | sort -u
echo "log dir: $WORKDIR"
SINCE="$(date '+%Y-%m-%d %H:%M:%S')"

if [ "$SKIP_BASELINE" -eq 0 ]; then
  stage baseline 60 "$SINCE" "$BASELINE"
fi

# The realistic workload first: this is the thing that has to work.
SINCE="$(date '+%Y-%m-%d %H:%M:%S')"
stage train_churn 180 "$SINCE" "$TRAIN" 180 churn

SINCE="$(date '+%Y-%m-%d %H:%M:%S')"
stage train_reuse 180 "$SINCE" "$TRAIN" 180

SINCE="$(date '+%Y-%m-%d %H:%M:%S')"
stage matmul_bounded 150 "$SINCE" "$MATMUL" 120

if [ "$WITH_CRASH" -eq 1 ]; then
  echo
  echo "waiting 90 s so the card is quiet before the deliberate crash stage..."
  sleep 90
  SINCE="$(date '+%Y-%m-%d %H:%M:%S')"
  stage crash_queue 90 "$SINCE" "$CRASH"
fi

echo
echo "=== boot totals ==="
journalctl -k -b --no-pager 2>/dev/null |
  grep -oE "Engine memory CAT error|Timedout job|Engine reset: engine_class=[a-z]+|exec queue reset detected" |
  sort | uniq -c
echo "logs: $WORKDIR"