"""ModelBus — central registry + capability routing tests"""


class _MockEngine:
    def __init__(self, response: str = "ok"):
        self.response = response

    async def process(self, query: str, context=None) -> str:
        return self.response


class _MockReflexEngine:
    def __init__(self, response: str = "ok"):
        self.response = response
        self.reflex = _MockReflex()

    async def process(self, query: str, context=None) -> str:
        return self.response


class _MockReflex:
    def __init__(self):
        self.patterns: list = []

    def add_pattern(self, trigger: str, response: str) -> None:
        self.patterns.append((trigger, response))


class TestModelBusRegistration:

    def setup_method(self):
        from ai.core.model_bus import ModelBus, ModelCapability
        self.bus = ModelBus()
        self.ModelCapability = ModelCapability

    def test_register(self):
        engine = _MockEngine()
        cap = self.ModelCapability(tier="test", domain="test", latency_ms=1.0, min_confidence=0.5)
        self.bus.register("test_model", engine, cap)
        stats = self.bus.get_stats()
        assert "test_model" in stats["registered_models"]

    def test_register_ed3n(self):
        engine = _MockEngine()
        self.bus.register_ed3n(engine)
        stats = self.bus.get_stats()
        assert "ed3n" in stats["registered_models"]
        assert stats["capabilities"]["ed3n"]["tier"] == "reflex"

    def test_register_garden(self):
        engine = _MockEngine()
        self.bus.register_garden(engine)
        stats = self.bus.get_stats()
        assert "garden" in stats["registered_models"]
        assert stats["capabilities"]["garden"]["domain"] == "knowledge"

    def test_register_cloud(self):
        engine = _MockEngine()
        self.bus.register_cloud(engine)
        stats = self.bus.get_stats()
        assert "cloud" in stats["registered_models"]
        assert stats["capabilities"]["cloud"]["tier"] == "cloud"

    def test_register_cloud_wraps_backend_without_process(self):
        class BackendWithGenerate:
            def __init__(self):
                self.called = False

            async def generate(self, query: str, context=None):
                self.called = True
                from core.interfaces.protocols import LLMResponse
                return LLMResponse(text="generated", confidence=0.9)

        backend = BackendWithGenerate()
        self.bus.register_cloud(backend)
        stats = self.bus.get_stats()
        assert "cloud" in stats["registered_models"]

    def test_get_stats_empty(self):
        stats = self.bus.get_stats()
        assert stats["registered_models"] == []
        assert stats["capabilities"] == {}


class TestModelBusDomainQueries:

    def setup_method(self):
        from ai.core.model_bus import ModelBus, ModelCapability
        self.bus = ModelBus()
        self.ModelCapability = ModelCapability
        self.bus.register("model_a", _MockEngine("a"), ModelCapability("t1", "reflex", 1.0, 0.9))
        self.bus.register("model_b", _MockEngine("b"), ModelCapability("t1", "knowledge", 10.0, 0.7))
        self.bus.register("model_c", _MockEngine("c"), ModelCapability("t2", "knowledge", 20.0, 0.6))

    def test_get_models_for_domain(self):
        models = self.bus.get_models_for_domain("knowledge")
        assert "model_b" in models
        assert "model_c" in models
        assert "model_a" not in models

    def test_get_models_for_domain_empty(self):
        models = self.bus.get_models_for_domain("nonexistent")
        assert models == []

    def test_get_training_assignment_returns_first_registered(self):
        model = self.bus.get_training_assignment("knowledge")
        assert model == "model_b"

    def test_get_training_assignment_none(self):
        model = self.bus.get_training_assignment("nonexistent")
        assert model is None


class TestModelBusResolveCandidates:

    def setup_method(self):
        from ai.core.model_bus import ModelBus, ModelCapability
        self.bus = ModelBus()
        self.ModelCapability = ModelCapability
        self.bus.register("ed3n", _MockEngine(), ModelCapability("reflex", "reflex", 0.1, 0.95))
        self.bus.register("garden", _MockEngine(), ModelCapability("lightweight", "knowledge", 10.0, 0.7))
        self.bus.register("cloud", _MockEngine(), ModelCapability("cloud", "creative", 500.0, 0.6))

    def test_resolve_reflex(self):
        candidates = self.bus._resolve_candidates("reflex")
        assert candidates == ["ed3n"]

    def test_resolve_math(self):
        candidates = self.bus._resolve_candidates("math")
        assert candidates == ["ed3n", "garden"]

    def test_resolve_knowledge(self):
        candidates = self.bus._resolve_candidates("knowledge")
        assert candidates == ["garden", "cloud"]

    def test_resolve_creative(self):
        candidates = self.bus._resolve_candidates("creative")
        assert candidates == ["cloud"]

    def test_resolve_unknown_type_returns_all(self):
        candidates = self.bus._resolve_candidates("unknown")
        assert set(candidates) == {"ed3n", "garden", "cloud"}

    def test_resolve_unregistered_model_skipped(self):
        self.bus._registry.pop("ed3n", None)
        candidates = self.bus._resolve_candidates("reflex")
        assert candidates == []


class TestModelBusPickBest:

    def test_pick_best_highest_confidence(self):
        from ai.core.model_bus import ModelRouteResult, ModelBus
        r1 = ModelRouteResult("a", "text", 0.5, 10.0, "x")
        r2 = ModelRouteResult("b", "text", 0.9, 10.0, "x")
        best = ModelBus._pick_best({"a": r1, "b": r2})
        assert best["model_id"] == "b"
        assert best["confidence"] == 0.9

    def test_pick_best_empty_returns_none(self):
        from ai.core.model_bus import ModelBus
        best = ModelBus._pick_best({})
        assert best["model_id"] == "none"

    def test_pick_best_single(self):
        from ai.core.model_bus import ModelRouteResult, ModelBus
        r = ModelRouteResult("a", "text", 0.7, 10.0, "x")
        best = ModelBus._pick_best({"a": r})
        assert best["model_id"] == "a"


class TestModelBusInjectPattern:

    def test_inject_pattern_with_reflex_add_pattern(self):
        from ai.core.model_bus import ModelBus
        engine = _MockReflexEngine()
        result = ModelBus._inject_pattern(engine, "hello", "world")
        assert result is True
        assert engine.reflex.patterns == [("hello", "world")]

    def test_inject_pattern_no_reflex(self):
        from ai.core.model_bus import ModelBus
        engine = _MockEngine()
        result = ModelBus._inject_pattern(engine, "hello", "world")
        assert result is False

    def test_sync_knowledge_syncs_patterns(self):
        from ai.core.model_bus import ModelBus, ModelCapability
        bus = ModelBus()
        source = _MockReflexEngine("source")
        target = _MockReflexEngine("target")
        cap = ModelCapability("t", "d", 1.0, 0.5)
        bus.register("src", source, cap)
        bus.register("tgt", target, cap)
        count = bus.sync_knowledge("src", "tgt", [("a", "1"), ("b", "2")])
        assert count == 2
        assert target.reflex.patterns == [("a", "1"), ("b", "2")]

    def test_sync_knowledge_unknown_model(self):
        from ai.core.model_bus import ModelBus, ModelCapability
        bus = ModelBus()
        target = _MockReflexEngine("t")
        bus.register("tgt", target, ModelCapability("t", "d", 1.0, 0.5))
        count = bus.sync_knowledge("unknown", "tgt", [("a", "1")])
        assert count == 0


class TestModelBusRouting:

    def setup_method(self):
        from ai.core.model_bus import ModelBus, ModelCapability
        self.bus = ModelBus()
        self.ModelCapability = ModelCapability

    def register_all(self):
        self.bus.register("ed3n", _MockEngine("reflex_response"), self.ModelCapability("reflex", "reflex", 0.1, 0.95))
        self.bus.register("garden", _MockEngine("garden_response"), self.ModelCapability("lightweight", "knowledge", 10.0, 0.7))
        self.bus.register("cloud", _MockEngine("cloud_response"), self.ModelCapability("cloud", "creative", 500.0, 0.6))

    async def test_route_reflex(self):
        self.register_all()
        decision = await self.bus.route("hello", "reflex")
        assert decision.selected_model == "ed3n"
        assert decision.results["ed3n"].text == "reflex_response"
        assert decision.confidence == 0.95

    async def test_route_greeting(self):
        self.register_all()
        decision = await self.bus.route("hi", "greeting")
        assert decision.selected_model == "ed3n"

    async def test_route_math_ed3n_high_confidence(self):
        self.register_all()
        decision = await self.bus.route("1+1", "math")
        assert "ed3n" in decision.results

    async def test_route_knowledge(self):
        self.register_all()
        decision = await self.bus.route("what is x", "knowledge")
        assert "garden" in decision.results

    async def test_route_creative(self):
        self.register_all()
        decision = await self.bus.route("write a poem", "creative")
        assert decision.selected_model == "cloud"

    async def test_route_general_fanout(self):
        self.register_all()
        decision = await self.bus.route("do something", "general")
        assert len(decision.results) >= 1

    async def test_route_empty_registry(self):
        decision = await self.bus.route("hello", "reflex")
        assert decision.results["ed3n"].error is not None
        assert decision.confidence == 0.0
        assert "not registered" in (decision.results["ed3n"].error or "")

    async def test_route_unregistered_model_type(self):
        self.bus.register("ed3n", _MockEngine(), self.ModelCapability("reflex", "reflex", 0.1, 0.95))
        decision = await self.bus.route("test", "creative")
        assert "cloud" in decision.results
        assert "not registered" in (decision.results["cloud"].error or "")

    async def test_route_engine_exception(self):
        class _CrashEngine:
            async def process(self, query: str, context=None) -> str:
                msg = "engine crashed"
                raise RuntimeError(msg)

        self.bus.register("ed3n", _CrashEngine(), self.ModelCapability("reflex", "reflex", 0.1, 0.95))
        decision = await self.bus.route("hello", "reflex")
        assert decision.results["ed3n"].error is not None
        assert decision.confidence == 0.0

    async def test_route_timeout(self):
        class _SlowEngine:
            async def process(self, query: str, context=None) -> str:
                import asyncio
                await asyncio.sleep(100)
                return "too late"

        self.bus.default_timeout = 0.01
        self.bus.register("ed3n", _SlowEngine(), self.ModelCapability("reflex", "reflex", 0.1, 0.95))
        decision = await self.bus.route("hello", "reflex")
        assert "Timeout" in (decision.results["ed3n"].error or "")

    async def test_route_knowledge_cloud_fallback(self):
        class _LowConfEngine:
            async def process(self, query: str, context=None) -> str:
                return ""

        self.bus.register("garden", _LowConfEngine(), self.ModelCapability("lightweight", "knowledge", 10.0, 0.7))
        self.bus.register("cloud", _MockEngine("fallback"), self.ModelCapability("cloud", "creative", 500.0, 0.6))
        decision = await self.bus.route("knowledge query", "knowledge")
        assert "cloud" in decision.results
