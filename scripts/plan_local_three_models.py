#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Plan three local models that actually fit this machine.

Three roles on one box is a VRAM budget problem, not a shopping problem: every
server keeps its weights resident, so the trio must fit *together* (plus KV
cache), not one at a time.

The catalog is deliberately small and Q4-only — Q8 at these sizes buys quality
you cannot measure on a 2-3B model and costs the VRAM that a third role needs.

Usage:
    python scripts/plan_local_three_models.py            # detect hardware, plan
    python scripts/plan_local_three_models.py --json     # machine-readable
    python scripts/plan_local_three_models.py --vram 8 --ram 7
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

LLAMA_DIR = Path.home() / "llama.cpp" / "build" / "bin"
SERVER_BIN = LLAMA_DIR / "llama-server"
MODELS_DIR = Path.home() / "models" / "gguf"


def detect_vram_gb() -> Optional[float]:
    """VRAM in GB from sysfs (Intel/AMD) or nvidia-smi; None when unknown."""
    for card in sorted(Path("/sys/class/drm").glob("card*/device/mem_info_vram_total")):
        try:
            total = int(card.read_text().strip())
            if total > 0:
                return round(total / 1024**3, 2)
        except (OSError, ValueError):
            continue
    if shutil.which("clinfo"):
        # Intel/AMD integrated and discrete GPUs expose no sysfs vram_total.
        try:
            out = subprocess.run(
                ["clinfo"], capture_output=True, text=True, timeout=10, check=False
            )
            sizes = [
                int(line.split()[-2])
                for line in out.stdout.splitlines()
                if "Global memory size" in line and line.split()[-2].isdigit()
            ]
            if sizes:
                return round(max(sizes) / 1024**3, 2)
        except (subprocess.SubprocessError, ValueError):
            pass
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            first = out.stdout.strip().splitlines()[0]
            return round(float(first) / 1024, 2)
        except (subprocess.SubprocessError, ValueError, IndexError):
            return None
    return None


def detect_ram_gb() -> Optional[float]:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return round(int(line.split()[1]) / 1024**2, 2)
    except OSError:
        pass
    return None


@dataclass(frozen=True)
class ModelSpec:
    key: str
    family: str
    label: str
    params_b: float
    weights_gb: float
    kv_gb_per_2k: float
    repo: str
    filename: str

    def footprint_gb(self, ctx: int = 2048) -> float:
        """Weights + KV cache + ~0.35 GB runtime overhead per server."""
        return round(self.weights_gb + self.kv_gb_per_2k * (ctx / 2048) + 0.35, 2)


CATALOG: Tuple[ModelSpec, ...] = (
    ModelSpec(
        "qwen2.5-0.5b",
        "qwen",
        "Qwen2.5-0.5B-Instruct Q4",
        0.5,
        0.40,
        0.08,
        "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        "qwen2.5-0.5b-instruct-q4_k_m.gguf",
    ),
    ModelSpec(
        "llama-3.2-1b",
        "llama",
        "Llama-3.2-1B-Instruct Q4",
        1.2,
        0.85,
        0.12,
        "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
    ),
    ModelSpec(
        "qwen2.5-1.5b",
        "qwen",
        "Qwen2.5-1.5B-Instruct Q4",
        1.5,
        1.10,
        0.16,
        "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        "qwen2.5-1.5b-instruct-q4_k_m.gguf",
    ),
    ModelSpec(
        "gemma-2-2b",
        "gemma",
        "Gemma-2-2B-IT Q4",
        2.6,
        1.80,
        0.22,
        "bartowski/gemma-2-2b-it-GGUF",
        "gemma-2-2b-it-Q4_K_M.gguf",
    ),
    ModelSpec(
        "qwen2.5-3b",
        "qwen",
        "Qwen2.5-3B-Instruct Q4",
        3.1,
        2.00,
        0.30,
        "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "qwen2.5-3b-instruct-q4_k_m.gguf",
    ),
    ModelSpec(
        "phi-3-mini",
        "phi",
        "Phi-3-mini-4k Q4",
        3.8,
        2.40,
        0.34,
        "microsoft/Phi-3-mini-4k-instruct-gguf",
        "Phi-3-mini-4k-instruct-q4.gguf",
    ),
)

# The three stage slots the backend already knows about, in role order.
SLOTS = (
    {"slot": "llamacpp-local", "role": "main", "port": 8080},
    {"slot": "llamacpp-gemma", "role": "role_b", "port": 8082},
    {"slot": "llamacpp-qwen", "role": "role_c", "port": 8081},
)


@dataclass
class Plan:
    mode: str
    budget_gb: float
    ctx: int
    picks: List[Tuple[Dict[str, object], ModelSpec]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def total_gb(self) -> float:
        return round(sum(model.footprint_gb(self.ctx) for _, model in self.picks), 2)

    def commands(self, threads: int = 6) -> List[str]:
        cmds = []
        for placement, model in self.picks:
            path = MODELS_DIR / model.filename
            cmds.append(
                " ".join(
                    [
                        str(SERVER_BIN),
                        f"-m {path}",
                        f"--host 127.0.0.1 --port {placement['port']}",
                        "-ngl 99",
                        f"-c {self.ctx}",
                        f"-t {threads}",
                        "--no-webui",
                    ]
                )
            )
        return cmds

    def to_dict(self) -> Dict[str, object]:
        return {
            "mode": self.mode,
            "budget_gb": self.budget_gb,
            "ctx": self.ctx,
            "total_gb": self.total_gb,
            "picks": [
                {
                    "slot": placement["slot"],
                    "role": placement["role"],
                    "port": placement["port"],
                    "model": model.key,
                    "label": model.label,
                    "footprint_gb": model.footprint_gb(self.ctx),
                    "path": str(MODELS_DIR / model.filename),
                }
                for placement, model in self.picks
            ],
            "commands": self.commands(),
            "notes": self.notes,
            "missing": self.missing,
        }


def _rank(picks: Sequence[ModelSpec]) -> Tuple[int, float, float]:
    """Rank a trio: distinct families, then the weakest link, then total size.

    The weakest-link term matters: a trio of two good models plus a 0.5B is
    worse on stage than three similar-sized ones, even at equal total params.
    """
    families = len({m.family for m in picks})
    weakest = min(m.params_b for m in picks)
    return families, weakest, sum(m.params_b for m in picks)


def display_attached() -> bool:
    """A desktop session shares the GPU VRAM with the compositor and the browser.

    The stage itself is a WebGL/canvas page, so running three servers at 85% of
    VRAM starves the window that is supposed to show them.
    """
    return bool(os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"))


def plan_three(
    vram_gb: Optional[float],
    ram_gb: Optional[float],
    ctx: int = 2048,
    headroom: Optional[float] = None,
    has_display: Optional[bool] = None,
) -> Plan:
    """Pick the strongest trio that fits; degrade to on-demand when nothing does."""
    if headroom is None:
        headroom = 0.30 if (display_attached() if has_display is None else has_display) else 0.15
    if vram_gb is not None and vram_gb > 0:
        budget = round(vram_gb * (1.0 - headroom), 2)
        mode = "gpu"
    elif ram_gb is not None and ram_gb > 0:
        # CPU-only: leave much more room — the OS, browser and backend live here.
        budget = round(ram_gb * 0.6, 2)
        mode = "cpu"
    else:
        budget = 3.0
        mode = "cpu"
        return _smallest_plan(budget, ctx, ["No VRAM/RAM detected; assuming 3 GB."], mode)

    best: Optional[Sequence[ModelSpec]] = None
    for i in range(len(CATALOG)):
        for j in range(i + 1, len(CATALOG)):
            for k in range(j + 1, len(CATALOG)):
                trio = (CATALOG[i], CATALOG[j], CATALOG[k])
                if sum(m.footprint_gb(ctx) for m in trio) <= budget:
                    if best is None or _rank(trio) > _rank(best):
                        best = trio
    if best is None:
        return _smallest_plan(
            budget,
            ctx,
            [f"Even the smallest trio does not fit {budget} GB at ctx={ctx}."],
            mode,
        )

    ordered = _order_by_strength(best)
    notes = [f"Budget {budget} GB ({mode}, ctx={ctx}, {int(headroom * 100)}% headroom)."]
    if ram_gb is not None and ram_gb < 8:
        notes.append(
            f"System RAM available is {ram_gb} GB — run the servers with `-ngl 99` "
            "so weights stay in VRAM, not in page cache."
        )
    return Plan(mode=mode, budget_gb=budget, ctx=ctx, picks=list(zip(SLOTS, ordered)), notes=notes)


def _order_by_strength(models: Sequence[ModelSpec]) -> List[ModelSpec]:
    """Strongest model on `main`, then the two others for role_b / role_c."""
    return sorted(models, key=lambda m: m.params_b, reverse=True)


def _smallest_plan(budget: float, ctx: int, notes: List[str], mode: str = "on_demand") -> Plan:
    trio = sorted(CATALOG, key=lambda m: m.footprint_gb(ctx))[:3]
    plan = Plan(mode="on_demand", budget_gb=budget, ctx=ctx, picks=list(zip(SLOTS, trio)))
    plan.notes = notes + [
        "Plan B: run them one at a time (llama-server has no built-in model swap).",
        "Ctrl-C one server before starting the next; roles fall back to the active backend.",
    ]
    plan.mode = "on_demand"
    return plan


def check_files(plan: Plan) -> List[str]:
    missing = [str(MODELS_DIR / model.filename) for _, model in plan.picks]
    return [path for path in missing if not Path(path).exists()]


def render(plan: Plan) -> str:
    lines = [
        f"mode      : {plan.mode}",
        f"budget    : {plan.budget_gb} GB (ctx={plan.ctx})",
        f"planned   : {plan.total_gb} GB total",
        "",
        f"{'role':8} {'slot':16} {'port':5} {'model':22} {'GB':>5}",
    ]
    for placement, model in plan.picks:
        lines.append(
            f"{placement['role']:8} {placement['slot']:16} {placement['port']:5} "
            f"{model.label:22} {model.footprint_gb(plan.ctx):5.2f}"
        )
    lines.append("")
    if plan.notes:
        lines.extend(f"note: {note}" for note in plan.notes)
        lines.append("")
    if plan.missing:
        lines.append("missing model files:")
        lines.extend(f"  - {path}" for path in plan.missing)
        lines.append("")
        lines.append("download (one example):")
        lines.append(
            f"  huggingface-cli download {plan.picks[0][1].repo} --include '*Q4*' --local-dir {MODELS_DIR}"
        )
        lines.append("")
    lines.append("start commands:")
    lines.extend(f"  {cmd}" for cmd in plan.commands())
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vram", type=float, default=None, help="VRAM in GB (default: detect)")
    parser.add_argument(
        "--ram", type=float, default=None, help="available RAM in GB (default: detect)"
    )
    parser.add_argument("--ctx", type=int, default=2048)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    vram = args.vram if args.vram is not None else detect_vram_gb()
    ram = args.ram if args.ram is not None else detect_ram_gb()
    plan = plan_three(vram, ram, ctx=args.ctx)
    plan.missing = check_files(plan)

    if args.json:
        payload = plan.to_dict()
        payload["vram_gb"] = vram
        payload["ram_gb"] = ram
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"vram      : {vram} GB")
        print(f"ram free  : {ram} GB")
        print(render(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
