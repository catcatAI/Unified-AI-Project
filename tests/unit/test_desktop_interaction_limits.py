# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""DesktopInteraction file-size limits (first coverage for core/engine writes)."""

import asyncio


def _interaction(tmp_path):
    from core.engine.desktop_interaction import DesktopInteraction

    return DesktopInteraction(
        config={
            "desktop_path": str(tmp_path / "desktop"),
            "organized_path": str(tmp_path / "organized"),
        }
    )


def test_create_small_file(tmp_path):
    interaction = _interaction(tmp_path)
    target = asyncio.run(interaction.create_file("ok.txt", "hello"))
    assert target is not None
    assert target.read_text(encoding="utf-8") == "hello"


def test_create_refuses_oversized(tmp_path, monkeypatch):
    import core.engine.desktop_interaction as di_mod

    monkeypatch.setattr(di_mod, "max_file_write_mb", lambda: 0)
    interaction = _interaction(tmp_path)
    assert asyncio.run(interaction.create_file("big.txt", "x" * 100)) is None
    assert not (tmp_path / "desktop" / "big.txt").exists()
