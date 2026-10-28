# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
# =============================================================================
"""SpaceService: stage state, speech expiry, and action validation."""

import pytest
from services.space import space_service as mod
from services.space.space_service import SpaceService


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, ms):
        self.now += ms / 1000.0


@pytest.fixture()
def clock():
    return FakeClock()


@pytest.fixture()
def service(clock):
    svc = SpaceService(clock=clock)
    svc.load_room({"room_id": "studio_a", "name": "棚"})
    svc.spawn({"role_id": "main", "avatar_id": "angela_base", "position": [5.5, 0]})
    svc.spawn({"role_id": "role_b", "avatar_id": "gemma_b", "position": [8, 0]})
    return svc


def test_room_and_actor_spawn(service):
    snap = service.snapshot()
    assert snap["data"]["room_id"] == "studio_a"
    assert [a["role_id"] for a in snap["data"]["actors"]] == ["main", "role_b"]


def test_duplicate_actor_is_rejected(service):
    with pytest.raises(ValueError):
        service.spawn({"role_id": "main"})


def test_spawn_needs_an_id(service):
    with pytest.raises(ValueError):
        service.spawn({})


def test_move_updates_position_and_revision(service):
    before = service.revision
    service.move("role_b", [10.5, 0])
    assert service.get("role_b")["position"] == [10.5, 0.0]
    assert service.revision > before


def test_say_sets_speech_that_expires(service, clock):
    service.say("role_b", "帳整理好了", ttl_ms=2000)
    assert service.snapshot()["data"]["actors"][1]["speech"] == {"text": "帳整理好了"}
    clock.advance(2001)
    assert service.snapshot()["data"]["actors"][1]["speech"] is None


def test_empty_speech_is_rejected(service):
    with pytest.raises(ValueError):
        service.say("role_b", "   ")


def test_unknown_actor_raises(service):
    with pytest.raises(ValueError):
        service.move("ghost", [1, 1])


def test_apply_dispatches_each_action(service):
    service.apply({"type": "express", "actor_id": "main", "expression": "smile"})
    service.apply({"type": "play", "actor_id": "main", "motion": "idle_breath"})
    service.apply({"type": "face", "actor_id": "main", "facing": 1.5})
    actor = service.get("main")
    assert actor["expression"] == "smile"
    assert actor["motion"] == "idle_breath"
    assert actor["facing"] == 1.5


def test_apply_rejects_unknown_action(service):
    with pytest.raises(ValueError):
        service.apply({"type": "backflip", "actor_id": "main"})


def test_despawn_removes_the_actor(service):
    assert service.despawn("role_b") is True
    assert service.despawn("role_b") is False
    assert [a["role_id"] for a in service.snapshot()["data"]["actors"]] == ["main"]


def test_visibility_is_carried_in_the_snapshot(service):
    service.spawn({"role_id": "role_c", "visible_to": ["main", "role_c"]})
    actors = {a["role_id"]: a for a in service.snapshot()["data"]["actors"]}
    assert actors["role_c"]["visible_to"] == ["main", "role_c"]


def test_singleton_resets(monkeypatch):
    monkeypatch.setattr(mod, "_service", None)
    first = mod.get_space_service()
    assert mod.get_space_service() is first
    mod.reset_space_service()
    assert mod.get_space_service() is not first


# --------------------------------------------------------------------------
# seeding
# --------------------------------------------------------------------------
def test_seed_reads_the_stage_roster(tmp_path, monkeypatch):
    roster = tmp_path / "roles.json"
    roster.write_text(
        '{"actors": [{"role_id": "main", "avatar_id": "angela_base", "position": [5.5, 0]},'
        ' {"role_id": "role_b", "avatar_id": "gemma_b", "position": [8, 0]}]}',
        encoding="utf-8",
    )
    monkeypatch.setenv("ANGELA_SPACE_ROSTER", str(roster))
    monkeypatch.delenv("SPACE_SEED_ROLES", raising=False)
    svc = mod.seed_default_stage(SpaceService())
    actors = svc.snapshot()["data"]["actors"]
    assert [a["role_id"] for a in actors] == ["main", "role_b"]
    assert actors[1]["avatar_id"] == "gemma_b"
    assert actors[1]["position"] == [8, 0]


def test_seed_can_be_disabled(monkeypatch):
    monkeypatch.setenv("SPACE_SEED_ROLES", "0")
    assert mod.seed_default_stage(SpaceService()).snapshot()["data"]["actors"] == []


def test_seed_does_not_touch_a_populated_stage(monkeypatch, tmp_path):
    roster = tmp_path / "roles.json"
    roster.write_text('{"actors": [{"role_id": "role_z"}]}', encoding="utf-8")
    monkeypatch.setenv("ANGELA_SPACE_ROSTER", str(roster))
    monkeypatch.delenv("SPACE_SEED_ROLES", raising=False)
    svc = SpaceService()
    svc.spawn({"role_id": "main"})
    mod.seed_default_stage(svc)
    assert [a["role_id"] for a in svc.snapshot()["data"]["actors"]] == ["main"]


def test_seed_falls_back_to_the_role_config(monkeypatch, tmp_path):
    monkeypatch.setenv("ANGELA_SPACE_ROSTER", str(tmp_path / "missing.json"))
    monkeypatch.delenv("SPACE_SEED_ROLES", raising=False)
    svc = mod.seed_default_stage(SpaceService())
    roles = [a["role_id"] for a in svc.snapshot()["data"]["actors"]]
    assert roles == ["main", "role_b", "role_c"]
