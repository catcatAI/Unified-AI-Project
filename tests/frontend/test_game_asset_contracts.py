"""2D/3D 遊戲資產契約測試（計畫 §5.1 / §5.3-1、2）。

WHY: 資產是內容管線與「萬物皆軸」引擎的輸入面——glb 合法性、包圍盒、
立繪尺寸、game_cards.json 自述總和都曾漂移（2026-10-17 實測發現
cards_by_type 總和 321≠351、total_abilities 33≠293 等，已修正並以本檔鎖定）。
任何資產改版或資料重生成必須同步更新本檔與計畫表（check_fact_gates 文檔域）。
"""

import json
import struct
from collections import Counter
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GLB_PATH = ROOT / "models" / "angela_clay" / "angela_clay.glb"
RENDER_DIR = ROOT / "models" / "angela_clay" / "render"
GAME_CARDS = ROOT / "apps" / "game-rpg" / "data" / "game_cards.json"

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def _parse_glb(raw: bytes):
    magic, version, total = struct.unpack_from("<III", raw, 0)
    assert raw[:4] == b"glTF", f"bad magic {raw[:4]!r}"
    assert version == 2, version
    assert total == len(raw), f"declared {total} != actual {len(raw)}"
    chunks = []
    off = 12
    while off < len(raw):
        clen, ctype = struct.unpack_from("<II", raw, off)
        data = raw[off + 8 : off + 8 + clen]
        assert len(data) == clen, f"chunk at {off} truncated"
        chunks.append((ctype, data))
        off += 8 + clen
    return chunks


def test_glb_is_valid_gltf_v2():
    raw = GLB_PATH.read_bytes()
    chunks = _parse_glb(raw)
    types = [c[0] for c in chunks]
    assert types[0] == JSON_CHUNK, "first chunk must be JSON"
    assert BIN_CHUNK in types, "expected BIN chunk for mesh buffers"

    doc = json.loads(chunks[0][1])
    assert doc["asset"]["version"] == "2.0"
    assert "Blender" in doc["asset"].get("generator", ""), doc["asset"].get("generator")
    # 計畫 §5.1 表鎖定：95 meshes / 18 materials（改版需同步 MD）
    assert len(doc["meshes"]) == 95, len(doc["meshes"])
    assert len(doc["materials"]) == 18, len(doc["materials"])
    assert len(doc["nodes"]) == 96, len(doc["nodes"])  # 95 mesh 節點 + 1 根節點
    assert doc["scenes"], "at least one scene"


def test_glb_position_accessors_yield_finite_aabb():
    """§5.3-2：由 JSON chunk 派生碰撞包圍盒（不依賴 trimesh）。"""
    raw = GLB_PATH.read_bytes()
    doc = json.loads(_parse_glb(raw)[0][1])

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    seen = 0
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            acc = doc["accessors"][prim["attributes"]["POSITION"]]
            assert "min" in acc and "max" in acc, "POSITION accessor must carry min/max"
            for i in range(3):
                lo[i] = min(lo[i], acc["min"][i])
                hi[i] = max(hi[i], acc["max"][i])
            seen += 1

    assert seen > 0
    assert all(map(lambda v: v == v and abs(v) != float("inf"), lo + hi)), "non-finite bound"
    extent = [hi[i] - lo[i] for i in range(3)]
    assert all(e > 0 for e in extent), f"degenerate extent {extent}"
    assert all(abs(v) < 1000 for v in lo + hi), "bounds outside sane model space"


RENDER_EXPECTED = {
    "preview_back.png",
    "preview_front.png",
    "preview_side.png",
    "preview_three_quarter.png",
}


def test_render_previews_complete_and_sized():
    found = {p.name for p in RENDER_DIR.glob("*.png")}
    assert found == RENDER_EXPECTED, found ^ RENDER_EXPECTED
    for name in sorted(found):
        with Image.open(RENDER_DIR / name) as im:
            assert im.size == (700, 900), (name, im.size)
            assert im.mode == "RGBA", (name, im.mode)


@pytest.mark.parametrize(
    "rel, size, mode",
    [
        ("apps/pixel-angela/base_sprite.png", (128, 128), "RGBA"),
        ("resources/angela_01.jpg", (339, 1024), "RGB"),
        ("resources/angela_02.jpg", (338, 1024), "RGB"),
        ("resources/angela_03.png", (592, 1792), "RGBA"),
        ("resources/icon.png", (32, 32), "RGBA"),
    ],
)
def test_bitmap_contract(rel, size, mode):
    p = ROOT / rel
    assert p.is_file(), f"missing {rel}"
    with Image.open(p) as im:
        assert im.size == size, (rel, im.size)
        assert im.mode == mode, (rel, im.mode)


class TestGameCardsContract:
    """game_cards.json：351 卡內容源 + 自述總和與資料一致性（曾漂移）。"""

    @pytest.fixture()
    def data(self):
        assert GAME_CARDS.is_file()
        with open(GAME_CARDS, encoding="utf-8") as f:
            return json.load(f)

    def test_top_level_totals_self_consistent(self, data):
        cards = data["cards"]
        assert data["version"] == "1.6"
        assert data["total_cards"] == 351 == len(cards)

        ids = [c.get("card_id") for c in cards]
        assert all(ids), "every card needs card_id"
        assert len(set(ids)) == 351, "card_id must be unique"

        # 自述 vs 資料（2026-10-17 修正後鎖定）
        assert data["cards_by_type"] == dict(Counter(c["card_type"] for c in cards))
        assert sum(data["cards_by_type"].values()) == 351
        assert data["total_with_description"] == sum(
            1 for c in cards if str(c.get("description") or "").strip()
        )
        assert data["total_abilities"] == sum(len(c.get("abilities") or []) for c in cards)
        assert data["total_relationships"] == sum(len(c.get("relationships") or []) for c in cards)

        n_tokens = sum(len(c.get("tokens") or []) for c in cards)
        token_cat = Counter(t["category"] for c in cards for t in c["tokens"])
        assert data["token_by_category"] == dict(token_cat)
        assert data["total_tokens"] == n_tokens == sum(token_cat.values())

        assert data["cards_with_time_data"] == sum(1 for c in cards if c.get("time_data"))

    def test_every_card_has_required_shape(self, data):
        required = {"card_id", "card_type", "name", "tokens", "stats", "abilities", "description"}
        for c in data["cards"]:
            missing = required - c.keys()
            assert not missing, f"{c.get('card_id')}: missing {missing}"
            assert isinstance(c["stats"], dict), c["card_id"]
            assert isinstance(c["abilities"], list), c["card_id"]
            assert isinstance(c["tokens"], list), c["card_id"]
            assert c["card_type"], c["card_id"]
            assert str(c["name"]).strip(), c["card_id"]
