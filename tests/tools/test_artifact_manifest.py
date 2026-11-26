"""Artifact manifest contract: traceable hashes, tamper detection."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def generator():
    path = REPO / "scripts" / "gen_artifact_manifest.py"
    spec = importlib.util.spec_from_file_location("gen_artifact_manifest", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_artifact_manifest"] = module
    spec.loader.exec_module(module)
    return module


def test_manifest_records_sha256_and_producer(generator, tmp_path) -> None:
    report = tmp_path / "data" / "intelligence_reports"
    report.mkdir(parents=True)
    (report / "core_control.json").write_text('{"suite":"math"}\n', encoding="utf-8")
    manifest = generator.build(tmp_path)
    entry = next(e for e in manifest["entries"] if e["path"].endswith("core_control.json"))
    assert entry["sha256"]
    assert entry["producer"] == "scripts/probe_core_control.py"
    assert entry["verified"] is True


def test_check_detects_a_tampered_artifact(generator, tmp_path) -> None:
    report = tmp_path / "data" / "intelligence_reports"
    report.mkdir(parents=True)
    artifact = report / "native_dialogue.json"
    artifact.write_text('{"v":1}\n', encoding="utf-8")
    out = tmp_path / "manifest.json"
    assert generator.main(["--root", str(tmp_path), "--out", str(out)]) == 0
    assert generator.main(["--root", str(tmp_path), "--out", str(out), "--check"]) == 0

    artifact.write_text('{"v":2}\n', encoding="utf-8")
    assert generator.main(["--root", str(tmp_path), "--out", str(out), "--check"]) == 1
