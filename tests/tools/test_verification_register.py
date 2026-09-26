"""The real verification register must stay honest.

tests/test_gen_project_map.py proves the loader's rules on synthetic data. This
file checks the committed register itself: that every claim CI cannot verify is
actually filed, that each entry points at files that exist, and that nothing
quietly claims to be verified.

The register exists because this environment has no display: Electron menus,
settings switches, TTS voices and proactive speech bubbles cannot be honestly
verified here. Keeping them in a data file the project-map tool renders means
the debt is visible every time the map is generated, instead of buried in source
comments where it can be forgotten.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs/VERIFICATION_REGISTER.json"
TOOL = ROOT / "scripts/gen_project_map.py"

VALID_AREAS = {"settings", "menu", "ipc", "agent", "training", "other"}


def _load_tool():
    spec = importlib.util.spec_from_file_location("gen_project_map_tvr", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def entries():
    return json.loads(REGISTER.read_text(encoding="utf-8"))["entries"]


def test_register_exists_and_is_not_empty(entries):
    assert REGISTER.is_file()
    assert entries, "an empty register would claim everything is CI-verifiable"


def test_every_entry_uses_a_known_area(entries):
    for e in entries:
        assert e["area"] in VALID_AREAS, f"{e['id']}: unknown area {e['area']!r}"


def test_every_entry_names_files_that_exist(entries):
    """A register pointing at a moved file is worse than none."""
    for e in entries:
        assert e["files"], f"{e['id']} names no files"
        for rel in e["files"]:
            assert (ROOT / rel).exists(), f"{e['id']} references missing {rel}"


def test_every_unverified_entry_explains_itself(entries):
    for e in entries:
        if e["status"] == "unverified":
            assert len(e["why_unverified"]) > 15, f"{e['id']}: no real reason given"
            assert len(e["how_to_verify"]) > 20, f"{e['id']}: not actionable by a human"


def test_verified_entries_carry_evidence(entries):
    for e in entries:
        if e["status"] == "verified":
            assert e.get("verified_how"), f"{e['id']} claims verified with no evidence"
            assert len(e["verified_how"]) > 20, f"{e['id']}: evidence too thin to trust"


def test_loader_accepts_the_committed_file():
    mod = _load_tool()
    loaded = mod.load_register(str(REGISTER))
    assert len(loaded) == len(json.loads(REGISTER.read_text(encoding="utf-8"))["entries"])


def test_generated_map_embeds_the_register():
    mod = _load_tool()
    loaded = mod.load_register(str(REGISTER))
    block = "\n".join(mod.block_verification(loaded))
    for e in loaded:
        assert e["id"] in block, f"{e['id']} is not rendered into the map"
