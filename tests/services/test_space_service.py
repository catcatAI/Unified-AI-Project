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
    assert roles == ["main", "role_b", "role_c", "role_d"]


# --------------------------------------------------------------------------
# wardrobe (S2: the AI may change an outfit)
# --------------------------------------------------------------------------
def test_actor_starts_with_an_empty_outfit(service):
    actor = service.get("main")
    assert actor["outfit"] == {}
    assert actor["outfit_rev"] == 0


def test_update_avatar_sets_one_slot_and_bumps_rev(service):
    service.update_avatar("role_b", "top", "jacket_purple", "#6a4f9e")
    actor = service.get("role_b")
    assert actor["outfit"]["top"] == {"item": "jacket_purple", "tint": "#6a4f9e"}
    assert actor["outfit_rev"] == 1
    service.update_avatar("role_b", "top", "hoodie", "#3b6ea5")
    assert actor["outfit_rev"] == 2


def test_update_avatar_keeps_previous_tint_when_omitted(service):
    service.update_avatar("role_b", "top", "jacket", "#112233")
    service.update_avatar("role_b", "top", "hoodie")
    assert service.get("role_b")["outfit"]["top"] == {"item": "hoodie", "tint": "#112233"}


def test_update_avatar_rejects_bad_input(service):
    with pytest.raises(ValueError):
        service.update_avatar("role_b", "hat", "beret")
    with pytest.raises(ValueError):
        service.update_avatar("role_b", "top", "")
    with pytest.raises(ValueError):
        service.update_avatar("role_b", "top", "x", "red")
    with pytest.raises(ValueError):
        service.update_avatar("ghost", "top", "x")


def test_apply_dispatches_wardrobe(service):
    service.apply(
        {
            "type": "wardrobe",
            "actor_id": "main",
            "slot": "shoes",
            "item": "boots",
            "tint": "#3a2f2a",
        }
    )
    assert service.get("main")["outfit"]["shoes"]["item"] == "boots"


def test_snapshot_carries_the_outfit(service):
    service.update_avatar("main", "accessory", "ribbon", "#d94f70")
    actor = next(a for a in service.snapshot()["data"]["actors"] if a["actor_id"] == "main")
    assert actor["outfit"]["accessory"] == {"item": "ribbon", "tint": "#d94f70"}


# --------------------------------------------------------------------------
# wardrobe rules (S2: state -> outfit)
# --------------------------------------------------------------------------
def test_low_valence_dresses_down(service):
    changed = service.auto_dress("main", {"valence": 0.1})
    assert changed == ["top", "accessory"]
    assert service.get("main")["outfit"]["top"]["tint"] == "#3f3f5f"


def test_tired_role_gets_comfortable_clothes(service):
    changed = service.auto_dress("main", {"valence": 0.5, "fatigue": 0.9})
    assert "top" in changed
    assert service.get("main")["outfit"]["top"]["item"] == "cardigan_green"


def test_no_rule_match_changes_nothing(service):
    assert service.auto_dress("main", {"valence": 0.5, "fatigue": 0.1}) == []
    assert service.get("main")["outfit"] == {}


def test_rules_can_be_injected(service):
    rules = [
        {
            "priority": 1,
            "when": {"stress": {"gte": 0.5}},
            "outfit": {"shoes": {"item": "boots", "tint": "#111111"}},
        }
    ]
    assert service.auto_dress("role_b", {"stress": 0.6}, rules=rules) == ["shoes"]
    assert service.get("role_b")["outfit"]["shoes"]["item"] == "boots"


def test_rules_file_is_loadable():
    rules = mod._load_wardrobe_rules()
    assert rules and rules[0]["priority"] >= rules[-1]["priority"]
