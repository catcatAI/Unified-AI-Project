# =============================================================================
# ANGELA-MATRIX: [L4] [α] [A] [L7]
# =============================================================================
"""專案AI自主研究管線測試（upgrade_research + 端點 + CLI 契約）。

涵蓋：版面常數一致性、輕量真實採集器、候選推導/透明公式擇優、章節生成、
LLM 潤色數字指紋守護、validate_report 零容忍各缺口分支、合成事實全管線
e2e、研究端點綁定/呼叫、CLI exit code。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest
from ai.research import upgrade_research as ur

REPO = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# 合成事實（貼近真實結構，供 draft/validate/e2e 使用）
# ---------------------------------------------------------------------------

_CHECK_TEXTS = {
    "A2": "決定 checkpoint 來源：從外置機器取回或本機重訓入庫（不修則訓練白跑）",
    "A3": "train_exact_bytes/heldout_bpc 接上呼叫者（訓練報表由留出集產生）",
    "A4": "補齊 3 個缺數據檔或明確從 pipeline 移除（禁止靜默 skip）",
    "A5": "GARDEN accuracy 改實測回傳；ED3N 評估改 hold-out",
    "A6": "統一評測入口：benchmark_ed3n_garden --gate 加留出集數字入 JSON 工件",
    "B4": "分通道定義主 ai：測評分開計 COMPOSED/fusion-google/unified/fallback",
    "C1": "離線策略三選一起 llama-server 或 ollama 或純雲端（現況離線開放域為 0）",
    "C3": "key 治理：keys.*.yaml 接載或刪除；避免單 .env 隱性依賴",
    "D1": "收斂 llm_mode/deployment.mode 雙變數分叉；修 _allowed_types 讀取層級",
    "D2": "清死檔（llm.evolved.yaml）、routing.policy 死碼、stats 初始化",
    "E1": "未見泛化探針 probe_reasoning_unseen.py（symbolic vs neural 分列）",
    "E2": "angela_bench gate 作回歸地板（math/knowledge_mc/routing）",
    "E3": "分數類型標注嚴格遵循六型表（架構/框架/預期/訓練/驗證/實際）",
}


def _mk_facts() -> dict:
    pending = [{"id": i, "done": False, "text": t} for i, t in _CHECK_TEXTS.items()]
    return {
        "generated_at": "2026-10-18T00:00:00",
        "repo_root": str(REPO),
        "repo": {
            "py_files": 667,
            "py_lines": 96000,
            "checkpoint_dir_exists": True,
            "checkpoints": ["old/weights.bin"],
            "unified_checkpoint_present": False,
        },
        "test_count": {"count": 8426, "method": "pytest --collect-only"},
        "status_matrix": {
            "total": 25,
            "by_status": {"verified": 15, "wired": 7, "implemented": 3},
            "pending": [
                {
                    "id": f"f{i}",
                    "status": "wired",
                    "claim": f"功能{i}已接線待驗證",
                    "verify_command": "pytest x",
                }
                for i in range(1, 11)
            ],
            "chat_pipeline": "verified",
        },
        "verification_register": {
            "open": 3,
            "entries": [
                {
                    "id": f"V{i}",
                    "claim": f"宣稱{i}：某模組行為與文件不符",
                    "why_unverified": "缺少自動化驗證命令",
                    "how_to_verify": "補一條 pytest 斷言後執行",
                    "area": "ai",
                }
                for i in range(1, 4)
            ],
        },
        "benchmarks": {
            "file": "bench_20260922-091107.json",
            "generated_at": "2026-09-22T09:11:07",
            "suites": [
                {
                    "backend": "native",
                    "suite": "math",
                    "total": 40,
                    "passed": 32,
                    "skipped": 0,
                    "accuracy": 80.0,
                    "floor": 75.0,
                    "state": "pass",
                },
                {
                    "backend": "native",
                    "suite": "knowledge_mc",
                    "total": 40,
                    "passed": 39,
                    "skipped": 0,
                    "accuracy": 97.5,
                    "floor": 90.0,
                    "state": "pass",
                },
                {
                    "backend": "native",
                    "suite": "code",
                    "total": 10,
                    "passed": 3,
                    "skipped": 0,
                    "accuracy": 30.0,
                    "floor": None,
                    "state": "no-floor",
                },
                {
                    "backend": "native",
                    "suite": "routing",
                    "total": 10,
                    "passed": 10,
                    "skipped": 0,
                    "accuracy": 100.0,
                    "floor": 95.0,
                    "state": "pass",
                },
            ],
        },
        "fact_gates": {
            "exit_code": 0,
            "passed": True,
            "checks": [{"name": "edge", "ok": True}, {"name": "chat", "ok": True}],
            "failed": [],
            "tail": "ALL PASS",
        },
        "validation": {
            "ed3n": {"ok": True, "engines": ["snn"], "datasets": ["math"]},
            "garden": {"ok": True, "engines": ["snn"], "datasets": ["cifar"]},
        },
        "checklist": {
            "total": 18,
            "done": 5,
            "pending": pending,
            "done_ids": ["A1", "B1", "B2", "B3", "C2"],
        },
        "docs_index": {
            "FRAMEWORK_OVERVIEW.md": {"path": "docs/FRAMEWORK_OVERVIEW.md", "lines": 800},
            "STATUS_MATRIX.md": {"path": None, "lines": 0},
        },
        "rule_store": {
            "total": 4,
            "serves": 12,
            "feedback": 6,
            "by_kind": {"math": 3},
            "avg_confidence": 0.7,
        },
        "collectors": [
            {"collector": n, "ok": True, "detail": "ok", "ms": 5}
            for n in (
                "repo_stats",
                "test_count",
                "status_matrix",
                "verification_register",
                "benchmarks",
                "fact_gates",
                "validation_reports",
                "assessment_checklist",
                "docs_index",
                "rule_store",
            )
        ],
    }


def _mk_web_offline() -> list:
    return [
        {"query": q, "ok": False, "error": "disabled（--no-web）"} for q in ur._EXTERNAL_QUERIES
    ]


def _mk_probes() -> list:
    return [
        {"probe": "deterministic.math+logic", "ok": True, "ms": 3, "output": "math ok"},
        {"probe": "ed3n.process", "ok": True, "ms": 7, "output": "2+2 = 4"},
    ]


def _mk_bundle() -> tuple:
    facts = _mk_facts()
    web = _mk_web_offline()
    probes = _mk_probes()
    facts["_probes"] = probes
    cands = ur.derive_candidates(facts)
    md = ur.draft_report(
        facts, web, probes, cands, [{"block": "p0:x", "action": "disabled（--no-polish）"}], 1.0
    )
    return facts, web, probes, cands, md


# ---------------------------------------------------------------------------
# 基礎常數 / 工具
# ---------------------------------------------------------------------------


class TestBasics:
    def test_repo_root_points_at_project(self) -> None:
        root = ur._repo_root()
        assert (root / "scripts" / "run_benchmarks.py").is_file()
        assert (root / "apps" / "backend" / "src").is_dir()

    def test_section_constants_aligned(self) -> None:
        assert set(ur._SECTION_MIN_CHARS) == set(ur._SECTION_HEADERS)
        assert len(ur._SECTION_HEADERS) == 9

    def test_numeric_fingerprint_ignores_wording(self) -> None:
        a = ur._numeric_fingerprint("共 12.5 個樣本，-3 次失敗")
        b = ur._numeric_fingerprint("樣本 12.5 共，失敗 -3 次")
        assert a == b == Counter({"12.5": 1, "-3": 1})

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("# 標題", True),
            ("> 引用", True),
            ("```bash", True),
            ("| a | b |", True),
            ("", True),
            ("這是一般敘述段落", False),
        ],
    )
    def test_is_table_or_heading(self, text: str, expected: bool) -> None:
        assert ur._is_table_or_heading(text) is expected


# ---------------------------------------------------------------------------
# 輕量真實採集器（自己查：讀真 repo）
# ---------------------------------------------------------------------------


class TestLightCollectorsRealRepo:
    def test_checklist_parses_with_consistent_counts(self) -> None:
        # 2026-10-19：原斷言 done==5 是五步曲批次（A5/B4/D2/E3…完成後漂移）的
        # 過時釘數——living checklist 改驗不變量：total>0、done 與 done_ids
        # 一致、首批已完成項仍在 done 內。
        res = ur._collect_checklist(ur._repo_root())
        assert res["total"] >= 18
        assert res["done"] == len(res["done_ids"])
        assert res["done"] >= 5
        assert {"A1", "B1", "B2", "B3", "C2"} <= set(res["done_ids"])
        assert all(i["id"] for i in res["pending"])

    def test_status_matrix_counts(self) -> None:
        res = ur._collect_status_matrix(ur._repo_root())
        assert res["total"] >= 20
        assert sum(res["by_status"].values()) == res["total"]
        assert isinstance(res["pending"], list)

    def test_verification_register_open_entries(self) -> None:
        res = ur._collect_verification_register(ur._repo_root())
        assert res["open"] >= 1
        assert all(e["claim"] for e in res["entries"])

    def test_benchmarks_with_gate_native_floors(self) -> None:
        res = ur._collect_benchmarks(ur._repo_root())
        assert res["suites"]
        native = {s["suite"]: s for s in res["suites"] if s["backend"] == "native"}
        assert {"math", "knowledge", "knowledge_mc", "routing"} <= set(native)
        assert native["math"]["floor"] == 75.0
        assert native["knowledge_mc"]["floor"] == 90.0
        assert native["math"]["state"] in ("pass", "margin", "below", "no-floor")
        assert any(s["state"] == "below" for s in res["suites"]), "echo/naive 基準套件應低於地板"

    def test_benchmark_collector_prefers_a_comparable_run(self, tmp_path: Path) -> None:
        """部分跑（單一 backend／suite）不是可比 artifact，不能因為它最新就選它。"""
        results = tmp_path / "benchmarks" / "results"
        results.mkdir(parents=True)
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "run_benchmarks.py").write_text(
            'GATE_NATIVE = {"math": 75.0}\n', encoding="utf-8"
        )
        full = {
            "generated_at": "2026-01-01T00:00:00",
            "results": [
                {"backend": b, "suite": "math", "accuracy": 10.0, "total": 1, "passed": 0}
                for b in ("native", "echo", "naive")
            ],
        }
        partial = {
            "generated_at": "2026-01-02T00:00:00",
            "results": [
                {
                    "backend": "native",
                    "suite": "knowledge",
                    "accuracy": 46.7,
                    "total": 15,
                    "passed": 7,
                }
            ],
        }
        (results / "bench_20260101-000000.json").write_text(json.dumps(full), encoding="utf-8")
        (results / "bench_20260102-000000.json").write_text(json.dumps(partial), encoding="utf-8")

        collected = ur._collect_benchmarks(tmp_path)

        assert collected["file"] == "bench_20260101-000000.json"
        assert {s["backend"] for s in collected["suites"]} == {"native", "echo", "naive"}

    def test_repo_stats(self) -> None:
        res = ur._collect_repo_stats(ur._repo_root())
        assert res["py_files"] > 100
        assert res["py_lines"] > 10000
        assert isinstance(res["unified_checkpoint_present"], bool)

    def test_fact_gates_structure(self) -> None:
        res = ur._collect_fact_gates(ur._repo_root())
        assert res["exit_code"] in (0, 1)
        assert isinstance(res["passed"], bool)
        assert res["checks"], "check_fact_gates 應至少回報一項"

    def test_docs_index(self) -> None:
        res = ur._collect_docs_index(ur._repo_root())
        assert res["FRAMEWORK_OVERVIEW.md"]["path"]
        assert res["FRAMEWORK_OVERVIEW.md"]["lines"] > 100

    def test_rule_store_stats(self) -> None:
        res = ur._collect_rule_store()
        assert {"total", "serves", "feedback", "avg_confidence", "by_kind"} <= set(res)

    def test_test_count_ast_fallback_when_pytest_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(ur, "_run_capture", lambda *a, **k: (2, "boom"))
        res = ur._collect_test_count(ur._repo_root())
        assert res["method"].startswith("ast-fallback")
        assert res["count"] > 1000


# ---------------------------------------------------------------------------
# 自有模型體檢 — 輕量探針（實跑真模型/引擎）
# ---------------------------------------------------------------------------


class TestLightProbesReal:
    def test_deterministic_math_logic(self) -> None:
        out = ur._probe_deterministic_math()
        assert "7006652" in out

    def test_knowledge_route_hits(self) -> None:
        assert ur._probe_knowledge_route() == "blue"

    def test_symbolic_route_hits(self) -> None:
        out = ur._probe_symbolic_route()
        assert isinstance(out, str) and out.strip()

    def test_rules_verify_accepts_true_positive(self) -> None:
        assert "verified" in ur._probe_rules_verify()

    def test_formula_solver_hits(self) -> None:
        out = ur._probe_formula_solve()
        assert "12" in out


# ---------------------------------------------------------------------------
# 候選推導 + 透明公式擇優（自己想）
# ---------------------------------------------------------------------------


def _cand_facts() -> dict:
    return {
        "checklist": {"pending": [{"id": "A2", "text": "決定 checkpoint 來源與重訓入庫路線"}]},
        "verification_register": {
            "entries": [
                {
                    "id": "V1",
                    "claim": "宣稱一",
                    "how_to_verify": "補測試",
                    "why_unverified": "無命令",
                    "area": "ai",
                }
            ]
        },
        "status_matrix": {"pending": [{"id": "f1"}], "by_status": {"wired": 1}},
        "benchmarks": {
            "suites": [
                {
                    "backend": "native",
                    "suite": "math",
                    "accuracy": 70.0,
                    "floor": 75.0,
                    "state": "below",
                    "passed": 35,
                    "total": 50,
                },
                {
                    "backend": "native",
                    "suite": "knowledge_mc",
                    "accuracy": 97.5,
                    "floor": 90.0,
                    "state": "pass",
                    "passed": 39,
                    "total": 40,
                },
                {
                    "backend": "native",
                    "suite": "code",
                    "accuracy": 30.0,
                    "floor": None,
                    "state": "no-floor",
                    "passed": 3,
                    "total": 10,
                },
                {
                    "backend": "native",
                    "suite": "routing",
                    "accuracy": 95.5,
                    "floor": 95.0,
                    "state": "margin",
                    "passed": 10,
                    "total": 10,
                },
                {
                    "backend": "native-max",
                    "suite": "math",
                    "accuracy": 100.0,
                    "floor": None,
                    "state": "no-floor",
                    "passed": 5,
                    "total": 5,
                },
            ]
        },
        "fact_gates": {"failed": ["edge"], "exit_code": 1},
        "repo": {
            "checkpoint_dir_exists": True,
            "unified_checkpoint_present": False,
            "checkpoints": [],
        },
        "collectors": [{"collector": "benchmarks", "ok": False, "detail": "boom", "ms": 1}],
        "docs_index": {"STATUS_MATRIX.md": {"path": None, "lines": 0}},
    }


class TestDeriveCandidates:
    def test_all_rules_fire_with_expected_ids(self) -> None:
        cands = ur.derive_candidates(_cand_facts())
        ids = {c["id"] for c in cands}
        assert "A2" in ids
        assert "VR-V1" in ids
        assert "SM-promote" in ids
        assert "BENCH-math" in ids
        assert "BENCH-floor-code" in ids
        assert "BENCH-margin-routing" in ids
        assert "GATE-edge" in ids
        assert "CKPT-unified" in ids
        assert "COL-benchmarks" in ids
        assert "DOCS-missing" in ids
        assert not any("BENCH-floor-knowledge" in i for i in ids), "pass 套件不該產生候選"
        assert not any(i.startswith("BENCH-") and "native-max" in i for i in ids)

    def test_score_formula_is_transparent(self) -> None:
        cands = {c["id"]: c for c in ur.derive_candidates(_cand_facts())}
        gate = cands["GATE-edge"]
        # source=fact-gates → impact 3, bonus 2；動作無 effort 關鍵字 → 2；risk 2
        expected = 4 * 3 + 2 * (4 - 2) + 2 * (4 - 2) + 2
        assert (gate["impact"], gate["effort"], gate["risk"]) == (3, 2, 2)
        assert gate["score"] == expected == 22
        ckpt = cands["CKPT-unified"]
        assert ckpt["effort"] == 3, "checkpoint 關鍵字 → 重工作量"

    def test_sort_waves_and_picked(self) -> None:
        cands = ur.derive_candidates(_cand_facts())
        scores = [c["score"] for c in cands]
        assert scores == sorted(scores, reverse=True)
        picked = [c["id"] for c in cands if c["picked"]]
        assert picked == [c["id"] for c in cands[:3]]
        assert {c["wave"] for c in cands} <= {1, 2, 3}
        for c in cands:
            assert c["evidence"] and c["title"]

    def test_each_candidate_scored(self) -> None:
        for c in ur.derive_candidates(_cand_facts()):
            recomputed = (
                4 * c["impact"]
                + 2 * (4 - c["effort"])
                + 2 * (4 - c["risk"])
                + ur._SOURCE_BONUS.get(c["source"], 0)
            )
            assert c["score"] == recomputed


# ---------------------------------------------------------------------------
# 章節生成（自己寫）
# ---------------------------------------------------------------------------


class TestDraftReport:
    def test_all_nine_sections_and_key_markers(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        for header in ur._SECTION_HEADERS:
            assert header in md
        assert "建議先做" in md
        assert "LLM 潤色記錄" in md
        assert "8426" in md
        assert "32/40" in md
        assert "擇優（公式排序前 3" in md
        # 每章達最小字數（validate 的版面規則同源）
        for header, minimum in ur._SECTION_MIN_CHARS.items():
            start = md.index(header)
            nxt = min(
                [
                    md.find(h, start + len(header))
                    for h in ur._SECTION_HEADERS
                    if md.find(h, start + len(header)) != -1
                ]
                or [len(md)],
            )
            assert len(md[start:nxt].strip()) >= minimum, f"{header} 過短"

    def test_appendix_lists_sources_and_reproduce_commands(self) -> None:
        _, web, _, _, md = _mk_bundle()
        assert "未取得" in md
        assert "check_fact_gates" in md
        assert "generate_upgrade_report" in md

    def test_offline_web_recorded_not_silent(self) -> None:
        _, _, _, _, md = _mk_bundle()
        assert "外部查證未取得" in md
        assert "disabled（--no-web）" in md


# ---------------------------------------------------------------------------
# LLM 潤色 — 數字指紋守護
# ---------------------------------------------------------------------------

_POLISH_MD = (
    "# 標題\n\n"
    "本輪共 1234 個測試樣本通過了完整驗證流程，檢查完畢且敘述足夠長以通過六十字以上的"
    "潤色挑選條件門檻，以下為填充敘述文字使其長度確認超過六十個字元以上。\n\n"
    "| a | b |\n|---|---|\n| 1 | 2 |"
)


class _FakeLLM:
    def __init__(self, text: str) -> None:
        self._text = text

    async def generate_text(self, **kwargs) -> str:
        return self._text


class TestPolish:
    @pytest.mark.asyncio
    async def test_disabled_keeps_md_and_records(self) -> None:
        md, records = await ur.polish_report(_POLISH_MD, False)
        assert md == _POLISH_MD
        assert records and "disabled" in records[0]["action"]

    @pytest.mark.asyncio
    async def test_llm_unavailable_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _raise():
            raise ImportError("no llm")

        monkeypatch.setattr("services.angela_llm_service.get_llm_service", _raise)
        md, records = await ur.polish_report(_POLISH_MD, True)
        assert md == _POLISH_MD
        assert any("fallback" in r["action"] for r in records)

    @pytest.mark.asyncio
    async def test_fingerprint_mismatch_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def _fake_get():
            return _FakeLLM(
                "數字被偷改的潤色結果 9999 個測試樣本通過了完整驗證流程，檢查完畢且敘述足夠長以通過六十字以上的潤色挑選條件門檻。"
            )

        monkeypatch.setattr("services.angela_llm_service.get_llm_service", _fake_get)
        md, records = await ur.polish_report(_POLISH_MD, True)
        assert md == _POLISH_MD, "指紋失配必須回退原稿"
        assert any("指紋失配" in r["action"] for r in records)

    @pytest.mark.asyncio
    async def test_matching_fingerprint_polished(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rewritten = (
            "驗證流程完整檢查完畢：本輪共有 1234 個測試樣本通過，敘述足夠長以通過"
            "六十字以上的潤色挑選條件門檻，以下為填充敘述文字使其長度確認超過六十個字元以上。"
        )

        async def _fake_get():
            return _FakeLLM(rewritten)

        monkeypatch.setattr("services.angela_llm_service.get_llm_service", _fake_get)
        md, records = await ur.polish_report(_POLISH_MD, True)
        assert rewritten in md
        assert any(r["action"] == "polished" for r in records)
        # 表格與標題不受潤色影響
        assert "| a | b |" in md
        assert md.startswith("# 標題")


# ---------------------------------------------------------------------------
# validate_report — 無異常零容忍（各缺口分支）
# ---------------------------------------------------------------------------


class TestValidateReport:
    def test_clean_bundle_no_problems(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        records = [{"block": "p1", "action": "disabled（--no-polish）"}]
        assert ur.validate_report(md, facts, cands, web, records) == []

    def test_missing_section(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        md = md.replace("## 五、實測現狀", "## 五、別的")
        problems = ur.validate_report(md, facts, cands, web, [{"block": "b", "action": "disabled"}])
        assert any("缺章" in p and "實測現狀" in p for p in problems)

    def test_placeholder_detection(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        problems = ur.validate_report(
            md + "\n\nTODO 待補內容", facts, cands, web, [{"block": "b", "action": "x"}]
        )
        assert any("佔位字" in p for p in problems)

    def test_too_few_candidates(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        problems = ur.validate_report(md, facts, cands[:5], web, [{"block": "b", "action": "x"}])
        assert any("候選覆蓋不足" in p for p in problems)

    def test_too_few_picked(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        unpicked = [dict(c, picked=False) for c in cands]
        problems = ur.validate_report(md, facts, unpicked, web, [{"block": "b", "action": "x"}])
        assert any("擇優項不足" in p for p in problems)

    def test_web_sources_insufficient(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        ok_web = [
            {
                "query": "q",
                "ok": True,
                "sources": [{"url": "http://a"}, {"url": "http://b"}],
                "facts": ["f"],
            }
        ]
        problems = ur.validate_report(md, facts, cands, ok_web, [{"block": "b", "action": "x"}])
        assert any("外部來源不足" in p for p in problems)

    def test_web_all_failed_needs_record_in_md(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        scrubbed = md.replace("未取得", "取得")
        problems = ur.validate_report(scrubbed, facts, cands, web, [{"block": "b", "action": "x"}])
        assert any("外部查證全失敗" in p for p in problems)

    def test_empty_polish_records(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        problems = ur.validate_report(md, facts, cands, web, [])
        assert any("潤色無記錄" in p for p in problems)

    def test_evidence_mismatch_test_count(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        facts = dict(facts, test_count={"count": 999999, "method": "x"})
        problems = ur.validate_report(md, facts, cands, web, [{"block": "b", "action": "x"}])
        assert any("證據不一致" in p for p in problems)

    def test_failed_collector_must_appear_in_md(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        facts = dict(facts)
        facts["collectors"] = facts["collectors"] + [
            {"collector": "ghost_collector", "ok": False, "detail": "boom", "ms": 1}
        ]
        problems = ur.validate_report(md, facts, cands, web, [{"block": "b", "action": "x"}])
        assert any("ghost_collector" in p for p in problems)

    def test_all_probes_failed_is_problem(self) -> None:
        facts, web, probes, cands, md = _mk_bundle()
        facts = dict(facts, _probes=[{"probe": "x", "ok": False, "ms": 1, "error": "e"}])
        problems = ur.validate_report(md, facts, cands, web, [{"block": "b", "action": "x"}])
        assert any("全數失敗" in p for p in problems)


# ---------------------------------------------------------------------------
# 全管線 e2e（合成事實 + 離線 + 無潤色）
# ---------------------------------------------------------------------------


class TestE2ESynthetic:
    @pytest.mark.asyncio
    async def test_run_upgrade_research_clean(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        facts = _mk_facts()

        def _fake_gather() -> dict:
            return facts

        async def _fake_probes() -> list:
            return _mk_probes()

        monkeypatch.setattr(ur, "gather_facts", _fake_gather)
        monkeypatch.setattr(ur, "probe_own_models", _fake_probes)

        out = str(tmp_path / "REPORT.md")
        res = await ur.run_upgrade_research(web=False, polish=False, out_path=out)

        assert res["problems"] == [], res["problems"]
        assert res["ok"] is True
        report = Path(out).read_text(encoding="utf-8")
        assert report.startswith("# 專案AI自主研究報告")
        for header in ur._SECTION_HEADERS:
            assert header in report
        assert "disabled（--no-polish）" in report
        assert res["stats"]["candidates"] >= 8
        assert len(res["stats"]["picked"]) >= 3
        assert res["stats"]["probes_ok"] == 2
        assert res["stats"]["collectors_ok"] == 10

    @pytest.mark.asyncio
    async def test_run_upgrade_research_surfaces_probe_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(ur, "gather_facts", _mk_facts)

        async def _all_fail() -> list:
            return [{"probe": "x", "ok": False, "ms": 1, "error": "boom"}]

        monkeypatch.setattr(ur, "probe_own_models", _all_fail)
        res = await ur.run_upgrade_research(
            web=False, polish=False, out_path=str(tmp_path / "R.md")
        )
        assert res["ok"] is False
        assert any("全數失敗" in p for p in res["problems"])


# ---------------------------------------------------------------------------
# CLI 契約 — problems 非空 exit 1
# ---------------------------------------------------------------------------


def _load_cli_module():
    spec = importlib.util.spec_from_file_location(
        "_gen_upgrade_report_cli", REPO / "scripts" / "generate_upgrade_report.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_result(ok: bool, problems: list) -> dict:
    return {
        "path": "/tmp/REPORT.md",
        "ok": ok,
        "problems": problems,
        "stats": {
            "elapsed_s": 1.0,
            "candidates": 13,
            "picked": ["A2", "B4", "C1"],
            "probes_ok": 9,
            "probes_total": 11,
            "web_ok": 3,
            "collectors_ok": 10,
            "collectors_total": 10,
            "polish": {"polished": 5},
            "report_chars": 9000,
        },
    }


class TestCLI:
    def test_exit_0_when_clean(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mod = _load_cli_module()

        async def _fake_run(**kwargs):
            return _fake_result(True, [])

        monkeypatch.setattr(mod, "run_upgrade_research", _fake_run)
        monkeypatch.setattr(sys, "argv", ["generate_upgrade_report.py", "--json"])
        assert mod.main() == 0

    def test_exit_1_with_problems(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mod = _load_cli_module()

        async def _fake_run(**kwargs):
            return _fake_result(False, ["缺章：## 一、摘要"])

        monkeypatch.setattr(mod, "run_upgrade_research", _fake_run)
        monkeypatch.setattr(sys, "argv", ["generate_upgrade_report.py", "--json"])
        assert mod.main() == 1

    def test_json_output_shape(self, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        mod = _load_cli_module()

        async def _fake_run(**kwargs):
            return _fake_result(True, [])

        monkeypatch.setattr(mod, "run_upgrade_research", _fake_run)
        monkeypatch.setattr(sys, "argv", ["generate_upgrade_report.py", "--json"])
        assert mod.main() == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["problems"] == []
        assert payload["stats"]["candidates"] == 13


# ---------------------------------------------------------------------------
# 研究端點 — 綁定與呼叫
# ---------------------------------------------------------------------------


class TestResearchEndpoints:
    def test_route_binding(self) -> None:
        from api.routes.research_routes import router

        routes = {r.path: set(r.methods) for r in router.routes if hasattr(r, "methods")}
        assert "/research/upgrade-report" in routes
        assert "POST" in routes["/research/upgrade-report"]
        assert "/research/upgrade-report/latest" in routes
        assert "GET" in routes["/research/upgrade-report/latest"]

    @pytest.mark.asyncio
    async def test_post_upgrade_report_delegates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import ai.research as research_pkg
        from api.routes.research_routes import run_upgrade_report

        seen = {}

        async def _fake(web: bool = True, polish: bool = True, out_path=None):
            seen.update({"web": web, "polish": polish, "out": out_path})
            return {"path": "/tmp/x.md", "ok": True, "problems": [], "stats": {"candidates": 9}}

        monkeypatch.setattr(research_pkg, "run_upgrade_research", _fake)
        res = await run_upgrade_report({"web": False, "polish": False})
        assert res["ok"] is True
        assert res["stats"]["candidates"] == 9
        assert seen == {"web": False, "polish": False, "out": None}

    @pytest.mark.asyncio
    async def test_post_upgrade_report_error_is_structured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import ai.research as research_pkg
        from api.routes.research_routes import run_upgrade_report

        async def _boom(**kwargs):
            raise RuntimeError("pipeline exploded")

        monkeypatch.setattr(research_pkg, "run_upgrade_research", _boom)
        res = await run_upgrade_report({})
        assert res["ok"] is False
        assert "pipeline exploded" in res["error"]

    @pytest.mark.asyncio
    async def test_get_latest_found_and_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import api.routes.research_routes as rr
        from api.routes.research_routes import latest_upgrade_report

        fake = tmp_path / "RESEARCH_UPGRADE_REPORT_2026-10-18.md"
        fake.write_text("# 報告\n\n內文測試", encoding="utf-8")
        monkeypatch.setattr(rr, "_find_latest", lambda root: str(fake))
        res = await latest_upgrade_report()
        assert res["ok"] and res["exists"]
        assert res["head"].startswith("# 報告")
        assert res["chars"] > 0

        monkeypatch.setattr(rr, "_find_latest", lambda root: None)
        res2 = await latest_upgrade_report()
        assert res2["ok"] and res2["exists"] is False


# ---------------------------------------------------------------------------
# 導出面
# ---------------------------------------------------------------------------


class TestExports:
    def test_package_exports(self) -> None:
        from ai.research import (
            derive_candidates,
            gather_facts,
            run_upgrade_research,
            validate_report,
        )

        assert callable(run_upgrade_research)
        assert callable(gather_facts)
        assert callable(derive_candidates)
        assert callable(validate_report)

    def test_mount_in_api_router(self) -> None:
        from api.router import router

        def _walk(rt) -> list:
            paths = []
            for route in rt.routes:
                p = getattr(route, "path", "")
                if p:
                    paths.append(p)
                orig = getattr(route, "original_router", None)
                if orig is not None:
                    paths.extend(_walk(orig))
                subs = getattr(route, "routes", None)
                if subs:
                    for s in subs:
                        sp = getattr(s, "path", "")
                        if sp:
                            paths.append(sp)
                        o2 = getattr(s, "original_router", None)
                        if o2 is not None:
                            paths.extend(_walk(o2))
            return paths

        paths = _walk(router)
        assert any(p.endswith("/research/upgrade-report") for p in paths)
