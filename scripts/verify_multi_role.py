#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Multi-role end-to-end verification (Phase 5) — no network, no LLM.

Checks the contract a user actually depends on:

  1. roles load from config, with the slots the plan names
  2. an unknown role is rejected, not silently answered as Angela
  3. a role's persona block overrides Angela explicitly
  4. memory namespaces are a hard partition (write A, read B -> empty)
  5. the router resolves each role's backend slot to a registered backend
  6. the /roles catalogue route is registered
  7. /chat/group and /chat/unified accept role_ids (route table)

Exit code 0 only when every check passes. `--json` for machine output.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))


class Report:
    def __init__(self) -> None:
        self.checks = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))

    @property
    def ok(self) -> bool:
        return all(c["ok"] for c in self.checks)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "checks": self.checks}


def verify_roles(report: Report) -> None:
    from ai.roleplay.runtime import load_roles, resolve_role

    roles = load_roles()
    ids = [r.role_id for r in roles]
    report.check("roles load", ids == ["main", "role_b", "role_c", "role_d"], str(ids))
    slots = {r.role_id: r.backend_slot for r in roles}
    report.check(
        "role_b -> gemma, role_c -> qwen, role_d -> deepseek",
        slots.get("role_b") == "llamacpp-gemma"
        and slots.get("role_c") == "llamacpp-qwen"
        and slots.get("role_d") == "deepseek",
        str(slots),
    )
    report.check("unknown role resolves to None", resolve_role("nobody") is None)


def verify_persona(report: Report) -> None:
    from ai.roleplay.runtime import build_role_persona, load_roles

    role = next(r for r in load_roles() if r.role_id == "role_b")
    block = build_role_persona(role)
    report.check(
        "persona names the role and forbids Angela",
        "Gemma 角色" in block and "不要自稱 Angela" in block and "優先" in block,
    )


def verify_memory(report: Report) -> None:
    import asyncio

    from ai.memory.vector_store import VectorMemoryStore

    async def run(tmp: str) -> None:
        store = VectorMemoryStore(persist_directory=tmp)
        await store.add_memory("a1", "secret of role a", None, namespace="role_a")
        await store.add_memory("b1", "secret of role b", None, namespace="role_b")
        a = await store.semantic_search("secret", 5, None, "role_a")
        b = await store.semantic_search("secret", 5, None, "role_b")
        cross = await store.semantic_search("secret", 5, None, "role_c")
        # numpy returns {} for "no rows"; chroma returns {"ids": [[]], ...}.
        # Callers read .get(...)[0], so both are "no hits" — assert semantics,
        # not the empty shape.
        cross_ids = (cross.get("ids") or [[]])[0]
        report.check("namespace isolates reads", a["ids"][0] == ["a1"], str(a["ids"][0]))
        report.check("other namespace sees its own row", b["ids"][0] == ["b1"], str(b["ids"][0]))
        report.check(
            "empty namespace returns no hits", not cross_ids, f"backend={store.backend_type}"
        )

    with tempfile.TemporaryDirectory() as tmp:
        asyncio.run(run(tmp))


def verify_router(report: Report) -> None:
    from services.llm.providers.registry import LLMBackend
    from services.llm.router import AngelaLLMService

    class Fake:
        def __init__(self, name: str) -> None:
            self.name = name

    router = object.__new__(AngelaLLMService)
    router.backends = {
        LLMBackend.LLAMA_CPP: Fake("cpp"),
        LLMBackend.LLAMA_CPP_GEMMA: Fake("gemma"),
        LLMBackend.LLAMA_CPP_QWEN: Fake("qwen"),
        LLMBackend.DEEPSEEK: Fake("deepseek"),
    }
    cases = {
        "llamacpp-gemma": "gemma",
        "llamacpp-qwen": "qwen",
        "deepseek": "deepseek",
    }
    for slot, expected in cases.items():
        backend, _ = router._resolve_forced_backend(slot)
        report.check(f"slot {slot} -> {expected}", getattr(backend, "name", None) == expected)
    unknown, _ = router._resolve_forced_backend("gone")
    report.check("unknown slot falls back (None)", unknown is None)


def verify_routes(report: Report) -> None:
    from api.routes.chat_routes import router as chat_router
    from api.routes.role_routes import router as role_router

    chat_paths = {route.path for route in chat_router.routes}
    role_paths = {route.path for route in role_router.routes}
    report.check("/chat/group registered", "/chat/group" in chat_paths)
    report.check("/chat/unified registered", "/chat/unified" in chat_paths)
    report.check("/roles catalogue registered", "/roles" in role_paths)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = Report()
    for step in (verify_roles, verify_persona, verify_memory, verify_router, verify_routes):
        try:
            step(report)
        except Exception as exc:  # noqa: BLE001 - a broken import is a failed check
            report.check(step.__name__, False, f"raised: {exc}")

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    print(f"\n{sum(c['ok'] for c in report.checks)}/{len(report.checks)} checks passed")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
