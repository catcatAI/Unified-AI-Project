"""Live2D model3.json manifest contract（web 與 desktop 兩面）。

WHY: 2026-10-12 審計發現 miara 的 model3.json 是「事後重建的最小清單」
（Groups Ids 全空、HitAreas 空、無 Expressions）。重建檔最容易漂移——
本測試守三件事：
  1. FileReferences 全部路徑在磁碟可解析（含 expressions/motions/physics），
  2. Groups.Ids 的每個參數 id 真的存在於 cdi3（P1-7 以 cdi3 實值填入），
  3. web / desktop 兩面的 manifest byte 一致（防單面改動漂移）。
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SURFACES = {
    "web": ROOT / "apps" / "web-live2d-viewer" / "models",
    "desktop": ROOT / "apps" / "desktop-app" / "electron_app" / "models",
}
MODELS = {
    "miara_pro_en": "miara_pro_en/runtime/miara_pro_t03.model3.json",
    "Epsilon_free": "Epsilon_free/runtime/Epsilon_free.model3.json",
}


def _iter_refs(manifest: dict) -> list[str]:
    refs: list[str] = []
    fr = manifest.get("FileReferences", {})
    for key in ("Moc", "DisplayInfo", "Physics"):
        if fr.get(key):
            refs.append(fr[key])
    refs.extend(fr.get("Textures") or [])
    exp = fr.get("Expressions") or []
    for e in exp:
        refs.append(e["File"])
    for group in (fr.get("Motions") or {}).values():
        for entry in group:
            refs.append(entry["File"])
    return refs


@pytest.mark.parametrize("model", sorted(MODELS))
def test_filereferences_resolve_on_both_surfaces(model):
    rel = MODELS[model]
    for surface, base in SURFACES.items():
        manifest_path = base / rel
        assert manifest_path.is_file(), f"{surface}: missing {manifest_path}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        refs = _iter_refs(manifest)
        assert refs, f"{surface}/{model}: no FileReferences at all"
        for ref in refs:
            target = manifest_path.parent / ref
            assert target.is_file(), f"{surface}/{model}: dangling ref '{ref}'"


@pytest.mark.parametrize("model", sorted(MODELS))
def test_groups_ids_exist_in_cdi3(model):
    rel = MODELS[model]
    for surface, base in SURFACES.items():
        manifest_path = base / rel
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        fr = manifest.get("FileReferences", {})
        if not fr.get("DisplayInfo"):
            continue
        cdi_path = manifest_path.parent / fr["DisplayInfo"]
        params = {p["Id"] for p in json.loads(cdi_path.read_text(encoding="utf-8"))["Parameters"]}
        for group in manifest.get("Groups", []):
            ids = group.get("Ids") or []
            missing = [i for i in ids if i not in params]
            assert (
                not missing
            ), f"{surface}/{model}: group '{group['Name']}' ids not in cdi3: {missing}"


def test_surfaces_byte_identical():
    for model, rel in MODELS.items():
        blobs = {s: (base / rel).read_bytes() for s, base in SURFACES.items()}
        assert (
            blobs["web"] == blobs["desktop"]
        ), f"{model}: web/desktop model3.json diverged — sync both copies"
