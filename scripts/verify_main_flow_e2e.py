#!/usr/bin/env python3
"""主流程端到端實測（R11 正式版實際使用證據）：用戶文本進 → 最終回應出。

走真實生產接線（classifier → gate → ModelBus.execute_handler），
handler 註冊複用 AngelaLLMService._register_model_bus_handlers（單一真相源，
不另寫鏡像）。只執行 auto_execute 且本地安全項；confirm 項驗 verdict +
handler 可解（模擬用戶確認前不執行）；網路項（search）只驗 verdict。

退出碼：0 全過 / 1 任一失敗（判定基線：正式版 RELEASE_CRITERIA.md）。
task 寫入已隔離（HOME 指向 tmp，見上），其餘皆唯讀或本地安全項。
"""

import asyncio
import os
import sys
import tempfile
import types

# task 寫入隔離：必須在 backend 模組 import 前設定，否則
# TaskManagerHandler 的 _TASKS_DIR 已綁定真實家目錄（R13）。
os.environ["HOME"] = tempfile.mkdtemp(prefix="e2e-fakehome-")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

# auto + 本地執行（ Garbage-free, 用戶態寫入限隔離 HOME）
# search 需真實網路（R18）：結構斷言（成功旗標＋前綴），不逐字斷言內容
# （檢索排序品質另案追蹤；此處只證鏈路通）。
EXEC_CASES = [
    # (用戶文本, 期望 type, 期望 gate, 期望 handler, 回應必須含)
    ("梁計算 b=300 d=450 As=1256", "civil", "auto_execute", "civil", "M_Rd="),
    ("列出 scripts/ 目錄文件", "file", "auto_execute", "file_ops", "scripts"),
    (
        "這張圖片裡有什麼 test_models/test_avatar_20260826_030647/layers/nose.png",
        "vision",
        "auto_execute",
        "vision",
        "（視覺分析）",
    ),
    ("建立任務：買牛奶", "task", "auto_execute", "task_mgr", "買牛奶"),
    ("任務列表", "task", "auto_execute", "task_mgr", "買牛奶"),
    ("完成任務 #1", "task", "auto_execute", "task_mgr", "完成"),
    ("搜尋台北天氣", "search", "auto_execute", "web_search", "（網路搜尋）"),
]

# confirm：只驗 verdict + handler 可解（不模擬用戶按確認）
CONFIRM_CASES = [
    ("執行 pwd", "execute", "confirm_then_execute", "code_exec"),
    ("提交報告", "system", "confirm_then_execute", "system_cmd"),
    ("整理桌面文件", "file", "confirm_then_execute", "file_ops"),
    ("刪除任務 #1", "task", "confirm_then_execute", "task_mgr"),
]

# 非動作：閘門應拒絕（交 LLM），不打擾用戶
REJECT_CASES = ["你好", "哦", "xyzabc"]


def main():
    from ai.core.execution_gate import ExecutionGate
    from ai.core.model_bus import ModelBus
    from ai.core.query_classifier import QueryClassifier
    from services.llm.router import AngelaLLMService

    qc = QueryClassifier()
    gate = ExecutionGate()
    mb = ModelBus()
    AngelaLLMService._register_model_bus_handlers(types.SimpleNamespace(model_bus=mb))

    fails = []

    async def run_exec(text, want_type, want_gate, want_handler, must_contain):
        r = qc.classify(text)
        d = gate.decide(r.primary_type.value, r.action_type, text, r.confidence, {})
        if r.primary_type.value != want_type or d.action != want_gate:
            return f"verdict 走偏：cls={r.primary_type.value} gate={d.action}"
        if d.handler != want_handler or d.handler not in mb._handlers:
            return f"handler 不可解：{d.handler}"
        try:
            out = await asyncio.wait_for(
                mb.execute_handler(d.handler, text, {"query_type": r.primary_type.value}),
                timeout=60,
            )
        except Exception as e:  # noqa: BLE001 — 實測腳本：異常即失敗證據
            return f"執行異常：{e}"
        if not out.get("success") or must_contain not in str(out.get("result")):
            return f"回應不符：{str(out.get('result'))[:120]}"
        return ""

    async def amain():
        for text, wt, wg, wh, mc in EXEC_CASES:
            err = await run_exec(text, wt, wg, wh, mc)
            print(f"  {'✅' if not err else '❌'} EXEC {text[:28]:28} {err}")
            if err:
                fails.append(text)
        for text, wt, wg, wh in CONFIRM_CASES:
            r = qc.classify(text)
            d = gate.decide(r.primary_type.value, r.action_type, text, r.confidence, {})
            ok = (
                r.primary_type.value == wt
                and d.action == wg
                and d.handler == wh
                and wh in mb._handlers
            )
            print(
                f"  {'✅' if ok else '❌'} CONFIRM {text[:28]:28} "
                f"cls={r.primary_type.value} gate={d.action}"
            )
            if not ok:
                fails.append(text)
        for text in REJECT_CASES:
            r = qc.classify(text)
            d = gate.decide(r.primary_type.value, r.action_type, text, r.confidence, {})
            ok = d.action == "reject"
            print(
                f"  {'✅' if ok else '❌'} REJECT  {text[:28]:28} "
                f"cls={r.primary_type.value} gate={d.action}"
            )
            if not ok:
                fails.append(text)

    print("主流程 e2e（classify→gate→execute 真接線）：")
    asyncio.run(amain())
    print(
        f"結果：{len(EXEC_CASES) + len(CONFIRM_CASES) + len(REJECT_CASES) - len(fails)}/"
        f"{len(EXEC_CASES) + len(CONFIRM_CASES) + len(REJECT_CASES)} 通過"
    )
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
