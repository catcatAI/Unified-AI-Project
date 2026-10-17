# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L3]
# =============================================================================

"""軸→視覺契約繪製測試（game_sprites）。

覆蓋計畫 §5.2 驗收：(1) 軸位→特徵契約（計畫例：物種 C→獸形、義體 C4→金屬高光）；
(2) 三圖層輸出 32×32/64×64 尺寸/色深斷言；(3) 16×16 四地形 tile；
(4) atlas 與 JSON 幀表一致性（邊界/不重疊/裁切等於原幀）；
(5) 與 apps/game-rpg/axis_system.py 軸位表的跨檔同步鎖定（防鏡像漂移）。
"""

import importlib.util
import json
from pathlib import Path

import pytest
from ai.multimodal.primitives.game_sprites import (
    AXIS_POSITIONS,
    BASE_PROFILE,
    ENTITY_SIZES,
    GROUP_PROFILES,
    LAYER_ORDER,
    TILE_KINDS,
    AxisCodeError,
    build_atlas,
    default_entity_codes,
    entity_frame_name,
    entity_traits,
    main,
    parse_entity_axes,
    render_entity_layers,
    render_entity_set,
    render_entity_sprite,
    render_terrain_set,
    render_terrain_tile,
    save_atlas,
)

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
AXIS_SYSTEM_PATH = ROOT / "apps" / "game-rpg" / "axis_system.py"

VALID_CODES = [
    ("物種", "N-H-P"),
    ("物種", "S-S-P"),
    ("物種", "F-C-M2"),
    ("AI", "F1-A1-O0"),
    ("義體人", "C4-H3-B3"),
    ("神話種", "D3-O1-M1"),
    (BASE_PROFILE, "base"),
]


def _max_alpha(img: Image.Image) -> int:
    return max(img.getchannel("A").tobytes())


@pytest.fixture(scope="module")
def axis_system():
    """載入 game-rpg axis_system（跨檔同步鎖定的比對基準）。"""
    assert AXIS_SYSTEM_PATH.is_file(), f"missing {AXIS_SYSTEM_PATH}"
    spec = importlib.util.spec_from_file_location("_axis_system_under_test", AXIS_SYSTEM_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestParseAxes:
    @pytest.mark.parametrize("profile,code", VALID_CODES)
    def test_valid_codes_parse_to_three_segments(self, profile, code):
        segs = parse_entity_axes(profile, code)
        assert len(segs) == len(AXIS_POSITIONS.get(profile, {"base": 1}))

    def test_lineage_prefix_and_parentheses_stripped(self):
        assert parse_entity_axes("物種", "獸娘｜ F-H-P（遠原種、類人型、純血）") == (
            "F",
            "H",
            "P",
        )

    def test_unknown_profile_raises(self):
        with pytest.raises(AxisCodeError):
            parse_entity_axes("未知系", "N-H-P")

    def test_wrong_segment_count_raises(self):
        with pytest.raises(AxisCodeError):
            parse_entity_axes("物種", "N-C")

    def test_unknown_segment_raises(self):
        with pytest.raises(AxisCodeError):
            parse_entity_axes("物種", "X-C-P")

    def test_base_profile_rejects_non_base_code(self):
        with pytest.raises(AxisCodeError):
            parse_entity_axes(BASE_PROFILE, "S-S-P")


class TestTraitContract:
    @pytest.mark.parametrize(
        "form,expected",
        [("H", "humanoid"), ("S", "anthro"), ("C", "beast")],
    )
    def test_species_form_axis_maps_silhouette(self, form, expected):
        # 計畫 §5.2 例：物種軸 C 類原型→獸形輪廓
        assert entity_traits("物種", f"N-{form}-P").silhouette == expected

    def test_cyber_metal_highlight_monotonic(self):
        # 計畫 §5.2 例：義體 C4→金屬高光（C1<C2<C3<C4）
        levels = [entity_traits("義體人", f"C{i}-H1-B1").highlight for i in (1, 2, 3, 4)]
        assert levels == sorted(levels) and levels[0] < levels[-1]
        assert entity_traits("義體人", "C4-H3-B3").highlight == pytest.approx(0.95)

    def test_cyber_brain_axis_emissive_monotonic(self):
        ems = [entity_traits("義體人", f"C1-H1-B{b}").emissive for b in (1, 2, 3)]
        assert ems == sorted(ems) and ems[-1] >= 0.9

    def test_ai_form_axis_maps_silhouette(self):
        assert entity_traits("AI", "F0-A0-O0").silhouette == "point"
        assert entity_traits("AI", "F3-A3-O2").silhouette == "humanoid"

    def test_ai_openness_transparency_monotonic(self):
        trans = [entity_traits("AI", f"F1-A1-O{o}").transparency for o in (0, 1, 2)]
        assert trans == sorted(trans) and trans[-1] > trans[0]

    def test_myth_mode_transparency_monotonic(self):
        trans = [entity_traits("神話種", f"D1-O1-M{m}").transparency for m in (1, 2, 3)]
        assert trans == sorted(trans) and trans[0] == 0.0 and trans[-1] >= 0.6

    def test_myth_fidelity_changes_accent_color(self):
        a = entity_traits("神話種", "D1-O1-M1").accent_color
        b = entity_traits("神話種", "D1-O3-M1").accent_color
        assert a != b

    def test_base_profile_humanoid_baseline(self):
        t = entity_traits(BASE_PROFILE, "base")
        assert t.silhouette == "humanoid"
        assert t.transparency == 0.0


class TestRenderLayers:
    @pytest.mark.parametrize("size", ENTITY_SIZES)
    def test_three_layers_size_and_mode(self, size):
        layers = render_entity_layers("N-C-P", "物種", size=size)
        assert tuple(layers) == LAYER_ORDER
        for layer in layers.values():
            assert layer.size == (size, size)
            assert layer.mode == "RGBA"

    @pytest.mark.parametrize("size", ENTITY_SIZES)
    def test_composite_size_and_mode(self, size):
        img = render_entity_sprite("C4-H3-B3", "義體人", size=size)
        assert img.size == (size, size)
        assert img.mode == "RGBA"

    def test_body_layer_has_pixels(self):
        layers = render_entity_layers("S-H-P", "物種", size=64)
        assert layers["body"].getbbox() is not None

    def test_emissive_layer_has_eyes(self):
        layers = render_entity_layers("C4-H3-B3", "義體人", size=64)
        assert layers["emissive"].getbbox() is not None

    def test_different_axes_produce_different_sprites(self):
        a = render_entity_sprite("N-H-P", "物種")
        b = render_entity_sprite("F-C-M2", "物種")
        assert a.tobytes() != b.tobytes()

    def test_transparency_softens_alpha(self):
        solid = render_entity_sprite("D1-O1-M1", "神話種", size=64)
        ghost = render_entity_sprite("D1-O1-M3", "神話種", size=64)
        assert _max_alpha(ghost) < _max_alpha(solid)

    @pytest.mark.parametrize("size", [8, 15])
    def test_too_small_size_raises(self, size):
        with pytest.raises(ValueError):
            render_entity_sprite("N-H-P", "物種", size=size)


class TestTerrainTiles:
    @pytest.mark.parametrize("kind", TILE_KINDS)
    def test_kinds_render_16x16_rgba(self, kind):
        tile = render_terrain_tile(kind)
        assert tile.size == (16, 16)
        assert tile.mode == "RGBA"
        assert tile.getbbox() is not None

    def test_plan_kinds_exact_set(self):
        # 計畫 §5.2-2：毒氣區/走廊/湖/市場
        assert set(TILE_KINDS) == {"toxic_zone", "corridor", "lake", "market"}

    def test_tiles_are_pairwise_distinct(self):
        tiles = {k: render_terrain_tile(k).tobytes() for k in TILE_KINDS}
        values = list(tiles.values())
        assert len(set(values)) == len(values)

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError):
            render_terrain_tile("lava")

    def test_too_small_tile_raises(self):
        with pytest.raises(ValueError):
            render_terrain_tile("lake", size=4)

    def test_terrain_set_names(self):
        frames = render_terrain_set()
        assert set(frames) == {f"terrain_{k}" for k in TILE_KINDS}


class TestAtlasConsistency:
    @pytest.fixture()
    def sample_frames(self):
        codes = [("物種", "N-H-P"), ("物種", "S-S-P"), ("義體人", "C4-H3-B3")]
        return render_entity_set(codes, size=32)

    def test_build_atlas_dims_and_meta(self, sample_frames):
        atlas, table = build_atlas(sample_frames, columns=2)
        assert atlas.size == (64, 64)  # 2 cols × 32, 2 rows（3 幀）
        meta = table["meta"]
        assert meta["frame_size"] == [32, 32]
        assert meta["count"] == 3
        assert meta["columns"] == 2

    def test_frame_rects_within_bounds_and_non_overlapping(self, sample_frames):
        atlas, table = build_atlas(sample_frames, columns=2)
        rects = []
        for name, f in table["frames"].items():
            assert f["x"] + f["w"] <= atlas.width
            assert f["y"] + f["h"] <= atlas.height
            rects.append((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
        for i, r1 in enumerate(rects):
            for r2 in rects[i + 1 :]:
                overlap = not (r1[2] <= r2[0] or r2[2] <= r1[0] or r1[3] <= r2[1] or r2[3] <= r1[1])
                assert not overlap

    def test_cropped_cell_equals_source_frame(self, sample_frames):
        atlas, table = build_atlas(sample_frames, columns=3)
        for name, f in table["frames"].items():
            cell = atlas.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
            assert cell.tobytes() == sample_frames[name].tobytes()

    def test_empty_frames_raise(self):
        with pytest.raises(ValueError):
            build_atlas({})

    def test_mixed_sizes_raise(self, sample_frames):
        sample_frames["bad"] = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        with pytest.raises(ValueError):
            build_atlas(sample_frames)

    def test_zero_columns_raise(self, sample_frames):
        with pytest.raises(ValueError):
            build_atlas(sample_frames, columns=0)

    def test_save_atlas_roundtrip(self, tmp_path, sample_frames):
        png_path, json_path = save_atlas(tmp_path, "unit_atlas", sample_frames, columns=2)
        assert png_path.is_file() and json_path.is_file()
        with Image.open(png_path) as img:
            assert img.mode == "RGBA"
            table = json.loads(json_path.read_text(encoding="utf-8"))
            for name, f in table["frames"].items():
                cell = img.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
                assert cell.tobytes() == sample_frames[name].tobytes()

    def test_duplicate_frame_name_raises(self):
        with pytest.raises(ValueError):
            render_entity_set([("物種", "N-H-P"), ("物種", "N-H-P")])

    def test_frame_name_strips_lineage_prefix(self):
        assert entity_frame_name("物種", "獸娘｜ F-H-P（註）") == "物種_F-H-P"


class TestSyncWithAxisSystem:
    """跨檔同步鎖定：game_sprites.AXIS_POSITIONS 必須逐鍵等於 axis_system.AXIS_SYSTEMS。"""

    def test_profiles_mirror_axis_system_exactly(self, axis_system):
        assert set(AXIS_POSITIONS) == set(axis_system.AXIS_SYSTEMS)
        for profile in AXIS_POSITIONS:
            assert AXIS_POSITIONS[profile] == axis_system.AXIS_SYSTEMS[profile], profile

    def test_group_profiles_cover_all_systems(self, axis_system):
        assert set(GROUP_PROFILES) == set(axis_system.AXIS_SYSTEMS) | {BASE_PROFILE}


class TestCli:
    def test_main_writes_both_atlases(self, tmp_path):
        rc = main([str(tmp_path), "--size", "32", "--columns", "5"])
        assert rc == 0
        for name in (
            "entity_atlas.png",
            "entity_atlas.json",
            "terrain_atlas.png",
            "terrain_atlas.json",
        ):
            assert (tmp_path / name).is_file()
        table = json.loads((tmp_path / "entity_atlas.json").read_text(encoding="utf-8"))
        assert table["meta"]["count"] == len(default_entity_codes())
        assert table["meta"]["frame_size"] == [32, 32]
