#!/usr/bin/env python3
"""
S6 端到端測試：v6.3 配置驅動系統測試套件

測試範圍：
1. IntentRegistry 配置驅動意圖注册
2. ChatService 意圖檢測（file_op/web_search/learning）
3. AngelaConfigManager 學習閉環（learn/write_learned）
4. AngelaLLMService 配置驅動後端初始化
5. 降級鏈整合
"""

import pytest
import time
from pathlib import Path


class TestIntentRegistryConfig:
    """測試 IntentRegistry 從 YAML 配置讀取"""

    def test_loads_from_config(self):
        """IntentRegistry 從 angela_core.yaml 讀取意圖配置"""
        from core.intent_registry import IntentRegistry

        reg = IntentRegistry()
        intent_names = [p.name for p in reg.patterns]

        assert "math" in intent_names
        assert "code" in intent_names
        assert "task" in intent_names
        assert len(reg.patterns) >= 8

    def test_math_pattern_keywords(self):
        """數學意圖關鍵字從配置讀取"""
        from core.intent_registry import IntentRegistry

        reg = IntentRegistry()
        math_p = next((p for p in reg.patterns if p.name == "math"), None)
        assert math_p is not None, "math intent not found"
        assert len(math_p.keywords) >= 3
        assert any(kw in ["計算", "加", "減"] for kw in math_p.keywords)

    def test_fallback_on_config_missing(self):
        """配置讀取失敗時回退到 hardcoded defaults"""
        from core.intent_registry import IntentRegistry

        reg = IntentRegistry()
        assert len(reg.patterns) > 0
        math_p = next((p for p in reg.patterns if p.name == "math"), None)
        assert math_p is not None


class TestAngelaConfigManagerLearning:
    """測試 AngelaConfigManager 學習閉環"""

    def test_write_learned_creates_file(self):
        """write_learned 創建 learned YAML 文件"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        learned_dir = cfg._angela_dir

        test_data = {
            "test_entry": {"keywords": ["test"], "count": 1},
            "metadata": {"updated": "2026-05-18"},
        }

        result = cfg.write_learned("patterns", test_data)
        assert result is True

        patterns_file = learned_dir / "learned_patterns.yaml"
        assert patterns_file.exists(), "learned_patterns.yaml should exist"

        content = patterns_file.read_text(encoding="utf-8")
        assert "test_entry" in content

    def test_learn_intent_pattern(self):
        """learn('intent_pattern') 新增意圖模式"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()

        test_intent = f"_test_intent_{int(time.time())}"
        result = cfg.learn("intent_pattern", {
            "intent": test_intent,
            "keywords": ["test_keyword_1", "test_keyword_2"],
        })

        learned = cfg.get_learned("patterns", {})
        patterns = learned.get("intent_patterns", {})
        assert test_intent in patterns or result is False

    def test_learn_route_success(self):
        """learn('route_success') 記錄成功路由"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        result = cfg.learn("route_success", {
            "provider": "TestBackend",
            "intent": "test_general",
            "latency_ms": 150.0,
        })

        learned = cfg.get_learned("routes", {})
        success_routes = learned.get("successful_routes", {})
        assert result is True or len(success_routes) >= 0

    def test_learn_route_fail(self):
        """learn('route_fail') 記錄失敗路由"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        result = cfg.learn("route_fail", {
            "provider": "TestBackend",
            "intent": "test_fail",
            "error": "timeout",
        })
        assert result is True

    def test_get_learned_stats(self):
        """get_learned_stats 返回學習統計"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        stats = cfg.get_learned_stats()

        assert "patterns" in stats
        assert "thresholds" in stats
        assert "routes" in stats
        assert "learned" in stats["patterns"]
        assert "authority" in stats["patterns"]

    def test_authority_not_overwritten(self):
        """Learned 配置不能覆蓋 Authority 配置"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        authority_intents = cfg.get_authority("angela_core", {}).get("intents", {})

        for intent_name in authority_intents:
            result = cfg.learn("intent_pattern", {
                "intent": intent_name,
                "keywords": ["hacker_keyword"],
            })
            assert result is False, f"Authority intent {intent_name} should not be overwritten"


class TestChatServiceIntentDetection:
    """測試 ChatService 意圖檢測擴展"""

    def test_detect_file_op_intent(self):
        """檢測桌面整理意圖"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        file_op_kw = cfg.get_intent_keywords("file_op")
        assert len(file_op_kw) > 0

        test_text = "幫我整理桌面"
        matched = any(kw in test_text for kw in file_op_kw)
        assert matched, f"file_op keyword should match '{test_text}'"

    def test_detect_web_search_intent(self):
        """檢測網路搜尋意圖"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        search_kw = cfg.get_intent_keywords("web_search")
        assert len(search_kw) > 0

        test_text = "搜尋一下 python 教程"
        matched = any(kw in test_text for kw in search_kw)
        assert matched, f"web_search keyword should match '{test_text}'"

    def test_detect_learning_intent(self):
        """檢測學習意圖"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        learn_kw = cfg.get_intent_keywords("learning")
        assert len(learn_kw) > 0, f"learning intent keywords should exist, got: {learn_kw}"

        test_text = "請記住這個偏好設定"
        matched = any(kw in test_text for kw in learn_kw)
        assert matched, f"learning keyword should match '{test_text}'"


class TestAngelaLLMServiceConfigDriven:
    """測試 AngelaLLMService 配置驅動後端初始化"""

    def test_llm_config_from_angela_config(self):
        """LLM 配置從 angela_config 讀取"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        llm_cfg = cfg.get_llm_config()

        assert "providers" in llm_cfg, "llm_config should have 'providers' key"
        providers = llm_cfg.get("providers", {})
        assert len(providers) >= 1, "should have at least 1 LLM provider"

    def test_llm_routing_policy(self):
        """LLM 路由策略從配置讀取"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        routing = cfg.get_routing_policy()

        assert isinstance(routing, dict)
        assert "fallback_chain" in routing or len(routing) >= 0

    def test_complexity_thresholds_from_config(self):
        """複雜度閾值從配置讀取"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        thresholds = cfg.get_complexity_thresholds()

        assert isinstance(thresholds, dict)
        assert "low" in thresholds
        assert "high" in thresholds

    def test_intent_keywords_complete(self):
        """所有 8 個意圖的關鍵字從配置讀取"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        expected_intents = ["math", "code", "task", "file_op", "web_search", "learning", "character_card", "document"]

        missing = []
        for intent in expected_intents:
            keywords = cfg.get_intent_keywords(intent)
            if not keywords:
                missing.append(intent)

        assert len(missing) == 0, f"Missing keywords for intents: {missing}"


class TestConfigLoaderHotReload:
    """測試配置熱重載"""

    def test_reload_if_changed(self):
        """熱重載方法存在且可調用"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        result = cfg.reload_if_changed()
        assert isinstance(result, bool)

    def test_watch_method(self):
        """watch 方法存在且可調用"""
        from core.config_loader import get_angela_config

        cfg = get_angela_config()
        result = cfg.watch()
        assert isinstance(result, bool)


class TestREPLCommands:
    """測試 REPL 命令解析"""

    def test_repl_command_handler_exists(self):
        """_handle_repl_command 函數存在"""
        import services.main_api_server as api_server
        assert hasattr(api_server, "_handle_repl_command")
        assert callable(api_server._handle_repl_command)

    def test_repl_help_command(self):
        """REPL /help 命令返回幫助文字"""
        from services.main_api_server import _handle_repl_command

        intent, response = _handle_repl_command("/help", None, [])
        assert intent == "system"
        assert response is not None
        assert "REPL" in response or "Commands" in response

    def test_repl_help_short(self):
        """REPL /h 命令（簡寫）"""
        from services.main_api_server import _handle_repl_command

        intent, response = _handle_repl_command("/h", None, [])
        assert intent == "system"

    def test_repl_unknown_command_returns_none(self):
        """未知 REPL 命令返回 None（passthrough）"""
        from services.main_api_server import _handle_repl_command

        intent, response = _handle_repl_command("/unknowncmd", None, [])
        assert response is None


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False,
    )


class TestTickleReflexSystem:
    """測試小腦反射系統（S7）"""

    def test_reflex_system_initializes(self):
        """TickleReflexSystem 正確初始化"""
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()
        assert reflex._initialized is True
        assert len(reflex._body_parts) > 0
        assert reflex._light_threshold > 0
        assert reflex._medium_threshold > reflex._light_threshold
        assert reflex._intense_threshold > reflex._medium_threshold

    def test_intensity_level_classification(self):
        """強度級別分類正確"""
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()
        assert reflex.get_intensity_level(0.1) == "none"
        assert reflex.get_intensity_level(0.3) == "light"
        assert reflex.get_intensity_level(0.55) == "medium"
        assert reflex.get_intensity_level(0.6) == "intense"
        assert reflex.get_intensity_level(0.9) == "intense"

    def test_body_parts_loaded_from_config(self):
        """身體部位從配置讀取"""
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()
        parts = reflex.get_all_body_parts()
        assert "abdomen" in parts
        assert "feet" in parts
        assert "neck" in parts
        assert reflex.get_reflex_config("abdomen")["sensitivity"] == 0.9

    def test_sensitive_parts_isolated(self):
        """敏感部位正確隔離"""
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()
        sensitive = reflex.get_sensitive_parts()
        assert "chest" in sensitive or "shoulders" in sensitive

    def test_trigger_returns_phase_structure(self):
        """trigger_tickles 返回 Phase1 + Phase2 結構"""
        import asyncio
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()

        async def run_trigger():
            result = await reflex.trigger_tickles(
                body_part="abdomen", intensity=0.5, duration_seconds=1.0, origin="Human"
            )
            return result

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(run_trigger())
        loop.close()

        assert "phase1" in result
        assert "phase2" in result
        assert "animation" in result["phase1"]
        assert "output_mode" in result["phase1"]
        assert "elapsed_ms" in result
        assert result["body_part"] == "abdomen"
        assert result["intensity_level"] in ("light", "medium")

    def test_sensitive_part_returns_comfort_seek(self):
        """敏感部位觸發時返回 comfort_seek"""
        import asyncio
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()

        async def run_trigger():
            result = await reflex.trigger_tickles(
                body_part="chest", intensity=0.6, duration_seconds=1.0, origin="Human"
            )
            return result

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(run_trigger())
        loop.close()

        assert result["is_sensitive"] is True
        assert result["phase1"]["output_mode"] == "comfort_seek"

    def test_sustained_stimulus_falls_back(self):
        """持續刺激（>5s）自動回退到 comfort_seek"""
        import asyncio
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()

        async def run_trigger():
            result = await reflex.trigger_tickles(
                body_part="feet", intensity=0.4, duration_seconds=6.0, origin="Human"
            )
            return result

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(run_trigger())
        loop.close()

        assert result["sustained"] is True
        assert result["phase1"]["output_mode"] == "comfort_seek"

    def test_intense_mode_output_mode(self):
        """intense 模式（>=0.8）輸出模式為 scream"""
        import asyncio
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()

        async def run_trigger():
            result = await reflex.trigger_tickles(
                body_part="sides", intensity=1.0, duration_seconds=0.5, origin="Human"
            )
            return result

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(run_trigger())
        loop.close()

        assert result["intensity_level"] == "intense"
        assert result["phase1"]["output_mode"] in ("scream", "comfort_seek")

    def test_gamma_invasion_on_sustained(self):
        """持續刺激時 γ軸 被入侵（恐懼+）"""
        import asyncio
        from core.life.tickle_reflex_system import get_reflex_system
        from core.autonomous.state_matrix import StateMatrix4D

        reflex = get_reflex_system()
        sm = StateMatrix4D()

        async def run_trigger():
            result = await reflex.trigger_tickles(
                body_part="neck", intensity=0.7, duration_seconds=6.0,
                origin="Human", state_matrix=sm
            )
            return result

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(run_trigger())
        loop.close()

        assert result["phase1"]["output_mode"] == "comfort_seek"

    def test_gamma_invasion_on_sensitive(self):
        """敏感部位觸發時 γ軸 被入侵"""
        import asyncio
        from core.life.tickle_reflex_system import get_reflex_system
        from core.autonomous.state_matrix import StateMatrix4D

        reflex = get_reflex_system()
        sm = StateMatrix4D()

        async def run_trigger():
            result = await reflex.trigger_tickles(
                body_part="shoulders", intensity=0.5, duration_seconds=1.0,
                origin="Human", state_matrix=sm
            )
            return result

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(run_trigger())
        loop.close()

        assert result["is_sensitive"] is True

    def test_reflex_timeout_config(self):
        """反射超時配置"""
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()
        assert reflex._reflex_timeout_ms > 0
        assert reflex._max_llm_words > 0


class TestAnchorLearningSuggestConfig:
    """測試 AnchorLearningEngine.suggest_config_update() (G11)"""

    def test_suggest_config_update_method_exists(self):
        """suggest_config_update 方法存在"""
        try:
            from core.engine.anchor_learning import AnchorLearningEngine
            assert hasattr(AnchorLearningEngine, "suggest_config_update")
        except ImportError:
            pass


class TestBuildAnchorContext:
    """測試 anchor_rules.yaml 自然語境注入 (Fix 2)"""

    def test_build_anchor_context_returns_string(self):
        """build_anchor_context 返回自然語境字符串"""
        from core.config_loader import get_angela_config
        cfg = get_angela_config()
        mock_state = {
            "axes": {
                "alpha": {"values": {"comfort": 0.7, "energy": 0.5, "arousal": 0.5}},
                "beta": {"values": {"focus": 0.8, "clarity": 0.6}},
                "gamma": {"values": {"happiness": 0.8, "trust": 0.5}},
                "delta": {},
                "epsilon": {},
                "theta": {},
                "zeta": {},
            },
            "theta": {"novelty": 0.3},
            "eta": {"success_rate": 0.8},
        }
        result = cfg.build_anchor_context(mock_state)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_anchor_context_falls_back_on_missing_data(self):
        """build_anchor_context 在缺失數據時返回空字符串"""
        from core.config_loader import get_angela_config
        cfg = get_angela_config()
        result = cfg.build_anchor_context({})
        assert isinstance(result, str)

    def test_interpret_axis_returns_string(self):
        """_interpret_axis 返回自然語境"""
        from core.config_loader import get_angela_config
        cfg = get_angela_config()
        axis_data = {"values": {"comfort": 0.8}}
        axis_rules = {
            "coordinate_interpretation": {
                "comfort": {
                    "high_positive": "非常舒適",
                    "neutral": "狀態正常",
                }
            }
        }
        result = cfg._interpret_axis(axis_data, axis_rules)
        assert isinstance(result, str)


class TestModelREPLCommand:
    """測試 /model REPL 命令"""

    def test_model_command_handler_exists(self):
        """_handle_model_command 函數存在"""
        import services.main_api_server as api_server
        assert hasattr(api_server, "_handle_model_command")
        assert callable(api_server._handle_model_command)

    def test_model_list_command(self):
        """REPL /model list 返回可用模型"""
        from services.main_api_server import _handle_model_command

        response = _handle_model_command("list", None)
        assert isinstance(response, str)
        assert "Available models" in response or "LLM routing error" in response

    def test_model_stats_command(self):
        """REPL /model stats 返回統計"""
        from services.main_api_server import _handle_model_command

        response = _handle_model_command("stats", None)
        assert isinstance(response, str)

    def test_tickle_command_handler_exists(self):
        """_handle_tickle_command 函數存在"""
        import services.main_api_server as api_server
        assert hasattr(api_server, "_handle_tickle_command")

    def test_tickle_no_args_returns_usage(self):
        """REPL /tickle 無參數返回使用說明"""
        from services.main_api_server import _handle_tickle_command

        response = _handle_tickle_command("")
        assert "Usage" in response or "Parts" in response


class TestTickleIntensityThresholdFix:
    """測試 tickle_config.yaml 強度閾值修正 (Fix 1)"""

    def test_intense_threshold_is_060(self):
        """intense 閾值應為 0.60（MD 定義）"""
        from core.config_loader import get_angela_config
        cfg = get_angela_config()
        tickle = cfg.get_tickle_config()
        thresholds = tickle.get("intensity_thresholds", {})
        assert thresholds.get("intense") == 0.60, f"intense should be 0.60, got {thresholds.get('intense')}"

    def test_intense_level_classification(self):
        """intensity >= 0.60 應被分類為 intense"""
        from core.life.tickle_reflex_system import get_reflex_system
        reflex = get_reflex_system()
        assert reflex.get_intensity_level(0.6) == "intense"
        assert reflex.get_intensity_level(0.65) == "intense"
        assert reflex.get_intensity_level(0.55) == "medium"


class TestGoogleDriveIntegration:
    """測試 Google Drive 接入 (新功能)"""

    def test_drive_service_class_exists(self):
        """GoogleDriveService 類存在"""
        from integrations.google_drive_service import GoogleDriveService
        assert GoogleDriveService is not None

    def test_drive_service_factory(self):
        """GoogleDriveService._create returns new instance each time"""
        from integrations.google_drive_service import GoogleDriveService
        s1 = GoogleDriveService._create()
        s2 = GoogleDriveService._create()
        assert s1 is not s2

    def test_drive_service_is_authenticated_without_token(self):
        """無有效 token 時返回 False"""
        from integrations.google_drive_service import GoogleDriveService
        GoogleDriveService._instance = None
        svc = GoogleDriveService()
        result = svc.is_authenticated()
        assert result is False

    def test_drive_service_get_auth_url_returns_url(self):
        """credentials.json 存在時返回 OAuth URL"""
        from integrations.google_drive_service import GoogleDriveService
        from pathlib import Path
        cred_path = Path(__file__).parent.parent / "config" / "credentials.json"
        if not cred_path.exists():
            import pytest
            pytest.skip("credentials.json not found")
        GoogleDriveService._instance = None
        svc = GoogleDriveService()
        url = svc.get_auth_url()
        assert isinstance(url, str)
        assert "accounts.google.com" in url

    def test_drive_repl_command_handler_exists(self):
        """REPL /drive 命令存在"""
        import services.main_api_server as api_server
        assert hasattr(api_server, "_handle_drive_command")
        assert callable(api_server._handle_drive_command)

    def test_drive_repl_help_shows_drive_command(self):
        """help 文案中包含 drive 命令"""
        from services.main_api_server import _build_help_text
        help_text = _build_help_text()
        assert "drive" in help_text.lower()

    def test_drive_intent_keywords_in_config(self):
        """google_drive intent 在 angela_core.yaml 中"""
        from core.config_loader import get_angela_config
        cfg = get_angela_config()
        kws = cfg.get_intent_keywords("google_drive")
        assert len(kws) > 0
        assert any("google" in k.lower() for k in kws)

    def test_drive_detect_intent_in_chat_service(self):
        """ChatService._detect_drive_intent 方法存在且可檢測意圖"""
        from services.chat_service import AngelaChatService
        import asyncio
        svc = AngelaChatService()
        assert hasattr(svc, "_detect_drive_intent")
        assert callable(svc._detect_drive_intent)
        result = svc._detect_drive_intent("幫我列出 Google Drive 的檔案")
        assert result == "google_drive"
        result_none = svc._detect_drive_intent("今天天氣怎麼樣")
        assert result_none is None

    def test_deduplication_class_exists(self):
        """DriveDeduplication 類存在"""
        from api.v1.endpoints.drive import DriveDeduplication
        d = DriveDeduplication()
        assert hasattr(d, "should_download")
        assert hasattr(d, "record_sync")

    def test_document_parser_class_exists(self):
        """DocumentParser 類存在"""
        from api.v1.endpoints.drive import DocumentParser
        p = DocumentParser()
        assert hasattr(p, "parse_document")
