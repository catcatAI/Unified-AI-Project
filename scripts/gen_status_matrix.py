#!/usr/bin/env python3
"""STATUS_MATRIX 生成器與核對器 — YAML 真相源 ↔ MD 生成視圖。

docs/status_matrix.yaml 是單一真相源；docs/STATUS_MATRIX.md 由本工具生成。
手改生成 MD 會被覆蓋；改狀態請改 YAML。

雙模式：
  generate（預設）  YAML → STATUS_MATRIX.md
  check             核對三層（--ci 退出碼契約：0 通過 / 1 違規 / 2 工具錯）
    1. 結構層    YAML 語法、必填欄位、status 合法值、id 唯一
    2. 實體層    implementation/tests 檔案存在性
    3. 語意層    verified ⇔ verify_command 雙向

只用 stdlib＋pyyaml（pyproject base 依賴）。
"""

import argparse
import datetime
import os
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

VALID_STATUSES = {"claimed", "implemented", "wired", "verified", "production"}
REQUIRED_FIELDS = ("id", "domain", "claim", "status")
# verified/production 必須可驗證；claimed 不得附實作宣稱外的證據門
STATUS_REQUIRES_VERIFY = {"verified", "production"}

STATUS_LABELS = {
    "claimed": "`claimed`",
    "implemented": "**implemented**",
    "wired": "**wired**",
    "verified": "**verified**",
    "production": "**production**",
}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def check(root, data):
    """三層核對。回傳違規字串清單（空 = 通過）。"""
    problems = []
    features = data.get("features") or []
    if not features:
        return ["YAML 無 features 或為空"]

    seen_ids = set()
    for i, feat in enumerate(features):
        if not isinstance(feat, dict):
            problems.append(f"features[{i}] 不是映射")
            continue
        fid = feat.get("id") or f"<index {i}>"
        # 結構層
        for field in REQUIRED_FIELDS:
            if not feat.get(field):
                problems.append(f"[{fid}] 缺必填欄位 `{field}`")
        if feat.get("status") not in VALID_STATUSES:
            problems.append(
                f"[{fid}] status=`{feat.get('status')}` 不合法"
                f"（合法：{'/'.join(sorted(VALID_STATUSES))}）"
            )
        if fid in seen_ids:
            problems.append(f"[{fid}] id 重複")
        seen_ids.add(fid)
        if feat.get("status") == "claimed" and feat.get("evidence"):
            problems.append(f"[{fid}] claimed 不應附 evidence（無驗證即 claimed）")

        # 實體層：implementation / tests 路徑存在性
        for field in ("implementation", "tests"):
            for path in feat.get(field) or []:
                full = os.path.join(root, path)
                if not os.path.exists(full):
                    problems.append(f"[{fid}] {field} 路徑不存在：{path}")

        # 語意層：verified ⇔ verify_command 雙向
        has_cmd = bool(feat.get("verify_command"))
        needs = feat.get("status") in STATUS_REQUIRES_VERIFY
        if needs and not has_cmd:
            problems.append(f"[{fid}] status={feat['status']} 但缺 verify_command")
        if has_cmd and not needs:
            problems.append(
                f"[{fid}] 有 verify_command 但 status={feat['status']}"
                f"（{'+'.join(sorted(STATUS_REQUIRES_VERIFY))} 才需附）"
            )
    return problems


def render_md(root, data):
    """YAML → STATUS_MATRIX.md（生成視圖）。"""
    features = data.get("features") or []
    meta = data.get("meta") or {}
    today = datetime.date.today()
    lines = [
        "<!--",
        "  本檔由 scripts/gen_status_matrix.py 自 docs/status_matrix.yaml 生成。",
        "  手改會被覆蓋；改狀態請改 YAML 真相源，再重跑生成器。",
        f"  真相源：docs/status_matrix.yaml（meta.version={meta.get('version', '?')}）",
        "-->",
        "",
        "# STATUS_MATRIX — 功能成熟度唯一總表",
        "",
        "> 本檔是**生成視圖**；單一真相源是 [`status_matrix.yaml`](status_matrix.yaml)。"
        "五級狀態：`claimed`（宣稱存在）→ `implemented`（程式存在）→ `wired`（生產路徑呼叫）→",
        "> `verified`（端到端測試證明）→ `production`（benchmark 達標）。"
        "每列必須附驗證指令與日期；無法附者降回 `claimed`。",
        "> 「架構完成度」≠「模型能力完成度」：確定性能力與神經泛化分開計分"
        "（見 INTELLIGENCE_ASSESSMENT）。",
        f"> 狀態快照：{today}（由 YAML 同步）。核對："
        "`python scripts/gen_status_matrix.py check`（0 通過 / 1 違規）。",
        "",
        "| 領域 | Claim（宣稱） | Implementation（實作） | 狀態 | 驗證指令／證據 | 最後驗證 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for feat in features:
        fid = feat.get("id", "?")
        impl = feat.get("implementation") or []
        impl_str = "<br>".join(f"`{p}`" for p in impl) if impl else "—（見證據欄）"
        verify = feat.get("verify_command") or ""
        evidence = feat.get("evidence") or ""
        verify_cell = (
            f"`{verify}`{'；' + evidence if evidence else ''}" if verify else (evidence or "—")
        )
        lines.append(
            f"| {feat.get('domain', '?')} | {feat.get('claim', '?')} | {impl_str} "
            f"| {STATUS_LABELS.get(feat.get('status'), feat.get('status'))} "
            f"| {verify_cell} | {feat.get('last_verified', '—')} |"
        )
    lines += [
        "",
        "## 誠實缺口（正式版判斷依據）",
        "",
        "1. **路由重複決策**（Pipeline/Router/ModelBus 各自分類）— 架構債，最高優先收斂。",
        "2. **學習品質未證明** — 「字典增長」≠「能力增長」；需 hold-out 前後測成為常態門。",
        "3. **Dashboard E2E** — 新面板僅 wired，缺自動化瀏覽器測試。",
        "4. **mypy 559** — 棘輪門鎖定（`scripts/mypy_budget_gate.py`）；新增型別債 CI 直接紅燈。",
        "5. **公開 benchmark** — 確定性能力有腳本級驗證；對外可重現的品質報告尚未發佈。",
        "6. **Luanti policy** — 訓練管線已通（hold-out 學習門鎖測試）；live 樣本待玩家在線累積；20 FPS 仍 ❌（10Hz＋2s poller）。",
        "7. **EmotionSystem 跨進程不共享** — 遊戲 agent 與主 server 生命階段已透過共享 lifecycle JSON 互通（R71c），情緒狀態仍各自 in-memory。",
        "",
        "> 調用方式查詢：見 **[`INVOCATION_MATRIX.md`](INVOCATION_MATRIX.md)**。"
        "本表答「能不能用、多成熟」；該表答「怎麼用、配什麼、怎麼驗證」。",
        "",
        "## 維護規則",
        "",
        "- 改狀態**只改 `docs/status_matrix.yaml`**，重跑"
        " `python scripts/gen_status_matrix.py`；手改本檔會被覆蓋。",
        "- 任何「看起來完成」必須附驗證指令＋日期，否則寫 `claimed`。",
        "- YAML 落實體核對：路徑不存在 / verified 無指令 → `gen_project_map.py` CI 紅燈。",
        "- 修復安全相關項目時，同時把 regression payload 加進 `tests/security/`。",
        "- 舊文件與本表衝突時，以本表為準並修訂舊文件。",
        "",
    ]
    return lines


def main():
    ap = argparse.ArgumentParser(description="STATUS_MATRIX 生成器＋核對器")
    ap.add_argument("mode", nargs="?", default="generate", choices=["generate", "check"])
    ap.add_argument("--yaml", default="docs/status_matrix.yaml")
    ap.add_argument("--output", default="docs/STATUS_MATRIX.md")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    if yaml is None:
        print("TOOL ERROR: pyyaml 未安裝（base 依賴應有；pip install pyyaml）")
        return 2
    root = os.path.abspath(args.root)
    yaml_path = os.path.join(root, args.yaml) if not os.path.isabs(args.yaml) else args.yaml
    try:
        data = load_yaml(yaml_path)
    except (OSError, yaml.YAMLError) as e:
        print(f"TOOL ERROR: {e}")
        return 2

    if args.mode == "check":
        problems = check(root, data)
        if problems:
            print(f"STATUS_MATRIX 核對：{len(problems)} 項違規")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"STATUS_MATRIX 核對通過：{len(data.get('features') or [])} 條目，三層全綠")
        return 0

    out_lines = render_md(root, data)
    out_path = os.path.join(root, args.output) if not os.path.isabs(args.output) else args.output
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
    except OSError as e:
        print(f"TOOL ERROR: {e}")
        return 2
    print(f"OK: {out_path}（{len(out_lines)} 行，{len(data.get('features') or [])} 條目）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
