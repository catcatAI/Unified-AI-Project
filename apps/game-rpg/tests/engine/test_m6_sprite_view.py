# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M6 測試：§5.2 精靈管線接 render_bridge（計畫 §6.3 M6 驗收）。

驗收（像素層自動化）：實體移動平滑、量化不抖動。附：真實 §5.2 管線載入
（含 editable .pth 條路）、雙保險吸附、負座標裁切、sorted 疊放確定性、
手動冒煙 CLI（motion_sheet/main）。
"""

from __future__ import annotations

import pytest
from engine.render_bridge import RenderBridge, RenderState
from engine.sprite_view import (
    DEFAULT_BACKGROUND,
    SpriteView,
    _backend_src,
    _game_sprites,
    load_entity_sprite,
    main,
    motion_sheet,
)
from PIL import Image, ImageChops


def entity_bbox(frame: Image.Image, background=DEFAULT_BACKGROUND):
    """幀內非背景像素的 bbox（無實體回 None）。"""
    bg = Image.new("RGB", frame.size, background)
    return ImageChops.difference(frame, bg).getbbox()


def sprite_offset(sprite: Image.Image):
    """精靈 alpha bbox 相對貼上原點的偏移（透明邊距）。"""
    bbox = sprite.getchannel("A").getbbox()
    assert bbox is not None
    return bbox[0], bbox[1]


class TestSpritePipeline:
    def test_backend_src_path_exists(self):
        # bootstrap 兜底路徑真實存在（editable .pth 時不觸發，防禦性）
        assert _backend_src().is_dir()

    def test_load_real_game_sprites_module(self):
        mod = _game_sprites()
        assert hasattr(mod, "render_entity_sprite")
        assert hasattr(mod, "AxisCodeError")

    def test_load_entity_sprite_rgba_32(self):
        sprite = load_entity_sprite(size=32)
        assert sprite.mode == "RGBA"
        assert sprite.size == (32, 32)
        # 非全透明（真的畫了東西）
        assert sprite.getchannel("A").getbbox() is not None

    def test_bad_axis_code_raises_loud(self):
        mod = _game_sprites()
        with pytest.raises(mod.AxisCodeError):
            load_entity_sprite(axis_code="Z-9-Z", group_profile="物種")

    def test_bad_size_raises(self):
        with pytest.raises(ValueError, match="size"):
            load_entity_sprite(size=8)


class TestFrameRender:
    def test_frame_size_and_background(self):
        view = SpriteView(width=320, height=180)
        frame = view.render({})
        assert frame.size == (320, 180)
        assert frame.getpixel((0, 0)) == DEFAULT_BACKGROUND

    def test_sprite_appears_at_state_position(self):
        view = SpriteView(width=320, height=180)
        frame = view.render({"a": RenderState("a", 10.0, 20.0)})
        bbox = entity_bbox(frame)
        assert bbox is not None
        ox, oy = sprite_offset(view.sprite)
        assert (bbox[0], bbox[1]) == (10 + ox, 20 + oy)  # 貼上點+精靈透明邊距
        assert bbox[2] <= 42 and bbox[3] <= 52  # 32px 精靈範圍內

    def test_defensive_snap_half_away(self):
        # 雙保險：外部直接餵 7.6/2.4 → 8/2（半遠離零同 M2/M4）
        view = SpriteView(width=320, height=180)
        frame = view.render({"a": RenderState("a", 7.6, 2.4)})
        bbox = entity_bbox(frame)
        assert bbox is not None
        ox, oy = sprite_offset(view.sprite)
        assert (bbox[0], bbox[1]) == (8 + ox, 2 + oy)

    def test_multiple_entities_deterministic_layering(self):
        view = SpriteView(width=320, height=180)
        a = RenderState("a", 30.0, 40.0)
        b = RenderState("b", 40.0, 50.0)
        f1 = view.render({"a": a, "b": b})
        f2 = view.render({"b": b, "a": a})  # 反序插入
        assert f1.tobytes() == f2.tobytes()  # sorted 疊放=確定性

    def test_negative_position_clipped_not_crash(self):
        view = SpriteView(width=320, height=180)
        frame = view.render({"a": RenderState("a", -10.0, -5.0)})
        bbox = entity_bbox(frame)
        assert bbox is not None
        assert bbox[0] == 0 and bbox[1] == 0  # 裁到畫布左上緣

    def test_fully_offscreen_renders_background_only(self):
        view = SpriteView(width=320, height=180)
        frame = view.render({"a": RenderState("a", 999.0, 999.0)})
        assert entity_bbox(frame) is None

    @pytest.mark.parametrize("w,h", [(0, 10), (10, 0)])
    def test_invalid_view_size_raises(self, w, h):
        with pytest.raises(ValueError, match="size"):
            SpriteView(width=w, height=h)


class TestVisualSmokeAcceptance:
    def test_movement_smooth_and_no_jitter_at_pixels(self):
        # M6 驗收（像素層）：30Hz 模擬/144Hz 顯示 —— 移動平滑、量化不抖動
        view = SpriteView(width=320, height=180)
        bridge = RenderBridge(pixel_size=1.0)
        velocity = 720.0  # 同 M4：每顯示幀 5px
        display_hz, sim_hz = 144.0, 30.0

        lefts, widths, heights, k = [], [], [], -1
        for m in range(25):
            t = m / display_hz
            while k < 0 or bridge.curr_time < t:
                k += 1
                sim_t = k / sim_hz
                bridge.push(
                    {"hero": RenderState("hero", velocity * sim_t, 60.0)},
                    sim_time=sim_t,
                )
            frame = view.render_at(bridge, t)
            bbox = entity_bbox(frame)
            assert bbox is not None, f"frame {m}: sprite missing"
            l, top, r, b = bbox
            lefts.append(l)
            widths.append(r - l)
            heights.append(b - top)

        # 移動平滑：左緣嚴格等速 +5px、無跳變/無回跳（回跳=抖動徵兆）
        diffs = [lefts[i + 1] - lefts[i] for i in range(len(lefts) - 1)]
        assert diffs == [5] * len(diffs)
        # 量化不抖動：每幀精靈 bbox 寬高完全一致（無子像素膨脹/閃爍）
        assert len(set(widths)) == 1
        assert len(set(heights)) == 1
        # 絕對位置=5m+精靈透明邊距偏移（首幀 t=0 → 貼上 0）
        ox, _ = sprite_offset(view.sprite)
        assert lefts == [5 * m + ox for m in range(25)]


class TestManualSmokeCLI:
    def test_motion_sheet_shapes(self):
        sheet = motion_sheet(frames=7, columns=3)
        # 3 欄：7 幀 → 3 行；view 預設 240x96
        assert sheet.size == (3 * 240, 3 * 96)

    def test_motion_sheet_frames_move(self):
        sheet = motion_sheet(frames=6, columns=6)
        # 每欄一幀：第一幀與最後一幀的實體位置不同（在動）
        tile_w = 240
        first = sheet.crop((0, 0, tile_w, 96))
        last = sheet.crop((5 * tile_w, 0, 6 * tile_w, 96))
        assert entity_bbox(first) != entity_bbox(last)

    def test_main_writes_png(self, tmp_path):
        out = tmp_path / "smoke.png"
        rc = main(["--out", str(out), "--frames", "6"])
        assert rc == 0
        assert out.is_file()
        with Image.open(out) as img:
            assert img.size[0] > 0 and img.size[1] > 0
