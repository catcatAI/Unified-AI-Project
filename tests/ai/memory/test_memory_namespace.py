# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""P1-3: memory namespaces — a hard partition for role memory.

Unscoped records (the legacy bucket) must stay reachable exactly as before;
scoped records must never leak across roles, even when they score higher.
"""

import pytest
from ai.memory.ham_memory.ham_manager import HAMMemoryManager
from ai.memory.vector_store import VectorMemoryStore


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("ANGELA_VECTOR_BACKEND", "numpy")
    monkeypatch.setenv("HAM_DISABLE_VECTOR_STORE", "0")
    return VectorMemoryStore(persist_directory=str(tmp_path))


async def add(store, memory_id, content, namespace=None, **metadata):
    await store.add_memory(memory_id, content, metadata or None, namespace=namespace)


# --------------------------------------------------------------------------
# vector store: write side
# --------------------------------------------------------------------------
async def test_namespace_lands_in_metadata(store):
    await add(store, "m1", "alpha", namespace="role_b")
    await store.semantic_search("alpha", limit=1)
    assert store._numpy_backend.metadatas[0]["namespace"] == "role_b"


async def test_no_namespace_leaves_metadata_untouched(store):
    await store.add_memory("m1", "alpha", {"importance": 0.5})
    assert store._numpy_backend.metadatas[0] == {"importance": 0.5}


async def test_explicit_metadata_namespace_wins(store):
    await store.add_memory("m1", "alpha", {"namespace": "explicit"}, namespace="ignored")
    assert store._numpy_backend.metadatas[0]["namespace"] == "explicit"


async def test_metadata_is_not_mutated_in_place(store):
    meta = {"importance": 0.5}
    await store.add_memory("m1", "alpha", meta, namespace="role_b")
    assert meta == {"importance": 0.5}


# --------------------------------------------------------------------------
# vector store: read side
# --------------------------------------------------------------------------
async def test_search_is_partitioned_by_namespace(store):
    await add(store, "a1", "cat on the mat", namespace="role_a")
    await add(store, "b1", "cat on the mat", namespace="role_b")
    hits = await store.semantic_search("cat", limit=5, namespace="role_a")
    assert hits["ids"][0] == ["a1"]


async def test_search_without_namespace_sees_everything(store):
    await add(store, "a1", "cat", namespace="role_a")
    await add(store, "b1", "cat", namespace="role_b")
    await add(store, "u1", "cat")
    hits = await store.semantic_search("cat", limit=5)
    assert set(hits["ids"][0]) == {"a1", "b1", "u1"}


async def test_unknown_namespace_returns_empty(store):
    await add(store, "a1", "cat", namespace="role_a")
    assert await store.semantic_search("cat", namespace="role_z") == {}


async def test_namespace_excludes_unscoped_records(store):
    await add(store, "u1", "cat")
    assert await store.semantic_search("cat", namespace="role_a") == {}


async def test_namespace_combines_with_document_needle(store):
    await add(store, "a1", "fact: sky is blue", namespace="role_a")
    await add(store, "a2", "chat about weather", namespace="role_a")
    await add(store, "b1", "fact: sky is blue", namespace="role_b")
    hits = await store.semantic_search(
        "sky", where_document={"$contains": "sky"}, namespace="role_a"
    )
    assert hits["ids"][0] == ["a1"]


async def test_namespace_respects_limit(store):
    for i in range(5):
        await add(store, f"a{i}", "cat", namespace="role_a")
    hits = await store.semantic_search("cat", limit=2, namespace="role_a")
    assert len(hits["ids"][0]) == 2


async def test_namespace_survives_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("ANGELA_VECTOR_BACKEND", "numpy")
    first = VectorMemoryStore(persist_directory=str(tmp_path))
    await add(first, "a1", "cat", namespace="role_a")
    await add(first, "b1", "cat", namespace="role_b")
    first.persist()

    second = VectorMemoryStore(persist_directory=str(tmp_path))
    hits = await second.semantic_search("cat", namespace="role_b")
    assert hits["ids"][0] == ["b1"]


# --------------------------------------------------------------------------
# HAM manager
# --------------------------------------------------------------------------
def bare_ham(entries):
    ham = object.__new__(HAMMemoryManager)
    ham._data = {"conversations": entries, "templates": []}
    return ham


async def test_ham_query_filters_by_namespace():
    ham = bare_ham(
        [
            {"content": "role b secret", "metadata": {"namespace": "role_b"}},
            {"content": "role c secret", "metadata": {"namespace": "role_c"}},
            {"content": "legacy fact", "metadata": {}},
        ]
    )
    hits = await ham.query_core_memory(namespace="role_b")
    assert [h.content for h in hits] == ["role b secret"]


async def test_ham_query_without_namespace_keeps_legacy_behaviour():
    ham = bare_ham(
        [
            {"content": "role b", "metadata": {"namespace": "role_b"}},
            {"content": "legacy", "metadata": {}},
        ]
    )
    assert len(await ham.query_core_memory()) == 2


async def test_ham_store_experience_records_namespace():
    ham = bare_ham([])
    ham._apply_retention_policy = lambda meta: {}
    ham._enforce_cap = lambda bucket: None
    ham.prune = lambda: {}
    ham._save = lambda: None
    await ham.store_experience("hello", "conversation", namespace="role_b")
    assert ham._data["conversations"][0]["metadata"]["namespace"] == "role_b"


async def test_ham_store_experience_explicit_metadata_wins():
    ham = bare_ham([])
    ham._apply_retention_policy = lambda meta: {}
    ham._enforce_cap = lambda bucket: None
    ham.prune = lambda: {}
    ham._save = lambda: None
    await ham.store_experience(
        "hello", "conversation", metadata={"namespace": "explicit"}, namespace="ignored"
    )
    assert ham._data["conversations"][0]["metadata"]["namespace"] == "explicit"
