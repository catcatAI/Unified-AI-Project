# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""組合式遊戲素材生成測試（game_materials — 液體/容器/混色/素材/工具）。

覆蓋使用者的混色語意：
- X:X:X 零件比例（非百分比）
- 反著來（檸檬黃去黃 → 檸檬水白）與捨棄（去大部分藍留微量）
- 液體裝進容器（mask 裁切不溢色）
- 素材基本色+形狀、工具段縮小對齊拼接
"""

import pytest
from ai.multimodal.primitives.game_materials import (
    LEMON_YELLOW,
    LEMONADE_WHITE,
    WATER_BLUE,
    Container,
    Liquid,
    Material,
    ToolPart,
    compose_tool,
    desaturate,
    mix_rgb,
    potion_color,
    render_potion,
    subtractive_filter,
    to_bytes,
)


class TestColorMixing:
    def test_mix_rgb_equal_parts(self):
        # 黑(0,0,0) + 白(255,255,255) 1:1 = 灰(128,128,128)
        assert mix_rgb([(0, 0, 0), (255, 255, 255)], (1, 1)) == (128, 128, 128)

    def test_mix_rgb_x_x_x_parts_not_percent(self):
        # 4 份檸檬水白 + 1 份天空藍：零件比例加法（非 50%/50%）
        out = mix_rgb([LEMONADE_WHITE, WATER_BLUE], (4, 1))
        # 4/5 * 255 + 1/5 * 135 = 204 + 27 = 231 (R 通道接近檸檬水白)
        assert out[0] == round(LEMONADE_WHITE[0] * 4 / 5 + WATER_BLUE[0] * 1 / 5)
        assert out[1] == round(LEMONADE_WHITE[1] * 4 / 5 + WATER_BLUE[1] * 1 / 5)

    def test_mix_rgb_ratio_mismatch_raises(self):
        with pytest.raises(ValueError):
            mix_rgb([(0, 0, 0), (255, 255, 255)], (1, 1, 1))

    def test_mix_rgb_clamps_out_of_range(self):
        assert mix_rgb([(300, 0, -10), (0, 255, 255)], (1, 0)) == (255, 0, 0)

    def test_desaturate_removes_hue_to_white(self):
        # 檸檬黃去黃 → 檸檬水白：完全灰階時三通道相等（明亮度）
        gray = desaturate(LEMON_YELLOW, 1.0)
        assert gray[0] == gray[1] == gray[2]
        assert gray[0] > 128  # 檸檬黃明亮 → 白

    def test_desaturate_zero_is_noop(self):
        assert desaturate(LEMON_YELLOW, 0.0) == LEMON_YELLOW

    def test_subtractive_filter_keeps_trace(self):
        # 捨棄大部分藍、保留微量：藍通道遠低於原本的天空藍
        out = subtractive_filter(WATER_BLUE, (True, True, True))
        assert out[2] < WATER_BLUE[2] / 2


class TestRecipes:
    def test_lemonade_is_whiteish_blue(self):
        color = potion_color("lemonade")
        # 檸檬水：接近白、微微藍（B > R，藍多於紅）
        assert color[0] > 200  # 偏白
        assert color[2] >= color[0]

    def test_roselle_tea_is_red_toned(self):
        color = potion_color("roselle_tea")
        assert color[0] > color[1]  # 紅主導
        assert color[0] > color[2]

    def test_pine_water_is_green_toned(self):
        color = potion_color("pine_water")
        assert color[1] > color[0]  # 綠通道最高

    def test_unknown_recipe_falls_back_to_water(self):
        assert potion_color("nope") == WATER_BLUE

    def test_water_is_sky_blue(self):
        assert potion_color("water") == WATER_BLUE


class TestLiquidInContainer:
    def test_render_potion_returns_rgba_image(self):
        img = render_potion(Container(size=96), recipe="lemonade")
        assert img.size == (96, 96)
        assert img.mode == "RGBA"

    def test_liquid_does_not_escape_container_mask(self):
        # 液體被 mask 裁切：角落(容器外)應透明
        img = render_potion(Container(size=64), Liquid(color=WATER_BLUE, level=1.0))
        # 畫布角落 (2,2) 在容器外 → alpha 0
        assert img.getpixel((2, 2))[3] == 0
        # 容器中心有液體
        assert img.getpixel((32, 32))[3] > 0

    def test_level_zero_liquid_absent(self):
        # level=0 → 液面在底；中心 (32,32) 無液體填充（僅容器壁）
        empty = render_potion(Container(size=64), Liquid(color=WATER_BLUE, level=0.0))
        full = render_potion(Container(size=64), Liquid(color=WATER_BLUE, level=1.0))
        empty_px = empty.getpixel((32, 32))
        full_px = full.getpixel((32, 32))
        assert full_px[3] > 0  # 滿液面中心不透明
        assert empty_px[3] == 0  # 空液面中心無液體

    def test_water_displayed_not_fully_transparent(self):
        img = render_potion(Container(size=48), Liquid(color=WATER_BLUE, level=1.0))
        center = img.getpixel((24, 40))
        assert center[3] > 0
        # 天空藍：B 通道明顯
        assert center[2] >= center[0]


class TestMaterial:
    def test_material_renders_shape(self):
        img = Material(name="wood", size=48).render()
        assert img.mode == "RGBA"
        assert img.size == (48, 48)
        # 形狀區域內有不透明像素
        pixels_with_alpha = sum(1 for px in img.getdata() if px[3] == 255)
        assert pixels_with_alpha > 0


class TestToolComposition:
    def test_compose_tool_joins_parts(self):
        pickaxe = compose_tool(
            [ToolPart(kind="head"), ToolPart(kind="handle")],
            total_height=48,
        )
        # 兩段拼接：寬度 = 兩段寬 + 間距
        assert pickaxe.width == 48 + 48 + 2
        assert pickaxe.height == 48

    def test_sword_handle_plus_blade(self):
        sword = compose_tool(
            [ToolPart(kind="handle", color=(100, 60, 20)), ToolPart(kind="blade")],
            total_height=48,
        )
        assert sword.width == 48 + 48 + 2
        # 刀刃段中心（x = handle 48 + spacing 2 + blade 中心 24 = 74）不透明
        assert sword.getpixel((48 + 2 + 24, 24))[3] > 0

    def test_compose_tool_requires_parts(self):
        with pytest.raises(ValueError):
            compose_tool([])


class TestIO:
    def test_to_bytes_png(self):
        img = render_potion(Container(size=32))
        data = to_bytes(img)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
