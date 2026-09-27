"""
Config coverage: declared settings must actually be honoured.

WHY this file exists
--------------------
An audit asked which config keys the running system reads found that
`system/compute.default.yaml` declares 14 per-feature compute toggles while only
10 were referenced anywhere in the source — `three_layer_visual`,
`multimodal_train`, `gpu_accelerator` and `llm_local_gpu` were referenced by zero
files, despite §X #263 documenting all of them as integrated. Setting a feature
to `off` did nothing at all.

A broad "is this key referenced" sweep is too noisy to be a test: config consumed
by iterating a subtree (`backends.*`, `profiles.*`, `hardware_tiers.*`) never
mentions its own leaf names. So these tests assert two precise things instead:

1. every declared compute feature is honoured somewhere (no false positives —
   the feature names are distinctive and the §X #263 contract is explicit);
2. every *other* known-unhonoured section is on a reviewed list, so adding new
   dead config fails the suite and fixing one forces the list to shrink.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import json
import re
import sys
from pathlib import Path

import pytest


def _repo_root() -> Path:
    """Walk up until the backend source tree appears.

    Hard-coding parents[n] is wrong for a test that moves between `tests/` and
    `tests/<subdir>/`; the marker is unambiguous.
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "apps/backend/src").is_dir():
            return candidate
    raise AssertionError("could not locate the repository root from this test file")


ROOT = _repo_root()
SRC = ROOT / "apps/backend/src"
CONFIGS = ROOT / "apps/backend/configs"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.system.config import tiered_loader  # noqa: E402


def _source_blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in SRC.rglob("*.py"))


@pytest.fixture(scope="module")
def blob() -> str:
    return _source_blob()


# --------------------------------------------------------------------------- #
# 1. The compute contract
# --------------------------------------------------------------------------- #
def _declared_compute_features() -> list:
    cfg = tiered_loader.get_config("system/compute") or {}
    compute = cfg.get("compute") or {}
    return sorted(k for k, v in compute.items() if isinstance(v, dict) and "mode" in v)


def test_compute_features_are_declared_at_all():
    features = _declared_compute_features()
    assert len(features) >= 10, (
        f"only {len(features)} compute features declared — the loader contract "
        "expects the full per-feature set"
    )


# Features that cannot be honoured by this repository, each with the reason.
# Kept tiny on purpose: every entry is a claim that has to be re-justified.
COMPUTE_FEATURES_NO_CONSUMER = {
    "llm_local_gpu": (
        "the GPU layer decision belongs to the llama.cpp server process, which this "
        "repo talks to over HTTP and never launches — no code here can honour it"
    ),
}


@pytest.mark.parametrize("feature", _declared_compute_features())
def test_every_declared_compute_feature_is_honoured(blob, feature):
    """A toggle nobody reads is a promise the config cannot keep."""
    if feature in COMPUTE_FEATURES_NO_CONSUMER:
        assert (
            len(COMPUTE_FEATURES_NO_CONSUMER[feature]) > 30
        ), f"compute.{feature} is exempt from the coverage contract without a reason"
        return
    assert f'"{feature}"' in blob or f"'{feature}'" in blob, (
        f"compute.{feature} is declared in system/compute.default.yaml but no source "
        "file references it — setting it to `off` would do nothing"
    )


def test_compute_exemptions_stay_minimal():
    """The exemption list is the place dead config would otherwise accumulate."""
    assert len(COMPUTE_FEATURES_NO_CONSUMER) <= 2, (
        "more than two compute features cannot be honoured — that is a design "
        "problem to fix, not an exemption to add"
    )


def test_gpu_accelerator_gate_is_in_the_gpu_path():
    """The one place GPU monitoring starts must consult the toggle."""
    monitor = (SRC / "monitoring/system_monitor.py").read_text(encoding="utf-8")
    gate = monitor.split("def _init_gpu_monitoring", 1)[1][:1200]
    assert (
        'compute_bool("gpu_accelerator"' in gate
    ), "GPU monitoring initialises NVML without honouring compute.gpu_accelerator"
    # The gate must come before the real call, or it gates nothing. Matching the
    # bare word "nvmlInit" hit this method's own docstring, which mentions it.
    assert gate.index('compute_bool("gpu_accelerator"') < gate.index("pynvml.nvmlInit()")


def test_multimodal_train_gate_refuses_explicitly():
    """Turning training off must be visible, not a silent no-op."""
    pipeline = (SRC / "ai/multimodal/training_pipeline.py").read_text(encoding="utf-8")
    body = pipeline.split("    def run(", 1)[1][:2500]
    assert 'compute_bool("multimodal_train"' in body
    assert '"status": "skipped"' in body, (
        "a skipped training run must say so, so callers can tell it from a run "
        "that trained nothing because there was no data"
    )


def test_three_layer_visual_gate_precedes_model_load():
    routes = (SRC / "api/routes/image_generation_routes.py").read_text(encoding="utf-8")
    body = routes.split("def _get_three_layer", 1)[1][:1500]
    assert 'compute_bool("three_layer_visual"' in body
    assert body.index('compute_bool("three_layer_visual"') < body.index("ThreeLayerVisual(")


# --------------------------------------------------------------------------- #
# 2. Reviewed list of config that is declared but not honoured
# --------------------------------------------------------------------------- #
# Each entry: path -> second-level sections with no consumer, with the reason.
# A section belongs here only after someone has checked *why* it has no consumer;
# "we did not get to it" is not a reason.
UNHONOURED_SECTIONS = {
    "system/llm": {
        "backends.ollama-tinyllama": "iterated by the provider factory, never by name",
        "backends.openai-gpt4": "iterated by the provider factory, never by name",
        "backends.anthropic-claude": "iterated by the provider factory, never by name",
        "backends.google-gemini": "iterated by the provider factory, never by name",
    },
    "system/core": {
        "ai.core_network": "ED3N keeps its own network constants; these are a second source",
        "command_triggers.complex_project": (
            "no command-trigger feature exists; noted in system/core.default.yaml"
        ),
        "command_triggers.manual_delegation": (
            "no command-trigger feature exists; noted in system/core.default.yaml"
        ),
        "command_triggers.context_analysis": (
            "no command-trigger feature exists; noted in system/core.default.yaml"
        ),
        "memory_manager.short_term_memory_limit": "memory modules size themselves",
        "operational_configs.api_server": "host/port come from the CLI and env",
        "operational_configs.learning_thresholds": "the learning loop uses its own constants",
        "operational_configs.execution_monitor": "the monitor takes its own arguments",
        "system.log_path": "logging sets up its own sink",
        "tool_dispatcher.default_location": "tools are dispatched by id, not by path",
        "core_systems.local_storage": "the vector store owns its own path",
        "web_search_tool.search_url_template": "the tool uses DuckDuckGo's fixed endpoint",
    },
    "system/compute": {
        "compute.llm_local_gpu": (
            "exempt in COMPUTE_FEATURES_NO_CONSUMER: the external llama.cpp server "
            "owns the GPU decision, so nothing here can honour it"
        ),
    },
    "system/ed3n": {
        "ed3n.core_network": "the engine uses its own defaults",
        "ed3n.output_anchor": "anchor output is derived, not configured",
    },
    "system/data": {
        "data.subdirs": "paths are created from data.root, not from this map",
        "data.wiki": "wiki paths are derived from data.root",
    },
    "system/keys": {"firebase.credentials_path": "no Firebase integration is wired"},
    "system/timing": {"timing.loop": "loop sleeps read their own keys"},
    "system/game": {
        "game.mount_card_dictionary": (
            "the game module resolves its own paths/constants; noted in game.default.yaml"
        ),
        "game.mount_free_matrix": "as mount_card_dictionary; noted in game.default.yaml",
        "game.mount_axes": "as mount_card_dictionary; noted in game.default.yaml",
        "game.max_cards": "as mount_card_dictionary; noted in game.default.yaml",
        "game.dictionary_modality": "the game module has no consumer",
        "game.axis_registry_name": "the game module has no consumer",
        "game.supplement_path": "the game module has no consumer",
    },
    "system/capacity": {"capacity.dataset": "no dataset budgeting code exists"},
    "system/bootstrap": {"paths.venv": "tooling resolves the venv itself"},
}


def _second_level_sections(cfg: dict) -> list:
    out = []
    for top, value in cfg.items():
        if isinstance(value, dict):
            out.extend(f"{top}.{k}" for k in value)
        else:
            out.append(top)
    return out


@pytest.mark.parametrize("path", sorted(UNHONOURED_SECTIONS))
def test_unhonoured_sections_match_the_reviewed_list(path, blob):
    """Adding dead config fails; fixing one forces this list to shrink."""
    cfg = tiered_loader.get_config(path) or {}
    actual = {
        s
        for s in _second_level_sections(cfg)
        if not re.search(rf'["\']{re.escape(s.split(".")[-1])}["\']', blob)
    }
    reviewed = set(UNHONOURED_SECTIONS[path])
    unexpected = actual - reviewed
    stale = reviewed - actual
    assert not unexpected, (
        f"{path}: these sections are declared but nothing reads them, and they are "
        f"not on the reviewed list — either wire them or document why: {sorted(unexpected)}"
    )
    assert not stale, (
        f"{path}: these entries are on the reviewed list but are now honoured "
        f"(or renamed) — remove them from UNHONOURED_SECTIONS: {sorted(stale)}"
    )


def test_unhonoured_sections_all_carry_a_reason():
    """A bare list would let the next person add entries without thinking."""
    for path, sections in UNHONOURED_SECTIONS.items():
        for section, reason in sections.items():
            assert len(reason) > 20, f"{path}/{section} has no recorded reason"


# --------------------------------------------------------------------------- #
# 3. The gates must change behaviour, not merely exist as text
# --------------------------------------------------------------------------- #
@pytest.fixture
def compute_off(monkeypatch):
    """Force every compute_bool() answer to False, at the definition site.

    Patching the module attribute is the narrow option: the call sites import
    `compute_bool` inside the function body, so they resolve it at call time and
    see the patch. Over-broad module mocking is what caused the R85 cross-file
    failures, so nothing else is replaced.
    """
    from core.system.config import magic_numbers

    monkeypatch.setattr(magic_numbers, "compute_bool", lambda *a, **k: False)
    return True


def test_multimodal_train_off_skips_with_a_reason(compute_off):
    from ai.multimodal.training_pipeline import FullTrainingPipeline

    pipeline = FullTrainingPipeline.__new__(FullTrainingPipeline)
    result = pipeline.run(contrastive_epochs=1)
    assert result["status"] == "skipped"
    assert "multimodal_train" in result["reason"]


def test_gpu_accelerator_off_never_initialises_nvml(compute_off):
    from monitoring.system_monitor import SystemMonitor

    monitor = SystemMonitor.__new__(SystemMonitor)
    assert monitor._init_gpu_monitoring() is False


def test_three_layer_visual_off_loads_no_model(compute_off):
    import api.routes.image_generation_routes as routes

    routes._three_layer_state = None
    assert routes._get_three_layer() is None


def test_gates_default_to_the_configured_value_not_a_hardcoded_off():
    """A regression here would make the features permanently off (or permanently on)."""
    from core.system.config import magic_numbers

    # The declared default in YAML is `auto` for these three, so an unset config
    # must not read as disabled.
    for feature in ("multimodal_train", "three_layer_visual"):
        assert (
            magic_numbers.compute_bool(feature) is True
        ), f"{feature} defaults to disabled; system/compute.default.yaml declares auto"
    # gpu_accelerator is declared `off` in this repo, so False is correct here.
    assert magic_numbers.compute_bool("gpu_accelerator", default=False) is False


# --------------------------------------------------------------------------- #
# Identity: one name, one source
# --------------------------------------------------------------------------- #
def test_configured_ai_name_is_angela():
    """The user decided the name; the config must agree with the decision."""
    from core.system.config.identity import get_ai_name

    assert get_ai_name() == "Angela"


def test_identity_accessor_follows_the_config(monkeypatch):
    from core.system.config import identity, tiered_loader

    original = identity.get_ai_name()
    try:
        tiered_loader._cache.pop("system/core", None)
        identity.clear_cache()
        config = tiered_loader.get_config("system/core")
        config["ai_name"] = "TestName"
        identity.clear_cache()
        assert identity.get_ai_name() == "TestName"
    finally:
        tiered_loader._cache.pop("system/core", None)
        config = tiered_loader.get_config("system/core")
        if config is not None:
            config["ai_name"] = original
        identity.clear_cache()


def test_self_model_resolves_its_name_at_import(monkeypatch):
    """The mechanism, not the value.

    Asserting `SelfModel().name == "Angela"` cannot tell a config read from a
    hardcoded "Angela" — the mutation that reverted it to a literal passed. So the
    accessor is stubbed to a different name and the module reloaded: only a real
    config read produces it.
    """
    import importlib

    from core.life import cyber_identity
    from core.system.config import identity

    monkeypatch.setattr(identity, "get_ai_name", lambda *a, **k: "ZZZ_Config_Name")
    identity.clear_cache()
    try:
        reloaded = importlib.reload(cyber_identity)
        assert reloaded.SelfModel().name == "ZZZ_Config_Name"
    finally:
        monkeypatch.undo()
        identity.clear_cache()
        importlib.reload(cyber_identity)


def test_create_soul_core_honours_an_explicit_name():
    """It used to accept `name` and pass a hardcoded literal instead."""
    from core.metamorphosis.soul_core import create_soul_core

    assert create_soul_core().identity.name == "Angela"
    assert create_soul_core(name="TestSoul").identity.name == "TestSoul"


def test_name_is_not_read_from_a_reentrant_live_check():
    """`angela_agent.py` uses "Angela" as a *game player* name.

    It looks like an identity literal and is not one. A future sweep that
    "consolidates" every occurrence of the string would break game filtering, so
    the exception is pinned here.
    """
    agent = (SRC / "ai/autonomous/angela_agent.py").read_text(encoding="utf-8")
    assert 'player == "Angela"' in agent, (
        "the game-player comparison changed; it must not be routed through the " "identity config"
    )
    assert "get_ai_name" not in agent


def test_routing_policy_map_is_either_used_or_documented():
    """Catches a dead mapping, which a per-key sweep cannot.

    The per-key check looks for each key's *name* in the source, and `math`,
    `code`, `task` and `general` all appear for unrelated reasons — so the whole
    `routing.policy` block looked alive while `self._angela_routing`, the only
    handle on it, was assigned at router.py:355 and never read.
    """
    router = (SRC / "services/llm/router.py").read_text(encoding="utf-8")
    assert "_angela_routing" in router, (
        "the router no longer touches routing.policy at all — update this test and "
        "system/llm.default.yaml, because the config's status just changed"
    )
    # Read anywhere other than its own assignment?
    reads = len(re.findall(r"_angela_routing(?!\s*=\s*routing)", router)) > 1
    if reads:
        return  # policy-driven selection exists; the config is live

    # Still dead: the config file must say so, so nobody reads it as behaviour.
    llm_yaml = (CONFIGS / "system/llm.default.yaml").read_text(encoding="utf-8")
    assert "not consumed by code" in llm_yaml, (
        "self._angela_routing is assigned but never read, so every routing.policy "
        "entry is dead, and system/llm.default.yaml does not say so — implementing "
        "policy-driven selection is a design decision, so until then the file must "
        "state the truth"
    )
