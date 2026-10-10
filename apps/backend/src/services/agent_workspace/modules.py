# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""Agent config modules — puzzle pieces for composing agents without hand-writing.

Main-AI-can't-hand-write insight (2026-10-10): the main AI will never author
adapter code, and engineers shouldn't re-write per-app configs either. So
capabilities ship as MODULES (action subsets + presets + prompts + policy on
top of the shell/files primitives — no new exec surface), and the composer
assembles them into a working adapter by id list. Adding app support =
registering ONE module once, reused everywhere.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.agent_workspace.agent import FilesAdapter, ShellAdapter
from services.agent_workspace.app_session import ActionSpec, AppAdapter

logger = logging.getLogger(__name__)


class ConfigModule:
    """One composable capability piece."""

    def __init__(
        self,
        module_id: str,
        label: str,
        base: str,
        actions: Optional[List[str]] = None,
        presets: Optional[Dict[str, Any]] = None,
        prompt: str = "",
        triggers: Optional[List[str]] = None,
    ) -> None:
        self.module_id = module_id
        self.label = label
        self.base = base  # shell | files
        self.actions = actions or []
        self.presets = presets or {}
        self.prompt = prompt
        self.triggers = [t.lower() for t in (triggers or [])]

    def build_base(self) -> AppAdapter:
        """Instantiate the underlying primitive adapter with presets."""
        if self.base == "shell":
            return ShellAdapter(workdir=self.presets.get("workdir"))
        return FilesAdapter()


MODULE_REGISTRY: Dict[str, ConfigModule] = {}


def register_module(module: ConfigModule) -> None:
    """Register one module (engineers add support here, once per app)."""
    MODULE_REGISTRY[module.module_id] = module


register_module(
    ConfigModule(
        module_id="shell-exec",
        label="命令執行",
        base="shell",
        actions=["run"],
        presets={"timeout": 60},
        prompt="通用命令執行（需確認）。",
        triggers=["shell", "終端", "命令行", "命令", "執行", "運行"],
    )
)
register_module(
    ConfigModule(
        module_id="shell-unity",
        label="Unity批處理",
        base="shell",
        actions=["run"],
        presets={
            "timeout": 300,
            "unity_bin": "~/Unity/Hub/Editor/6000.6.5f1/Editor/Unity",
            "batch_flags": "-batchmode -nographics",
        },
        prompt="Unity無頭批處理（建專案/執行方法/編譯驗證），長超時。",
        triggers=["unity", "建模", "小車", "場景", "scene"],
    )
)
register_module(
    ConfigModule(
        module_id="shell-eda",
        label="EDA工具",
        base="shell",
        actions=["run"],
        presets={"timeout": 120, "tools": ["ngspice", "klayout", "magic", "kicad-cli"]},
        prompt="EDA工具鏈調用（仿真/版圖），需確認。",
        triggers=["eda", "ngspice", "klayout", "magic", "kicad", "仿真", "版圖", "gds"],
    )
)
register_module(
    ConfigModule(
        module_id="files-rw",
        label="文件讀寫",
        base="files",
        actions=["list", "read", "write"],
        presets={},
        prompt="完整文件操作（寫入需確認）。",
        triggers=["files", "文件", "檔案", "讀寫", "讀取", "寫入"],
    )
)
register_module(
    ConfigModule(
        module_id="files-ro",
        label="文件隻讀",
        base="files",
        actions=["list", "read"],
        presets={},
        prompt="隻讀文件操作（列目錄/讀檔，無寫入）。",
        triggers=["隻讀", "只读", "查看目錄", "列目錄", "chip"],
    )
)


class ComposedAdapter(AppAdapter):
    """An adapter assembled from modules (puzzle assembly, no hand-writing)."""

    def __init__(self, app_id: str, label: str, modules: List[ConfigModule]) -> None:
        super().__init__()
        self.app_id = app_id
        self.label = label
        self.module_ids = [m.module_id for m in modules]
        seen: Dict[str, str] = {}
        for module in modules:
            base = module.build_base()
            for action in module.actions:
                if action in seen:
                    raise ValueError(
                        f"action collision: {action} from {seen[action]} and {module.module_id}"
                    )
                seen[action] = module.module_id
                if not base.has(action):
                    raise ValueError(f"module {module.module_id} wants unknown action {action}")
                spec = next(s for s in base.specs() if s.name == action)

                async def _handler(
                    params: Dict[str, Any], _b: AppAdapter = base, _a: str = action
                ) -> Dict[str, Any]:
                    return await _b.run(_a, params)

                self.register(spec, _handler)

    async def read_state(self) -> Dict[str, Any]:
        """State summary lists composed modules (AI recognition)."""
        return {"app_id": self.app_id, "label": self.label, "modules": self.module_ids}


def suggest_modules(task_text: str) -> List[str]:
    """Deterministic task→module mapping (keyword triggers, longest wins per hit)."""
    lowered = (task_text or "").lower()
    hits: List[str] = []
    for module_id, module in MODULE_REGISTRY.items():
        if any(trigger and trigger in lowered for trigger in module.triggers):
            hits.append(module_id)
    # files-ro is subsumed by files-rw when both hit (superset wins).
    if "files-rw" in hits and "files-ro" in hits:
        hits.remove("files-ro")
    return hits


def compose_agent(app_id: str, module_ids: List[str], label: str = "") -> AppAdapter:
    """Assemble an adapter from module ids (raises on unknown/collision)."""
    modules: List[ConfigModule] = []
    for mid in module_ids:
        module = MODULE_REGISTRY.get(mid)
        if module is None:
            raise ValueError(f"unknown module: {mid} (available: {sorted(MODULE_REGISTRY)})")
        modules.append(module)
    if not modules:
        raise ValueError("no modules given")
    return ComposedAdapter(app_id, label or "+".join(m.module_id for m in modules), modules)
