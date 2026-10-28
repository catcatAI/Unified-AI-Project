# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Three local models: sizing against this machine, and the config overlay."""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


planner = load("plan_local_three_models", REPO_ROOT / "scripts" / "plan_local_three_models.py")
runner = load("run_local_three_models", REPO_ROOT / "scripts" / "run_local_three_models.py")


# --------------------------------------------------------------------------
# sizing
# --------------------------------------------------------------------------
def test_gpu_with_display_leaves_room_for_the_desktop():
    plan = planner.plan_three(9.44, 7.0, ctx=2048, has_display=True)
    assert plan.mode == "gpu"
    assert len(plan.picks) == 3
    assert plan.total_gb <= 9.44 * 0.70 + 0.01
    assert plan.total_gb == pytest.approx(
        sum(m.footprint_gb(2048) for _, m in plan.picks), abs=0.02
    )


def test_three_distinct_families_are_preferred():
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    families = {model.family for _, model in plan.picks}
    assert len(families) == 3


def test_strongest_model_goes_to_main():
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    roles = [placement["role"] for placement, _ in plan.picks]
    assert roles == ["main", "role_b", "role_c"]
    main_params = plan.picks[0][1].params_b
    assert main_params >= max(model.params_b for _, model in plan.picks) - 0.01


def test_small_gpu_degrades_to_on_demand():
    plan = planner.plan_three(4.0, 8.0, has_display=False)
    assert plan.mode == "on_demand"
    assert "one at a time" in " ".join(plan.notes).lower()


def test_cpu_only_uses_a_tighter_budget():
    plan = planner.plan_three(None, 16.0, has_display=False)
    assert plan.mode == "cpu"
    assert plan.total_gb <= 16.0 * 0.6 + 0.01


def test_unknown_hardware_assumes_a_small_box():
    plan = planner.plan_three(None, None)
    assert plan.mode == "on_demand"
    assert len(plan.picks) == 3


def test_footprints_include_kv_and_runtime():
    smallest = planner.CATALOG[0]
    assert smallest.footprint_gb(2048) > smallest.weights_gb


def test_commands_pin_ports_and_gpu_offload():
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    commands = plan.commands(threads=4)
    assert len(commands) == 3
    for command, (placement, _) in zip(commands, plan.picks):
        assert f"--port {placement['port']}" in command
        assert "-ngl 99" in command
        assert "-t 4" in command


def test_missing_files_are_reported_for_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(planner, "MODELS_DIR", tmp_path)
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    assert len(planner.check_files(plan)) == 3


def test_existing_files_are_not_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(planner, "MODELS_DIR", tmp_path)
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    for _, model in plan.picks:
        (tmp_path / model.filename).write_text("stub")
    assert planner.check_files(plan) == []


# --------------------------------------------------------------------------
# overlay
# --------------------------------------------------------------------------
def test_overlay_enables_three_slots(tmp_path, monkeypatch):
    overlay = tmp_path / "llm.evolved.yaml"
    monkeypatch.setattr(runner, "OVERLAY", overlay)
    monkeypatch.setattr(runner, "OVERLAY_BACKUP", tmp_path / "backup.yaml")
    monkeypatch.setattr(runner, "CONFIG_DIR", tmp_path)

    plan = planner.plan_three(9.44, 7.0, has_display=True)
    runner.install_overlay(plan.to_dict()["picks"])

    text = overlay.read_text(encoding="utf-8")
    for slot in ("llamacpp-local", "llamacpp-gemma", "llamacpp-qwen"):
        assert f"{slot}:" in text
        assert "enabled: true" in text
    assert "deployment:" not in text  # the evolved layer must not choose cloud access


def test_overlay_is_restored_not_deleted(tmp_path, monkeypatch):
    overlay = tmp_path / "llm.evolved.yaml"
    backup = tmp_path / "llm.evolved.yaml.pre-local"
    monkeypatch.setattr(runner, "OVERLAY", overlay)
    monkeypatch.setattr(runner, "OVERLAY_BACKUP", backup)
    monkeypatch.setattr(runner, "CONFIG_DIR", tmp_path)

    overlay.write_text("original: true\n", encoding="utf-8")
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    runner.install_overlay(plan.to_dict()["picks"])

    assert backup.read_text(encoding="utf-8") == "original: true\n"
    assert "llamacpp-local:" in overlay.read_text(encoding="utf-8")

    runner.remove_overlay()
    assert overlay.read_text(encoding="utf-8") == "original: true\n"
    assert not backup.exists()


def test_remove_overlay_without_backup_deletes_the_generated_file(tmp_path, monkeypatch):
    overlay = tmp_path / "llm.evolved.yaml"
    monkeypatch.setattr(runner, "OVERLAY", overlay)
    monkeypatch.setattr(runner, "OVERLAY_BACKUP", tmp_path / "none.yaml")
    monkeypatch.setattr(runner, "CONFIG_DIR", tmp_path)

    overlay.write_text(
        runner.overlay_yaml([{"slot": "llamacpp-local", "port": 8080, "path": "/m/x.gguf"}]),
        encoding="utf-8",
    )
    runner.remove_overlay()
    assert not overlay.exists()


def test_overlay_state_distinguishes_ours_from_theirs(tmp_path, monkeypatch):
    overlay = tmp_path / "llm.evolved.yaml"
    monkeypatch.setattr(runner, "OVERLAY", overlay)

    assert runner.overlay_state() == "absent"
    overlay.write_text("settings:\n  preferred_backend: unified\n", encoding="utf-8")
    assert runner.overlay_state() == "present (not ours — stop will not touch it)"
    overlay.write_text(
        runner.overlay_yaml([{"slot": "llamacpp-local", "port": 8080, "path": "/m/x.gguf"}]),
        encoding="utf-8",
    )
    assert runner.overlay_state().startswith("generated")


def test_gemma_command_disables_flash_attention():
    """gemma-2 on this build needs -fa off; the command must carry it."""
    plan = planner.plan_three(9.44, 7.0, has_display=True)
    by_slot = {placement["slot"]: cmd for (placement, _), cmd in zip(plan.picks, plan.commands())}
    assert "-fa off" in by_slot["llamacpp-gemma"]
    assert "-fa off" not in by_slot["llamacpp-local"]


def test_remove_overlay_leaves_a_foreign_overlay_alone(tmp_path, monkeypatch):
    overlay = tmp_path / "llm.evolved.yaml"
    monkeypatch.setattr(runner, "OVERLAY", overlay)
    monkeypatch.setattr(runner, "OVERLAY_BACKUP", tmp_path / "none.yaml")

    overlay.write_text("# Angela's self-evolution layer\n{}\n", encoding="utf-8")
    runner.remove_overlay()
    assert overlay.exists(), "stop must not delete a config it did not generate"
