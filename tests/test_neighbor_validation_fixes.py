"""
鄰機後端驗證批次回歸測試（問題單 1-8）。

Neighbor AI runtime validation surfaced 8 problems; this batch fixed 1/2/3/4/6/8
(5 and 7 were record-only — no code change, honest analysis in commit message):

  1  integrations/__init__ eager google import + v1 endpoints all-or-nothing
  2  multimodal encode masked pipeline errors as "Unknown modality";
     modality="text" unsupported
  3  LLM decision loop logged a JSON-parse WARNING every ~2min forever and
     kept re-calling a model that never returns JSON
  4  memory/store+search+recall accepted only form bodies (JSON -> unhelpful
     422 "input: null")
  6  MetaController.save_calibration_state had zero callers and chat traffic
     never fed record_confidence
  8  is_math_message missed Unicode/full-width operators (×÷＋－−／) and
     simplified 计算, so "请计算 123 × 456" skipped the native path
"""

import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(SRC))


def _subprocess_python(code: str) -> subprocess.CompletedProcess:
    """Run code in a fresh interpreter with src on PYTHONPATH."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


# --- Problem 1: lazy integrations + per-module endpoint isolation ---


class TestLazyIntegrationsInit:
    """問題單 1a: importing integrations must not pull the google stack."""

    def test_fresh_package_import_pulls_no_google_stack(self):
        result = _subprocess_python("""
            import sys
            import integrations

            assert "googleapiclient" not in sys.modules, "google pulled by package init"
            assert "GoogleDriveService" not in vars(integrations), "lazy attr materialized at import"
            """)
        assert result.returncode == 0, result.stderr

    def test_lazy_getattr_map_dir_and_unknown(self):
        import integrations

        assert set(integrations._LAZY_INTEGRATIONS) == {
            "GoogleDriveService",
            "OSBridgeAdapter",
        }
        assert "GoogleDriveService" in dir(integrations)
        with pytest.raises(AttributeError):
            getattr(integrations, "NoSuchIntegration")


class TestV1EndpointIsolation:
    """問題單 1b: one failing endpoint module must not drop the bundle."""

    def test_expected_module_names_and_files(self):
        from api.v1.endpoints import _ENDPOINT_MODULES

        assert _ENDPOINT_MODULES == ("drive", "vision", "audio", "mobile", "trace", "plugins")
        for name in _ENDPOINT_MODULES:
            assert (SRC / "api" / "v1" / "endpoints" / f"{name}.py").is_file()

    def test_bundle_survives_drive_dependency_failure(self):
        natural = _subprocess_python("""
            from fastapi import APIRouter
            from api.v1.endpoints import include_endpoint_routers

            root = APIRouter()
            include_endpoint_routers(root)
            print("ROUTES=%d" % len(root.routes))
            """)
        assert natural.returncode == 0, natural.stderr
        natural_routes = int(natural.stdout.strip().split("=")[1])

        blocked = _subprocess_python("""
            import sys
            import importlib.abc

            class BlockDriveDeps(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path, target=None):
                    if fullname.startswith("googleapiclient"):
                        raise ImportError("googleapiclient blocked for isolation test")
                    return None

            sys.meta_path.insert(0, BlockDriveDeps())
            from fastapi import APIRouter
            from api.v1.endpoints import include_endpoint_routers

            root = APIRouter()
            include_endpoint_routers(root)
            print("ROUTES=%d" % len(root.routes))
            """)
        assert blocked.returncode == 0, blocked.stderr
        blocked_routes = int(blocked.stdout.strip().split("=")[1])
        # vision+audio+mobile+trace+plugins always register; drive may or may
        # not (depends on the [google] extra) but its failure never shrinks
        # the surviving bundle.
        assert blocked_routes >= 5
        assert blocked_routes <= natural_routes


# --- Problem 2: encode error attribution + text modality ---


@pytest.fixture
def multimodal_service():
    from services.multimodal_service import MultimodalService

    return MultimodalService()


@pytest.mark.asyncio
class TestEncodeErrorAttributionAndText:
    """問題單 2: honest errors + modality="text" support."""

    async def test_pipeline_error_propagates_not_masked_as_unknown(self, multimodal_service):
        async def _boom(data):
            return {"error": "vision pipeline exploded"}

        multimodal_service._encode_vision = _boom
        out = await multimodal_service.encode(b"png-bytes", "vision")
        assert out.get("error") == "vision pipeline exploded"

    async def test_unsupported_modality_lists_supported_set(self, multimodal_service):
        out = await multimodal_service.encode(b"x", "tactile")
        err = out.get("error", "")
        assert "Unsupported modality" in err
        assert "vision, audio, text" in err

    async def test_text_encode_structural_vector_deterministic(self, multimodal_service):
        out = await multimodal_service.encode(b"hello world", "text")
        assert out.get("error") is None, out.get("error")
        assert out.get("text_encoder") == "structural"
        vec = out.get("feature_vector")
        assert vec is not None and len(vec) == 512
        out2 = await multimodal_service.encode(b"hello world", "text")
        assert list(vec) == list(out2["feature_vector"])
        out3 = await multimodal_service.encode(b"totally different payload xyz", "text")
        assert list(vec) != list(out3["feature_vector"])

    async def test_text_empty_and_invalid_utf8_have_honest_errors(self, multimodal_service):
        empty = await multimodal_service.encode(b"   ", "text")
        assert "text payload is empty" in empty.get("error", "")
        bad = await multimodal_service.encode(b"\xff\xfe\x00", "text")
        assert "UTF-8" in bad.get("error", "")


# --- Problem 3: LLM decision loop JSON-failure cooldown ---


class _FakeLLMService:
    def __init__(self, content: str):
        self.content = content
        self.calls = 0

    async def chat_completion(self, messages):
        self.calls += 1
        return self


class _FakeUserMonitor:
    def get_user_state(self):
        return SimpleNamespace(online=True, emotion="neutral")

    def get_idle_time(self):
        return 0.0

    def detect_return(self):
        return False


def _make_decision_loop(fake_llm):
    from ai.lifecycle.llm_decision_loop import LLMDecisionLoop

    return LLMDecisionLoop(
        llm_service=fake_llm,
        state_manager=None,
        memory_manager=None,
        user_monitor=_FakeUserMonitor(),
    )


@pytest.mark.asyncio
class TestLLMJsonFailureCooldown:
    """問題單 3: streak cooldown, periodic probe, success reset, warn rate."""

    async def test_failure_streak_cooldown_probe_and_recovery(self):
        fake = _FakeLLMService("你好！很高兴见到你！")
        loop = _make_decision_loop(fake)
        first = await loop._generate_decision("d")
        assert isinstance(first, dict) and "action" in first
        assert fake.calls == 1 and loop._json_fail_streak == 1
        await loop._generate_decision("d")
        await loop._generate_decision("d")
        assert fake.calls == 3 and loop._json_fail_streak == 3
        # cooldown: no further LLM calls, still fallback-safe
        await loop._generate_decision("d")
        assert fake.calls == 3 and loop._json_fail_streak == 3
        # probe after the retry window (streak keeps counting)
        loop._last_llm_attempt = time.monotonic() - 601.0
        await loop._generate_decision("d")
        assert fake.calls == 4 and loop._json_fail_streak == 4
        # a parseable reply resets the streak
        fake.content = '{"action": "none", "message": "", "confidence": 0.5}'
        loop._last_llm_attempt = time.monotonic() - 601.0
        out = await loop._generate_decision("d")
        assert out == {"action": "none", "message": "", "confidence": 0.5}
        assert loop._json_fail_streak == 0
        assert fake.calls == 5

    async def test_warnings_rate_limited_to_first_failure(self, caplog):
        import logging

        fake = _FakeLLMService("你好！很高兴见到你！")
        loop = _make_decision_loop(fake)
        with caplog.at_level(logging.WARNING):
            await loop._generate_decision("d")
            first_has_streak_warn = any(
                "streak 1" in rec.message for rec in caplog.records if rec.levelname == "WARNING"
            )
            caplog.clear()
            await loop._generate_decision("d")
            second_streak_warns = any(
                "streak 2" in rec.message for rec in caplog.records if rec.levelname == "WARNING"
            )
        assert first_has_streak_warn
        assert not second_streak_warns


# --- Problem 4: dual-format memory endpoints ---


class _FakeMemoryService:
    async def memory_store(self, item_id):
        return "entry-1" if item_id == "v1" else None

    async def memory_search(self, query_item_id, top_k, modality_filter=None):
        return [{"item": query_item_id, "top_k": top_k}]

    async def memory_recall(self, hours=24):
        return [{"hours": hours}]


@pytest.fixture
def memory_client(monkeypatch):
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from api.routes import multimodal_routes

    monkeypatch.setattr(multimodal_routes, "_SERVICE", _FakeMemoryService())
    app = FastAPI()
    app.include_router(multimodal_routes.router)
    return TestClient(app)


class TestMemoryDualFormatEndpoints:
    """問題單 4: JSON and form bodies both work; clear field-level 422s."""

    def test_json_store_accepted(self, memory_client):
        resp = memory_client.post("/multimodal/memory/store", json={"item_id": "v1"})
        assert resp.status_code == 200
        assert resp.json() == {"success": True, "entry_id": "entry-1"}

    def test_form_store_still_works(self, memory_client):
        resp = memory_client.post("/multimodal/memory/store", data={"item_id": "v1"})
        assert resp.status_code == 200
        assert resp.json()["entry_id"] == "entry-1"

    def test_json_missing_item_id_clear_422(self, memory_client):
        resp = memory_client.post("/multimodal/memory/store", json={})
        assert resp.status_code == 422
        assert "item_id required" in resp.json()["detail"]

    def test_json_search_and_top_k_validation(self, memory_client):
        ok = memory_client.post(
            "/multimodal/memory/search", json={"query_item_id": "v1", "top_k": 2}
        )
        assert ok.status_code == 200
        assert ok.json()["count"] == 1
        bad_type = memory_client.post(
            "/multimodal/memory/search", json={"query_item_id": "v1", "top_k": "bad"}
        )
        assert bad_type.status_code == 422
        assert "top_k" in bad_type.json()["detail"]
        out_of_range = memory_client.post(
            "/multimodal/memory/search", json={"query_item_id": "v1", "top_k": 500}
        )
        assert out_of_range.status_code == 400

    def test_form_search_regression(self, memory_client):
        resp = memory_client.post("/multimodal/memory/search", data={"query_item_id": "v1"})
        assert resp.status_code == 200

    def test_recall_hours_validation_and_success(self, memory_client):
        bad = memory_client.post("/multimodal/memory/recall", json={"hours": "abc"})
        assert bad.status_code == 422
        assert "hours" in bad.json()["detail"]
        ok = memory_client.post("/multimodal/memory/recall", json={"hours": 1.5})
        assert ok.status_code == 200
        assert ok.json()["entries"] == [{"hours": 1.5}]


# --- Problem 6: MetaController persistence + chat calibration sampling ---


class TestMetaCalibrationClosure:
    """問題單 6: throttled persist after mutation + chat feeds calibration."""

    def test_record_confidence_persists_and_throttles(self, tmp_path):
        from ai.meta.meta_controller import MetaController

        path = str(tmp_path / "meta.json")
        ctrl = MetaController(persist_path=path)
        ctrl._last_save_ts = time.monotonic() - 400.0
        ctrl.record_confidence("unit:test", 0.7, correct=True)
        data = __import__("json").loads(Path(path).read_text(encoding="utf-8"))
        assert data["total_samples"] == 1
        assert "unit:test" in data["ewma"]
        # inside the throttle window the file must not be rewritten
        Path(path).write_text("{}", encoding="utf-8")
        ctrl.record_confidence("unit:test", 0.6, correct=False)
        assert Path(path).read_text(encoding="utf-8") == "{}"
        # after the window the next mutation persists again
        ctrl._last_save_ts = time.monotonic() - 400.0
        ctrl.record_confidence("unit:test", 0.5, correct=True)
        data2 = __import__("json").loads(Path(path).read_text(encoding="utf-8"))
        assert data2["total_samples"] == 3

    def test_chat_feedback_records_calibration_sample(self, monkeypatch):
        import api.routes.chat_routes as chat_routes
        import api.routes.meta_routes as meta_routes
        from ai.meta.meta_controller import MetaController

        fresh = MetaController(persist_path=None)
        monkeypatch.setattr(meta_routes, "_META_CONTROLLER", fresh)
        monkeypatch.setattr(
            chat_routes, "_learn_from_classification_feedback", lambda *a, **k: None
        )
        monkeypatch.setattr(chat_routes, "_get_intent_manager", lambda: None)
        context = {"intent_routing": {"routing_mode": "balanced", "intent_strength": 0.8}}
        chat_routes._record_post_response_feedback(context, "A" * 30, "hello")
        assert "chat:intent_routing" in fresh._samples
        assert fresh._ewma["chat:intent_routing"] == pytest.approx(0.8)
        assert fresh._total_samples == 1

    def test_chat_feedback_without_routing_mode_is_noop(self, monkeypatch):
        import api.routes.chat_routes as chat_routes
        import api.routes.meta_routes as meta_routes
        from ai.meta.meta_controller import MetaController

        fresh = MetaController(persist_path=None)
        monkeypatch.setattr(meta_routes, "_META_CONTROLLER", fresh)
        monkeypatch.setattr(
            chat_routes, "_learn_from_classification_feedback", lambda *a, **k: None
        )
        monkeypatch.setattr(chat_routes, "_get_intent_manager", lambda: None)
        chat_routes._record_post_response_feedback({}, "A" * 30, "hello")
        assert fresh._total_samples == 0


# --- Problem 8: Unicode/full-width math detection ---


class TestUnicodeMathDetection:
    """問題單 8: ×÷＋－−／ and simplified 计算 now take the native path."""

    def test_unicode_and_fullwidth_operators_detected(self):
        from services.math_verifier import MathVerifier

        verifier = MathVerifier()
        queries = (
            "请计算 123 × 456",
            "计算 8 ÷ 2",
            "123 － 45",
            "100 ＋ 23",
            "= 5＋3",
        )
        for query in queries:
            assert verifier.is_math_message(query) is True, query

    def test_non_math_still_rejected(self):
        from services.math_verifier import MathVerifier

        verifier = MathVerifier()
        assert verifier.is_math_message("你好吗") is False
        assert verifier.is_math_message("请给我讲个故事") is False

    def test_verify_computes_unicode_operators(self):
        from services.math_verifier import MathVerifier

        verifier = MathVerifier()
        result = verifier.verify("请计算 123 × 456")
        assert result.is_correct is True
        assert "56088" in result.response_text
        result2 = verifier.verify("123 ＋ 45")
        assert result2.is_correct is True
        assert "168" in result2.response_text
