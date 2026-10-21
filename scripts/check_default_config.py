#!/usr/bin/env python3
"""設定衛生門禁 — 提交的配置必須等於預設。

**為什麼有這個門禁**：設定分三層（`core/system/config/tiered_loader.py`）：
`*.default.yaml`（預設，該被提交）→ `*.user.yaml`（**執行期狀態**，Desktop
Settings API 會寫它）→ `*.evolved.yaml`（專案自己的演進層，該被提交）。
把 `*.user.yaml` 提交上去，等於把某台機器的非預設部署（例如
`deployment.mode: local+llm` 把雲端供應商重新打開） shipping 給所有人——
這是錯的行為，不是風格問題。

本門禁檢查三件事（任一不過 → exit 1）：

1. **沒有被追蹤的 user 層**：``git ls-files`` 不得出現任何 ``*.user.yaml``。
2. **沒有金鑰**：被追蹤的檔案不得含看起來像 API key 的常值（``api_key:`` 的
   非環境變數參照、以及 ``sk-``／``AIza``／``gsk_`` 之類的前綴）。
3. **evolved 層不得改部署模式**：`deployment.mode` 決定雲端是否連線，那是人的
   決定；專案自己的演進層只能調內容，不能打開雲端。

用法：
    python scripts/check_default_config.py            # 門禁模式
    python scripts/check_default_config.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS_ROOT = REPO_ROOT / "apps" / "backend" / "configs"

# The user layer is runtime state and must never be tracked.
USER_LAYER_GLOB = "*.user.yaml"

# The key prefixes that must never appear as a literal in a tracked file.
KEY_LITERAL_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"\bsk-[A-Za-z0-9_\-]{16,}", "openai-style key"),
    (r"\bAIza[0-9A-Za-z_\-]{20,}", "google api key"),
    (r"\bgsk_[A-Za-z0-9]{16,}", "groq-style key"),
    (r"\bAKIA[0-9A-Z]{12,}", "aws access key id"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
)

# `api_key: <value>` — allowed only when the value is an env reference.
API_KEY_LINE = re.compile(r"^\s*api_key\s*:\s*(?P<value>.+?)\s*$", re.MULTILINE)
ENV_REFERENCE = re.compile(r"^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$|^[A-Z][A-Z0-9_]{2,}$")


def _run_git(*args: str) -> List[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _tracked_files() -> List[str]:
    return _run_git("ls-files")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _load_yaml(path: Path) -> Optional[dict]:
    text = _read_text(path).strip()
    if not text:
        return None
    try:
        import yaml

        data = yaml.safe_load(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _check_user_layers(tracked: List[str]) -> List[str]:
    """The user layer must never be tracked."""
    return [f for f in tracked if Path(f).name.endswith(".user.yaml")]


def _check_key_literals(tracked: List[str]) -> List[str]:
    """No API key literal in a tracked file."""
    violations: List[str] = []
    for rel in tracked:
        if not rel.endswith((".yaml", ".yml", ".json", ".env", ".example", ".toml")):
            continue
        if rel.endswith(".env.example") or rel.endswith(".example"):
            # The .example files document the *names* of the env vars.
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        text = _read_text(path)
        if not text:
            continue
        for pattern, label in KEY_LITERAL_PATTERNS:
            if re.search(pattern, text):
                violations.append(f"{rel}: looks like a {label}")
        for match in API_KEY_LINE.finditer(text):
            value = match.group("value").split("#", 1)[0].strip().strip("\"'")
            if not value or ENV_REFERENCE.match(value) or "PLACEHOLDER" in value.upper():
                continue
            violations.append(f"{rel}: api_key literal {value[:12]}… (use api_key_env)")
    return violations


def _check_deployment_mode() -> List[str]:
    """The evolved layer may not open the cloud."""
    violations: List[str] = []
    default = _load_yaml(CONFIGS_ROOT / "system" / "llm.default.yaml") or {}
    evolved = _load_yaml(CONFIGS_ROOT / "system" / "llm.evolved.yaml") or {}
    default_mode = ((default.get("deployment") or {}).get("mode")) or "local"
    evolved_mode = (evolved.get("deployment") or {}).get("mode")
    if evolved_mode and evolved_mode != default_mode:
        violations.append(
            f"llm.evolved.yaml changes deployment.mode {default_mode} → {evolved_mode} "
            "(cloud access is a human decision, not the evolved layer's)"
        )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", help="write the verdict as JSON")
    args = parser.parse_args()

    tracked = _tracked_files()
    violations: List[str] = []
    user_layers = _check_user_layers(tracked)
    for rel in user_layers:
        violations.append(
            f"{rel}: the user config layer is runtime state (like .env) and must not be committed"
        )
    violations.extend(_check_key_literals(tracked))
    violations.extend(_check_deployment_mode())

    result = {
        "tracked_files": len(tracked),
        "user_layers_tracked": user_layers,
        "violations": violations,
        "ok": not violations,
    }

    print("設定衛生門禁（提交的配置必須等於預設）")
    print(f"  被追蹤檔案：{len(tracked)}")
    print(f"  被追蹤的 user 層：{len(user_layers)}（應為 0）")
    if violations:
        print("  ❌ 違規：")
        for item in violations:
            print(f"    - {item}")
    else:
        print("  ✅ 通過：沒有非預設配置被提交")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  結果已寫入 {args.json_path}")
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
