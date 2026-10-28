# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""P1-4: ChatService forwards the role namespace into recall and storage."""

from services.chat_service import ChatService


class FakeVectorStore:
    def __init__(self):
        self.searches = []
        self.writes = []

    async def semantic_search(self, query, limit=10, where_document=None, namespace=None):
        self.searches.append({"query": query, "namespace": namespace})
        return {"documents": [["a doc"]], "distances": [[0.1]]}

    async def add_memory(self, memory_id, content, metadata=None, namespace=None):
        self.writes.append({"id": memory_id, "metadata": metadata, "namespace": namespace})


class FakeMemoryManager:
    def __init__(self):
        self.calls = []

    async def store_experience(self, **kwargs):
        self.calls.append(kwargs)


class FakeLLM:
    def __init__(self, memory_manager=None):
        self.enable_memory_enhancement = memory_manager is not None
        self.memory_manager = memory_manager


def bare_service():
    svc = object.__new__(ChatService)
    svc._vector_store_backoff_until = 0.0
    svc._vector_store_recent_fail = False
    svc._background_tasks = set()
    svc._pending = []
    svc._spawn_background_task = lambda coro: svc._pending.append(coro)
    return svc


async def drain(svc):
    for coro in svc._pending:
        await coro


# --------------------------------------------------------------------------
# recall
# --------------------------------------------------------------------------
async def test_recall_uses_the_role_namespace():
    svc = bare_service()
    svc._vector_store = FakeVectorStore()
    svc._build_rag_entries = lambda docs, distances: []

    context = {"_memory_namespace": "role_b"}
    await svc._inject_vector_context(context, "hi")

    assert svc._vector_store.searches == [{"query": "hi", "namespace": "role_b"}]
    assert context["dictionary_context"] == ["a doc"]


async def test_recall_without_a_role_is_unchanged():
    svc = bare_service()
    svc._vector_store = FakeVectorStore()
    svc._build_rag_entries = lambda docs, distances: []

    await svc._inject_vector_context({}, "hi")

    assert svc._vector_store.searches[0]["namespace"] is None


# --------------------------------------------------------------------------
# storage
# --------------------------------------------------------------------------
async def test_storage_writes_both_stores_with_the_namespace():
    svc = bare_service()
    svc._vector_store = FakeVectorStore()
    memory = FakeMemoryManager()
    svc._llm_service = FakeLLM(memory)

    async def fake_metadata(content, context=None):
        return {"importance": 0.4}

    svc._build_memory_metadata = fake_metadata

    await svc._persist_conversation_text("hello", "world", {"_memory_namespace": "role_b"})
    await drain(svc)

    assert svc._vector_store.writes[0]["namespace"] == "role_b"
    assert memory.calls[0]["namespace"] == "role_b"
    assert memory.calls[0]["metadata"] == {"importance": 0.4}


async def test_storage_without_a_role_stays_unscoped():
    svc = bare_service()
    svc._vector_store = FakeVectorStore()
    memory = FakeMemoryManager()
    svc._llm_service = FakeLLM(memory)

    async def fake_metadata(content, context=None):
        return {}

    svc._build_memory_metadata = fake_metadata

    await svc._persist_conversation_text("hello", "world", None)
    await drain(svc)

    assert svc._vector_store.writes[0]["namespace"] is None
    assert memory.calls[0]["namespace"] is None
