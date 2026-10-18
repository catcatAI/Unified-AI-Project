"""Gate 捷徑記憶落地（#2）＋ web-search 稽核端點（#7）— audit 2026-10-18。

研究結果原先只活在 RAM TTL session＋眼前的回應 JSON：
/context/memory/recent 對 gate 研究查詢 grep=0（普通對話有存）——gate 在
generate_response 之前 return，跳過 _store_interaction_memories。
"""

import asyncio
from types import SimpleNamespace


class FakeVecStore:
    def __init__(self):
        self.added = []

    async def add_memory(self, memory_id, content, metadata):
        self.added.append((memory_id, content, metadata))


class FakeMemoryManager:
    def __init__(self):
        self.stored = []

    async def store_experience(self, *, raw_data, data_type, metadata):
        self.stored.append((raw_data, data_type, metadata))


def _bare_chat_service(vector_store=None, enable_mm=False, memory_manager=None):
    from services.chat_service import ChatService

    svc = object.__new__(ChatService)
    svc._vector_store = vector_store
    svc._llm_service = SimpleNamespace(
        enable_memory_enhancement=enable_mm, memory_manager=memory_manager
    )
    svc._background_tasks = set()
    return svc


class TestStoreGateInteraction:
    def test_vector_store_receives_conversation(self):
        vec = FakeVecStore()
        svc = _bare_chat_service(vector_store=vec)

        async def run():
            await svc.store_gate_interaction(
                "幫我調查 Brave Search API", "「Brave」的搜尋結果：\n• T — https://a.example"
            )
            await asyncio.sleep(0)  # let fire-and-forget tasks drain

        asyncio.run(run())
        assert len(vec.added) == 1
        _mid, content, metadata = vec.added[0]
        assert "幫我調查 Brave Search API" in content
        assert "https://a.example" in content
        assert metadata == {"type": "conversation"}

    def test_memory_manager_when_enhancement_on(self):
        mm = FakeMemoryManager()
        svc = _bare_chat_service(vector_store=None, enable_mm=True, memory_manager=mm)

        async def run():
            await svc.store_gate_interaction("研究 X", "結果 Y")
            await asyncio.sleep(0)

        asyncio.run(run())
        assert len(mm.stored) == 1
        raw_data, data_type, _meta = mm.stored[0]
        assert raw_data == {"user": "研究 X", "assistant": "結果 Y"}
        assert data_type == "conversation"

    def test_empty_response_is_noop(self):
        vec = FakeVecStore()
        svc = _bare_chat_service(vector_store=vec)
        asyncio.run(svc.store_gate_interaction("q", ""))
        assert vec.added == []

    def test_store_method_shares_persist_path_with_generate(self):
        vec = FakeVecStore()
        svc = _bare_chat_service(vector_store=vec)
        resp = SimpleNamespace(text="hello")
        asyncio.run(svc._store_interaction_memories("hi", resp))
        asyncio.run(svc.store_gate_interaction("hi", "hello"))
        assert len(vec.added) == 2
        assert vec.added[0][1] == vec.added[1][1]


class TestPersistGateInteractionHelper:
    def test_calls_service_store(self):
        from api.routes.chat_routes import _persist_gate_interaction

        calls = []

        async def fake_store(user_message, response_text, context):
            calls.append((user_message, response_text, context))

        chat_svc = SimpleNamespace(store_gate_interaction=fake_store)
        asyncio.run(_persist_gate_interaction("q", "r", chat_svc, {"k": "v"}))
        assert calls == [("q", "r", {"k": "v"})]

    def test_none_chat_svc_noop(self):
        from api.routes.chat_routes import _persist_gate_interaction

        asyncio.run(_persist_gate_interaction("q", "r", None, {}))

    def test_missing_method_noop(self):
        from api.routes.chat_routes import _persist_gate_interaction

        asyncio.run(_persist_gate_interaction("q", "r", SimpleNamespace(), {}))

    def test_exception_swallowed_with_warning(self, caplog):
        from api.routes.chat_routes import _persist_gate_interaction

        async def boom(user_message, response_text, context):
            raise RuntimeError("memory down")

        chat_svc = SimpleNamespace(store_gate_interaction=boom)
        # 不擋回應路徑：不 raise
        asyncio.run(_persist_gate_interaction("q", "r", chat_svc, {}))


class TestResearchLLMSynthesis:
    """gate web_search 的 AI 歸納環：LLM 成文＋來源不丟；失敗降級抽取式。"""

    MATERIAL = (
        "「q」的搜尋結果（研究摘要：1/1 頁內文）：\n"
        "【關鍵事實】\n• Free tier is 2,000 queries per month.\n"
        "【來源（按可信度）】\n1. [高] Official — https://x.example/p"
    )

    def test_synthesis_applied_and_sources_kept(self):
        from api.routes.chat_routes import _synthesize_research_response

        async def fake_gen(*, prompt, max_tokens, temperature, system_prompt):
            assert "研究問題" in prompt and "Free tier" in prompt
            assert temperature == 0.2
            return (
                "綜合多個來源後：Brave Search API 的免費額度為每月 2,000 次查詢，"
                "超過後按每千次 3 USD 計價；DuckDuckGo 未提供公開搜尋 API。"
                "以上結論僅基於已抓取的來源材料。"
            )

        chat_svc = SimpleNamespace(generate_text=fake_gen)
        out = asyncio.run(_synthesize_research_response("q", self.MATERIAL, chat_svc))
        # LLM 沒帶來源 → 從材料補回
        assert "免費額度為每月 2,000 次查詢" in out
        assert "【來源（按可信度）】" in out
        assert "https://x.example/p" in out

    def test_synthesis_keeps_llm_sources_when_present(self):
        from api.routes.chat_routes import _synthesize_research_response

        llm_out = "綜合結論……\n【來源】\n1. [高] Official — https://y.example/p"

        async def fake_gen(*, prompt, max_tokens, temperature, system_prompt):
            return llm_out

        chat_svc = SimpleNamespace(generate_text=fake_gen)
        out = asyncio.run(_synthesize_research_response("q", self.MATERIAL, chat_svc))
        assert out == llm_out  # 不重複附加

    def test_no_llm_falls_back_to_material(self):
        from api.routes.chat_routes import _synthesize_research_response

        assert (
            asyncio.run(_synthesize_research_response("q", self.MATERIAL, SimpleNamespace()))
            == self.MATERIAL
        )

    def test_llm_exception_falls_back(self):
        from api.routes.chat_routes import _synthesize_research_response

        async def boom(*, prompt, max_tokens, temperature, system_prompt):
            raise RuntimeError("model down")

        chat_svc = SimpleNamespace(generate_text=boom)
        out = asyncio.run(_synthesize_research_response("q", self.MATERIAL, chat_svc))
        assert out == self.MATERIAL

    def test_short_llm_output_falls_back(self):
        from api.routes.chat_routes import _synthesize_research_response

        async def tiny(*, prompt, max_tokens, temperature, system_prompt):
            return "ok"

        chat_svc = SimpleNamespace(generate_text=tiny)
        out = asyncio.run(_synthesize_research_response("q", self.MATERIAL, chat_svc))
        assert out == self.MATERIAL


class TestWebSearchHistoryEndpoint:
    def test_history_endpoint_reads_tail(self, monkeypatch):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import core.tools.web_search_tool as wst

        fake = [{"query": "q1", "provider": "duckduckgo", "n_results": 2, "urls": []}]
        monkeypatch.setattr(wst, "read_recent_history", lambda limit=20: fake)

        from api.routes.web_search_routes import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        client = TestClient(app)
        resp = client.get("/api/v1/web-search/history?limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["count"] == 1
        assert body["history"][0]["query"] == "q1"

    def test_history_endpoint_swallows_errors(self, monkeypatch):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import core.tools.web_search_tool as wst

        def _boom(limit=20):
            raise OSError("disk gone")

        monkeypatch.setattr(wst, "read_recent_history", _boom)

        from api.routes.web_search_routes import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        client = TestClient(app)
        resp = client.get("/api/v1/web-search/history")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is False
        assert body["history"] == []
