# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 組合式遊戲素材生成（液體 / 容器 / 混色 / 素材形狀 / 工具拼接）
# 維度: γ 回應維度（組合式圖像生成）、δ 素材維度
# 安全: 使用 Key A (後端控制)；無真實世界指令執行
# 成熟度: L2+ 等級開始接觸組合式視覺素材
#
# =============================================================================

"""組合式遊戲素材生成（GVV game materials）。

承襲 `primitives/` 組合式圖像生成思想，專為遊戲素材提供可直接組裝的
零件與演算法：

- 混色（X:X:X 零件比例，非百分比；含「反著來 / 捨棄」規則）。
- 液體（液面層級 + 半透明呈現）。
- 容器（杯 / 瓶 / 壺輪廓，並以 mask 裁切液體讓液體「裝在容器內」）。
- 素材（基本色 + 形狀：木材、鐵錠…）。
- 工具（分段零件：頭 / 柄 / 刃 → 縮小對齊拼接成完整工具）。

「水」以天空藍呈現（透明不好做）；「去除大部分藍並保留一點點」等
規則以配方表（recipe）封裝，配方之間可再混色。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]

# ---------------------------------------------------------------------------
# 基礎色
# ---------------------------------------------------------------------------
WATER_BLUE: RGB = (135, 206, 235)  # 天空藍——遊戲中「水」的呈現色
LEMON_YELLOW: RGB = (255, 238, 0)
LEMONADE_WHITE: RGB = (255, 250, 222)  # 檸檬水白（未稀釋）
ROSELLE_RED: RGB = (150, 20, 60)  # 洛神花
PINE_GREEN: RGB = (20, 110, 60)  # 松針
WOOD_BROWN: RGB = (139, 96, 44)
IRON_GRAY: RGB = (160, 162, 166)
STEEL_BLADE: RGB = (210, 214, 218)

# ---------------------------------------------------------------------------
# 混色（X:X:X 零件比例，非百分比）
# ---------------------------------------------------------------------------


def _clamp(v: float, lo: int = 0, hi: int = 255) -> int:
    return max(lo, min(hi, int(round(v))))


def mix_rgb(colors: Sequence[RGB], ratio: Optional[Sequence[int]] = None) -> RGB:
    """X:X:X 零件比例加法混色。

    Args:
        colors: 依序參與混色的基礎色。
        ratio: 各色的「零件數」比例（X:X:X）。省略時等份。
            例: ``mix_rgb([LEMONADE_WHITE, WATER_BLUE], (4, 1))``
            = 4 份檸檬水白 + 1 份天空藍 → 微藍檸檬水。

    Returns:
        混色結果 RGB。非百分比：總份數 = sum(ratio)，各色佔 ratio_i/總份。
    """
    n = len(colors)
    parts = ratio or tuple([1] * n)
    if len(parts) != n or n == 0:
        raise ValueError("ratio must match number of colors")
    if any(p < 0 for p in parts):
        raise ValueError("ratio parts must be non-negative")
    total = sum(parts) or 1
    out = tuple(
        _clamp(sum(c * w for c, w in zip(channel, parts)) / total) for channel in zip(*colors)
    )
    return out  # type: ignore[return-value]


def desaturate(color: RGB, amount: float = 1.0) -> RGB:
    """去除色相、保留亮度（「反著來」：檸檬黃去黃 → 檸檬水白）。

    amount=1.0 → 完全灰階；amount=0 → 原色。
    """
    amount = max(0.0, min(1.0, amount))
    lum = _clamp(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
    return tuple(_clamp(c + (lum - c) * amount) for c in color)  # type: ignore[return-value]


def subtractive_filter(color: RGB, keep: Sequence[bool]) -> RGB:
    """捨棄通道（「捨棄」規則）。

    例: 天空藍 (135,206,235) 去除大部分藍並保留一點點——
    ``subtractive_filter(WATER_BLUE, (True, True, True))`` 保留藍為低值，
    常用於「混色時捨棄過強通道、保留微量」的語意。
    """
    return tuple(_clamp(c * (0.15 if keep else 0.02)) for c, keep in zip(color, keep))  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# 配方（recipe）——把「反著來 / 捨棄 / 比例」封裝成可重用的素材語意
# ---------------------------------------------------------------------------

POTION_RECIPES: Dict[str, RGB] = {}


def _recipe(name: str) -> RGB:
    return POTION_RECIPES[name]


def _init_recipes() -> None:
    # 檸檬水: 檸檬黃去黃 → 檸檬水白（未稀釋）→ 再與天空藍水 4:1 調整
    lemonade_white = desaturate(LEMON_YELLOW, 0.95)
    POTION_RECIPES["lemonade"] = mix_rgb([lemonade_white, WATER_BLUE], (4, 1))
    # 熱水: 水(天空藍) + 熱(暖紅) 3:1
    hot_water = mix_rgb([WATER_BLUE, (255, 140, 100)], (3, 1))
    # 洛神花茶: 洛神花 + 熱水 3:2
    POTION_RECIPES["roselle_tea"] = mix_rgb([ROSELLE_RED, hot_water], (3, 2))
    # 松針水: 松針 + 天空藍水 2:3
    POTION_RECIPES["pine_water"] = mix_rgb([PINE_GREEN, WATER_BLUE], (2, 3))
    # 純水
    POTION_RECIPES["water"] = WATER_BLUE


_init_recipes()


def potion_color(recipe: str) -> RGB:
    """查配方取得成品色。未知配方 fallback 純水。"""
    return POTION_RECIPES.get(recipe, WATER_BLUE)


# ---------------------------------------------------------------------------
# 液體
# ---------------------------------------------------------------------------


@dataclass
class Liquid:
    """液體：基本色 + 液面層級（0=空, 1=滿）。"""

    color: RGB = WATER_BLUE
    level: float = 0.8
    opacity: float = 0.55

    def __post_init__(self) -> None:
        self.level = max(0.0, min(1.0, self.level))
        self.opacity = max(0.0, min(1.0, self.opacity))


# ---------------------------------------------------------------------------
# 容器
# ---------------------------------------------------------------------------


@dataclass
class Container:
    """容器：種類 + 形狀。以 mask 裁切液體，讓液體「裝在容器內」。"""

    kind: str = "cup"  # cup / bottle / teapot
    size: int = 96
    outline: RGB = (80, 84, 90)
    wall: int = 4

    def _polygon(self) -> List[Tuple[float, float]]:
        """容器內部範圍（畫布 size×size，原點中心）。"""
        s = self.size
        if self.kind == "bottle":
            # 瓶：窄口、寬身
            return [
                (s * 0.32, s * 0.18),
                (s * 0.45, s * 0.30),
                (s * 0.45, s * 0.80),
                (s * 0.55, s * 0.80),
                (s * 0.55, s * 0.30),
                (s * 0.68, s * 0.18),
                (s * 0.68, s * 0.08),
                (s * 0.32, s * 0.08),
            ]
        if self.kind == "teapot":
            # 壺：寬身圓肚
            return [
                (s * 0.18, s * 0.42),
                (s * 0.30, s * 0.24),
                (s * 0.70, s * 0.24),
                (s * 0.82, s * 0.42),
                (s * 0.78, s * 0.78),
                (s * 0.22, s * 0.78),
            ]
        # cup：上寬下窄杯
        return [
            (s * 0.22, s * 0.30),
            (s * 0.78, s * 0.30),
            (s * 0.70, s * 0.85),
            (s * 0.30, s * 0.85),
        ]

    def shape(self) -> Image.Image:
        """容器輪廓 RGBA（外透明、內壁可見）。"""
        s = self.size
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pts = self._polygon()
        draw.polygon(pts, outline=self.outline + (255,), width=self.wall)
        return img

    def mask(self) -> Image.Image:
        """容器內部 mask（RGBA）：液體裁切用的二值遮罩。"""
        s = self.size
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 內縮 wall 畫素，避免液體蓋住容器壁
        pts = [(x, y) for (x, y) in self._polygon()]
        # 縮小內壁：向中心收縮 wall
        cx = s / 2
        cy = s * 0.5
        shrink = [(cx + (x - cx) * 0.94, cy + (y - cy) * 0.94) for (x, y) in pts]
        draw.polygon(shrink, fill=(255, 255, 255, 255))
        return img


# ---------------------------------------------------------------------------
# 藥水合成（液體 + 容器）
# ---------------------------------------------------------------------------


def render_potion(
    container: Container,
    liquid: Optional[Liquid] = None,
    recipe: str = "",
) -> Image.Image:
    """把液體裝進容器：液面以下填充液體色，再以容器 mask 裁切。

    視覺語意：液體被容器「裝著」，容器壁外不會溢色。
    """
    if liquid is None:
        liquid = Liquid(color=potion_color(recipe))
    s = container.size
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 液面底線：容器底 10% → 依 level 上移
    top_ratio = 0.85 * (1 - liquid.level) + 0.10
    y_top = int(s * top_ratio)
    draw.rectangle([0, y_top, s, s], fill=liquid.color + (int(255 * liquid.opacity),))

    # 以容器 mask 裁切液體
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), container.mask())

    # 疊上容器輪廓
    out = Image.alpha_composite(out, container.shape())
    return out


# ---------------------------------------------------------------------------
# 素材（基本色 + 形狀）
# ---------------------------------------------------------------------------

MATERIAL_SHAPES: Dict[str, str] = {
    "wood": "ingot",
    "iron": "ingot",
}


@dataclass
class Material:
    """素材：基本色 + 以形狀呈現（木材、鐵錠…）。"""

    name: str = "wood"
    color: RGB = WOOD_BROWN
    size: int = 48

    def render(self) -> Image.Image:
        """以素材形狀呈現（目前：扁錠形 + 圓角）。"""
        s = self.size
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pad = int(s * 0.14)
        draw.rounded_rectangle(
            [pad, pad * 1.6, s - pad, s - pad * 1.6],
            radius=int(s * 0.12),
            fill=self.color + (255,),
        )
        # 高光：讓形狀立體
        hl = int(s * 0.05)
        draw.line(
            [s * 0.28, s * 0.30, s * 0.72, s * 0.30],
            fill=(255, 255, 255, 90),
            width=hl,
        )
        return img


# ---------------------------------------------------------------------------
# 工具（分段零件 → 縮小對齊拼接）
# ---------------------------------------------------------------------------


@dataclass
class ToolPart:
    """工具段：頭 / 柄 / 刃。"""

    kind: str = "handle"  # head / handle / blade
    color: RGB = WOOD_BROWN

    def render(self, h: int = 48) -> Image.Image:
        """以基本色只換形狀呈現單一工具段（高×h，寬按種類）。"""
        w = h
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if self.kind == "handle":
            # 木棍：細長
            draw.rectangle([int(w * 0.40), 2, int(w * 0.60), h - 2], fill=self.color + (255,))
        elif self.kind == "blade":
            # 刀身：上寬下尖
            draw.polygon(
                [(w * 0.5, 2), (w * 0.80, h * 0.45), (w * 0.50, h - 2), (w * 0.20, h * 0.45)],
                fill=self.color + (255,),
            )
        elif self.kind == "head":
            # 鎬頭：橫長兩端收尖（十字鎬）
            draw.polygon(
                [(2, h * 0.40), (w * 0.35, h * 0.30), (w * 0.35, h * 0.50), (2, h * 0.60)],
                fill=self.color + (255,),
            )
            draw.polygon(
                [(w - 2, h * 0.40), (w * 0.65, h * 0.30), (w * 0.65, h * 0.50), (w - 2, h * 0.60)],
                fill=self.color + (255,),
            )
        else:  # 其他：中段
            draw.rectangle([int(w * 0.35), 2, int(w * 0.65), h - 2], fill=self.color + (255,))
        return img


def compose_tool(
    parts: Sequence[ToolPart],
    total_height: int = 48,
    spacing: int = 2,
) -> Image.Image:
    """把工具段縮小對齊並拼接成完整工具。

    以「首段高度」統一各段高度（縮小），水平對齊置中，間距相連。
    例: ``[head(鎬頭), handle(木棍)]`` → 十字鎬。
        ``[handle(刀柄), blade(刀身)]`` → 刀。
    """
    if not parts:
        raise ValueError("compose_tool requires at least one part")
    renders = [p.render(h=total_height) for p in parts]
    widths = [im.width for im in renders]
    total_w = sum(widths) + spacing * (len(parts) - 1)
    canvas = Image.new("RGBA", (total_w, total_height), (0, 0, 0, 0))
    x = 0
    for im in renders:
        canvas.alpha_composite(im, (x, 0))
        x += im.width + spacing
    return canvas


# ---------------------------------------------------------------------------
# 圖像輸出入
# ---------------------------------------------------------------------------


def to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    """RGBA 圖像 → bytes。"""
    import io

    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def render_material_set() -> Dict[str, Image.Image]:
    """渲染一組素材（木材 / 鐵錠）供前端直接使用。"""
    return {
        "wood": Material(name="wood", color=WOOD_BROWN).render(),
        "iron": Material(name="iron", color=IRON_GRAY).render(),
    }
