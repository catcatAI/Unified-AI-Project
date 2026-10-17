# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L3]
# =============================================================================
#
# 職責: 軸→視覺契約化繪製（entity sprite 三圖層 / terrain tile / PNG atlas+幀表）
# 維度: γ 回應維度（組合式圖像生成）、δ 素材維度
# 安全: 使用 Key A (後端控制)；純本機 PIL 繪製，無網路/無檔案系統副作用
# 成熟度: L3——軸語意驅動的素材管線（計畫 §5.2）
#
# =============================================================================

"""軸→視覺的契約化精靈繪製（game sprites）。

依《物種分類架構（三軸系統）》之軸位，把 ``(group_profile, axis_code)``
映到視覺特徵（輪廓/配色/金屬高光/發光/透明度），再以 PIL 組出三圖層
``body``/``overlay``/``emissive``，合成 32×32 或 64×64 精靈；亦可打包
PNG atlas + JSON 幀表，另提供 16×16 地形 tile（毒氣區/走廊/湖/市場）。

混色/去色/水藍等基礎語意承襲同家族 ``game_materials.py``。

本模組**不** import `apps/game-rpg`（後端不依賴 CLI 套件）：
``AXIS_POSITIONS`` 是軸位表的**視覺契約鏡像**，
`tests/ai/multimodal/primitives/test_game_sprites.py::TestSyncWithAxisSystem`
以 importlib 讀入 `axis_system.py` 做逐鍵同步鎖定，任何一側漂移即紅。

CLI（內容再生成，輸出不入庫——gitignore 政策：忽略生成資料）::

    python -m ai.multimodal.primitives.game_sprites <out_dir>
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageChops, ImageDraw

from ai.multimodal.primitives.game_materials import WATER_BLUE, to_bytes

RGB = Tuple[int, int, int]

# ---------------------------------------------------------------------------
# 軸位表（視覺契約鏡像——同步鎖定見 test_game_sprites.py）
# ---------------------------------------------------------------------------


class AxisCodeError(ValueError):
    """軸碼無法通過視覺契約驗證（未知 profile／段數不符／軸位不存在）。"""


AXIS_POSITIONS: Dict[str, Dict[str, Dict[str, str]]] = {
    "物種": {
        "原種距離": {"N": "近原種", "S": "標準種", "F": "遠原種"},
        "人形比例": {"H": "類人型", "S": "標準型", "C": "類原型"},
        "混血譜系": {"P": "純血", "M1": "混血（一級）", "M2": "混血（二級）", "M3": "混血（三級）"},
    },
    "AI": {
        "人形模仿度": {"F0": "無形體", "F1": "抽象載體", "F2": "部分人形", "F3": "仿真人形"},
        "自主性": {"A0": "被動型", "A1": "條件型", "A2": "學習型", "A3": "完全自主"},
        "程序開放度": {"O0": "封閉黑箱", "O1": "部分開源", "O2": "完全開源"},
    },
    "義體人": {
        "義體化比例": {
            "C1": "輕度（<30%）",
            "C2": "中度（30%-70%）",
            "C3": "重度（70%-95%）",
            "C4": "全身（>95%）",
        },
        "外觀人形保留度": {"H1": "完全人形", "H2": "部分暴露", "H3": "非人形態"},
        "神經保留度": {"B1": "生物腦完整", "B2": "生物腦增強", "B3": "意識上傳"},
    },
    "神話種": {
        "神性濃度": {"D1": "傳說級", "D2": "信仰級", "D3": "原初級"},
        "原典忠實度": {"O1": "自由改編", "O2": "部分保留", "O3": "高度還原"},
        "存在維度": {"M1": "物質顯形", "M2": "靈體/概念", "M3": "跨維度"},
    },
}

#: 「其他」為人類基線（axis_system.DEFAULT_LINEAGE），無軸譜，軸碼固定 "base"。
BASE_PROFILE = "其他"
GROUP_PROFILES: Tuple[str, ...] = ("物種", "義體人", "AI", "神話種", BASE_PROFILE)

LAYER_ORDER: Tuple[str, ...] = ("body", "overlay", "emissive")
ENTITY_SIZES: Tuple[int, ...] = (32, 64)
TILE_SIZE = 16
TILE_KINDS: Tuple[str, ...] = ("toxic_zone", "corridor", "lake", "market")
ATLAS_META_VERSION = 1

# ---------------------------------------------------------------------------
# 軸位 → 視覺特徵表
# ---------------------------------------------------------------------------

_SPECIES_SIL = {"H": "humanoid", "S": "anthro", "C": "beast"}
_SPECIES_BODY: Dict[str, RGB] = {"N": (150, 110, 70), "S": (176, 146, 110), "F": (214, 204, 196)}
_SPECIES_ACCENT: Dict[str, RGB] = {
    "P": (94, 72, 52),
    "M1": (126, 96, 150),
    "M2": (86, 134, 152),
    "M3": (156, 96, 116),
}

_CYBER_BODY: Dict[str, RGB] = {
    "C1": (168, 172, 178),
    "C2": (150, 155, 162),
    "C3": (132, 138, 146),
    "C4": (110, 118, 128),
}
_CYBER_HIGHLIGHT: Dict[str, float] = {"C1": 0.25, "C2": 0.45, "C3": 0.65, "C4": 0.95}
_CYBER_SIL = {"H1": "humanoid", "H2": "humanoid", "H3": "angular"}
_CYBER_EMISSIVE: Dict[str, float] = {"B1": 0.25, "B2": 0.5, "B3": 0.9}
_CYBER_ACCENT: RGB = (232, 236, 240)

_AI_SIL = {"F0": "point", "F1": "orb", "F2": "partial", "F3": "humanoid"}
_AI_BODY: Dict[str, RGB] = {"O0": (64, 74, 86), "O1": (96, 156, 186), "O2": (144, 204, 232)}
_AI_TRANSPARENCY: Dict[str, float] = {"O0": 0.05, "O1": 0.25, "O2": 0.5}
_AI_ACCENT: RGB = (210, 246, 255)

_MYTH_BODY: Dict[str, RGB] = {"D1": (232, 196, 96), "D2": (216, 176, 124), "D3": (198, 158, 168)}
_MYTH_ACCENT: Dict[str, RGB] = {"O1": (236, 140, 170), "O2": (232, 196, 96), "O3": (246, 240, 214)}
_MYTH_TRANSPARENCY: Dict[str, float] = {"M1": 0.0, "M2": 0.35, "M3": 0.6}
_MYTH_EMISSIVE: Dict[str, float] = {"M1": 0.5, "M2": 0.7, "M3": 0.85}
_MYTH_SIL = {"M1": "humanoid", "M2": "humanoid", "M3": "angular"}

_HUMANOID_BASE: RGB = (196, 164, 132)
_HUMANOID_ACCENT: RGB = (150, 120, 96)


@dataclass(frozen=True)
class EntityTraits:
    """軸位映出的視覺特徵（繪製輸入的唯一契約）。"""

    silhouette: str  # humanoid / anthro / beast / orb / partial / point / angular
    body_color: RGB
    accent_color: RGB
    highlight: float  # 金屬高光強度 0..1（義體 C4 最高）
    emissive: float  # 發光強度 0..1（眼點/光核/光環）
    transparency: float  # 主體透明度 0..1（神話種 M2/M3、AI 開放度）
    overlay_pattern: str  # none / mottle / exposed / circuit / sigil


def _normalize_code(code: str) -> str:
    """去譜系前綴（`獸娘｜ F-H-P…`）與括號註記，回傳純軸碼。"""
    v = str(code).strip()
    for sep in ("｜", "|"):
        if sep in v:
            v = v.split(sep)[-1].strip()
    if "（" in v:
        v = v.split("（", 1)[0].strip()
    return v


def parse_entity_axes(group_profile: str, axis_code: str) -> Tuple[str, ...]:
    """驗證並解析軸碼 → 各軸段碼元組；失敗 raise :class:`AxisCodeError`。

    例：``parse_entity_axes("物種", "N-C-P")`` → ``("N", "C", "P")``。
    """
    if group_profile == BASE_PROFILE:
        if _normalize_code(axis_code) != "base":
            raise AxisCodeError(f"{BASE_PROFILE} 無無軸譜，軸碼須為 'base'，得到 {axis_code!r}")
        return ("base",)
    axes = AXIS_POSITIONS.get(group_profile)
    if axes is None:
        raise AxisCodeError(f"unknown group_profile: {group_profile!r}; expected {GROUP_PROFILES}")
    segs = [s for s in _normalize_code(axis_code).split("-") if s]
    names = list(axes)
    if len(segs) != len(names):
        raise AxisCodeError(
            f"{group_profile} 軸碼段數不符: {axis_code!r} 得 {len(segs)} 段，需 {len(names)} 段"
        )
    for name, seg in zip(names, segs):
        if seg not in axes[name]:
            raise AxisCodeError(
                f"{group_profile}/{name} 無此軸位 {seg!r}; 合法值 {sorted(axes[name])}"
            )
    return tuple(segs)


def entity_traits(group_profile: str, axis_code: str) -> EntityTraits:
    """軸位 → 視覺特徵（契約化繪製的核心映射）。"""
    segs = parse_entity_axes(group_profile, axis_code)
    if group_profile == BASE_PROFILE:
        return EntityTraits(
            silhouette="humanoid",
            body_color=_HUMANOID_BASE,
            accent_color=_HUMANOID_ACCENT,
            highlight=0.2,
            emissive=0.15,
            transparency=0.0,
            overlay_pattern="none",
        )
    if group_profile == "物種":
        origin, form, lineage = segs
        return EntityTraits(
            silhouette=_SPECIES_SIL[form],
            body_color=_SPECIES_BODY[origin],
            accent_color=_SPECIES_ACCENT[lineage],
            highlight=0.15 + (0.1 if origin == "F" else 0.0),
            emissive=0.12,
            transparency=0.0,
            overlay_pattern="none" if lineage == "P" else "mottle",
        )
    if group_profile == "義體人":
        cyber, human, brain = segs
        return EntityTraits(
            silhouette=_CYBER_SIL[human],
            body_color=_CYBER_BODY[cyber],
            accent_color=_CYBER_ACCENT,
            highlight=_CYBER_HIGHLIGHT[cyber],
            emissive=_CYBER_EMISSIVE[brain],
            transparency=0.0,
            overlay_pattern="exposed",
        )
    if group_profile == "AI":
        form, autonomy, openness = segs
        a_idx = int(autonomy[1])  # A0..A3 → 0..3
        return EntityTraits(
            silhouette=_AI_SIL[form],
            body_color=_AI_BODY[openness],
            accent_color=_AI_ACCENT,
            highlight=0.3,
            emissive=0.3 + 0.15 * a_idx,
            transparency=_AI_TRANSPARENCY[openness],
            overlay_pattern="circuit" if a_idx >= 2 else "none",
        )
    # 神話種
    divinity, fidelity, mode = segs
    return EntityTraits(
        silhouette=_MYTH_SIL[mode],
        body_color=_MYTH_BODY[divinity],
        accent_color=_MYTH_ACCENT[fidelity],
        highlight=0.35,
        emissive=_MYTH_EMISSIVE[mode],
        transparency=_MYTH_TRANSPARENCY[mode],
        overlay_pattern="sigil",
    )


# ---------------------------------------------------------------------------
# 幾何繪製（body / overlay / emissive 三圖層）
# ---------------------------------------------------------------------------


def _chan(v: float) -> int:
    return max(0, min(255, int(round(v))))


def _shade(color: RGB, f: float) -> RGB:
    """f<0 變暗、f>0 變亮（向黑/白插值）。"""
    target = 0.0 if f < 0 else 255.0
    t = abs(f)
    return tuple(_chan(c + (target - c) * t) for c in color)  # type: ignore[return-value]


def _draw_silhouette(draw: ImageDraw.ImageDraw, kind: str, s: int, fill: int) -> None:
    """在 L/RGBA draw 上以固定座標系（s×s）畫輪廓形。"""
    u = s  # 直覺單位：所有座標 = 比例 × s

    def rect(x0: float, y0: float, x1: float, y1: float) -> None:
        draw.rectangle([x0 * u, y0 * u, x1 * u, y1 * u], fill=fill)

    if kind == "humanoid":
        draw.ellipse([0.36 * u, 0.06 * u, 0.64 * u, 0.30 * u], fill=fill)
        draw.rounded_rectangle([0.36 * u, 0.28 * u, 0.64 * u, 0.60 * u], radius=0.06 * u, fill=fill)
        rect(0.30, 0.32, 0.37, 0.58)
        rect(0.63, 0.32, 0.70, 0.58)
        rect(0.40, 0.58, 0.48, 0.95)
        rect(0.52, 0.58, 0.60, 0.95)
    elif kind == "anthro":
        draw.ellipse([0.34 * u, 0.08 * u, 0.66 * u, 0.34 * u], fill=fill)
        draw.polygon([(0.36 * u, 0.14 * u), (0.40 * u, 0.02 * u), (0.47 * u, 0.11 * u)], fill=fill)
        draw.polygon([(0.64 * u, 0.14 * u), (0.60 * u, 0.02 * u), (0.53 * u, 0.11 * u)], fill=fill)
        draw.rounded_rectangle([0.34 * u, 0.30 * u, 0.66 * u, 0.72 * u], radius=0.10 * u, fill=fill)
        rect(0.40, 0.70, 0.47, 0.95)
        rect(0.53, 0.70, 0.60, 0.95)
        draw.polygon([(0.34 * u, 0.52 * u), (0.22 * u, 0.40 * u), (0.24 * u, 0.60 * u)], fill=fill)
    elif kind == "beast":
        draw.ellipse([0.10 * u, 0.34 * u, 0.78 * u, 0.70 * u], fill=fill)
        draw.ellipse([0.64 * u, 0.20 * u, 0.92 * u, 0.48 * u], fill=fill)
        draw.polygon([(0.68 * u, 0.24 * u), (0.70 * u, 0.10 * u), (0.78 * u, 0.20 * u)], fill=fill)
        draw.polygon([(0.84 * u, 0.22 * u), (0.88 * u, 0.08 * u), (0.91 * u, 0.22 * u)], fill=fill)
        rect(0.18, 0.62, 0.26, 0.94)
        rect(0.36, 0.62, 0.44, 0.94)
        rect(0.54, 0.62, 0.62, 0.94)
        rect(0.68, 0.60, 0.76, 0.94)
        draw.polygon([(0.12 * u, 0.40 * u), (0.02 * u, 0.24 * u), (0.10 * u, 0.26 * u)], fill=fill)
    elif kind == "orb":
        draw.ellipse([0.20 * u, 0.20 * u, 0.80 * u, 0.80 * u], fill=fill)
    elif kind == "partial":
        draw.ellipse([0.28 * u, 0.16 * u, 0.72 * u, 0.60 * u], fill=fill)
        rect(0.18, 0.34, 0.30, 0.44)
        rect(0.70, 0.34, 0.82, 0.44)
        rect(0.38, 0.58, 0.46, 0.90)
        rect(0.54, 0.58, 0.62, 0.90)
    elif kind == "point":
        draw.ellipse([0.38 * u, 0.38 * u, 0.62 * u, 0.62 * u], fill=fill)
    elif kind == "angular":
        draw.polygon(
            [
                (0.50 * u, 0.00 * u),
                (0.66 * u, 0.14 * u),
                (0.50 * u, 0.28 * u),
                (0.34 * u, 0.14 * u),
            ],
            fill=fill,
        )
        draw.polygon(
            [
                (0.50 * u, 0.26 * u),
                (0.74 * u, 0.40 * u),
                (0.70 * u, 0.66 * u),
                (0.50 * u, 0.76 * u),
                (0.30 * u, 0.66 * u),
                (0.26 * u, 0.40 * u),
            ],
            fill=fill,
        )
        rect(0.36, 0.74, 0.46, 0.96)
        rect(0.54, 0.74, 0.64, 0.96)
    else:  # pragma: no cover - parse 保證 silhouette 皆在表內
        raise ValueError(f"unknown silhouette: {kind!r}")


_EYE_ANCHOR: Dict[str, Tuple[float, float]] = {
    "humanoid": (0.50, 0.19),
    "anthro": (0.50, 0.21),
    "beast": (0.80, 0.33),
    "orb": (0.50, 0.44),
    "partial": (0.50, 0.36),
    "point": (0.50, 0.50),
    "angular": (0.50, 0.13),
}


def _silhouette_mask(traits: EntityTraits, s: int) -> Image.Image:
    mask = Image.new("L", (s, s), 0)
    _draw_silhouette(ImageDraw.Draw(mask), traits.silhouette, s, fill=255)
    return mask


def _render_body(traits: EntityTraits, s: int) -> Image.Image:
    """body：輪廓實心 + 底部陰影 + 依 highlight 強度的頂部金屬高光。"""
    mask = _silhouette_mask(traits, s)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(traits.body_color + (255,), (0, 0), mask)

    # 底部陰影（下 45% 輪廓內變暗）
    lower = Image.new("L", (s, s), 0)
    ImageDraw.Draw(lower).rectangle([0, int(s * 0.55), s, s], fill=255)
    lower = ImageChops.multiply(lower, mask)
    img.paste(_shade(traits.body_color, -0.28) + (255,), (0, 0), lower)

    # 金屬高光：頂部斜帶（白，alpha ∝ highlight，僅輪廓內）
    if traits.highlight > 0:
        band = Image.new("L", (s, s), 0)
        bd = ImageDraw.Draw(band)
        bd.polygon(
            [(0, int(s * 0.08)), (s, int(s * 0.00)), (s, int(s * 0.14)), (0, int(s * 0.24))],
            fill=_chan(255 * traits.highlight),
        )
        band = ImageChops.multiply(band, mask)
        img.paste((255, 255, 255, 255), (0, 0), band)
    return img


def _paint_mottle(draw: ImageDraw.ImageDraw, s: int, traits: EntityTraits) -> None:
    accent = traits.accent_color
    cell = max(3, s // 4)
    for gy in range(0, s, cell):
        for gx in range(0, s, cell):
            if ((gx // cell) * 3 + (gy // cell) * 5) % 7 < 2:
                draw.rectangle([gx, gy, gx + cell - 1, gy + cell - 1], fill=accent + (90,))


def _paint_exposed(draw: ImageDraw.ImageDraw, s: int, traits: EntityTraits) -> None:
    accent = traits.accent_color
    step = max(4, s // 8)
    alpha = _chan(60 + 150 * traits.highlight)
    for x in range(step, s, step):
        draw.line([x, 0, x, s], fill=accent + (alpha,), width=1)
    for px, py in ((0.33, 0.36), (0.66, 0.36), (0.44, 0.68), (0.56, 0.68)):
        r = max(1, s // 14)
        cx, cy = int(px * s), int(py * s)
        draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill=accent + (220,))


def _paint_circuit(draw: ImageDraw.ImageDraw, s: int, traits: EntityTraits) -> None:
    accent = traits.accent_color
    step = max(4, s // 4)
    for gy in range(step // 2, s, step):
        draw.line([0, gy, s, gy], fill=accent + (70,), width=1)
        for gx in range(step // 2, s, step):
            r = max(1, s // 20)
            draw.ellipse([gx - r, gy - r, gx + r, gy + r], fill=accent + (200,))


def _paint_sigil(draw: ImageDraw.ImageDraw, s: int, traits: EntityTraits) -> None:
    accent = traits.accent_color
    scx, scy = s * 0.5, s * 0.42
    r = max(2, s // 7)
    draw.polygon(
        [
            (scx, scy - r),
            (scx + r * 0.35, scy - r * 0.35),
            (scx + r, scy),
            (scx + r * 0.35, scy + r * 0.35),
            (scx, scy + r),
            (scx - r * 0.35, scy + r * 0.35),
            (scx - r, scy),
            (scx - r * 0.35, scy - r * 0.35),
        ],
        fill=accent + (180,),
    )


_OVERLAY_PAINTERS: Dict[str, Callable[[ImageDraw.ImageDraw, int, EntityTraits], None]] = {
    "mottle": _paint_mottle,
    "exposed": _paint_exposed,
    "circuit": _paint_circuit,
    "sigil": _paint_sigil,
}


def _render_overlay(traits: EntityTraits, s: int) -> Image.Image:
    """overlay：紋樣（限輪廓內）。"""
    pattern = traits.overlay_pattern
    if pattern == "none":
        return Image.new("RGBA", (s, s), (0, 0, 0, 0))
    painter = _OVERLAY_PAINTERS.get(pattern)
    if painter is None:  # pragma: no cover - parse 保證皆在表內
        raise ValueError(f"unknown overlay_pattern: {pattern!r}")
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    painter(ImageDraw.Draw(layer), s, traits)
    # 限縮在輪廓內
    mask = _silhouette_mask(traits, s)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    return layer


def _render_emissive(traits: EntityTraits, s: int) -> Image.Image:
    """emissive：眼點（恆有，alpha ∝ emissive）+ 高發光時的光核/光環。"""
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    em = max(0.0, min(1.0, traits.emissive))
    eye_a = _chan(60 + 195 * em)
    ex, ey = _EYE_ANCHOR[traits.silhouette]
    r = max(1, s // 16)
    for dx in (-0.05, 0.05):
        cx, cy = (ex + dx) * s, ey * s
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=traits.accent_color + (eye_a,))
    if traits.silhouette in ("point", "orb", "partial") and em >= 0.3:
        # 光核：同心減衰
        cx = cy = s * 0.5
        for ring, a in ((0.30, 60), (0.20, 120), (0.11, 220)):
            rr = s * ring
            draw.ellipse(
                [cx - rr, cy - rr, cx + rr, cy + rr],
                fill=traits.accent_color + (_chan(a * em),),
            )
    if em >= 0.5:
        # 光環：輪廓外擴 2px 的橢圓描邊
        m = max(2, s // 16)
        draw.ellipse(
            [m, m, s - m, s - m],
            outline=traits.accent_color + (_chan(160 * em),),
            width=max(1, s // 32 + 1),
        )
    return layer


def _render_layers_from_traits(traits: EntityTraits, size: int) -> Dict[str, Image.Image]:
    return {
        "body": _render_body(traits, size),
        "overlay": _render_overlay(traits, size),
        "emissive": _render_emissive(traits, size),
    }


def render_entity_layers(
    axis_code: str, group_profile: str, size: int = 64
) -> Dict[str, Image.Image]:
    """三圖層分離繪製：回傳 ``{body, overlay, emissive}``（皆 size×size RGBA）。"""
    if size < 16:
        raise ValueError(f"size must be >= 16, got {size}")
    return _render_layers_from_traits(entity_traits(group_profile, axis_code), size)


def render_entity_sprite(axis_code: str, group_profile: str, size: int = 64) -> Image.Image:
    """合成精靈（body → overlay → emissive 依序 alpha 合成，再套主體透明度）。"""
    if size < 16:
        raise ValueError(f"size must be >= 16, got {size}")
    traits = entity_traits(group_profile, axis_code)
    layers = _render_layers_from_traits(traits, size)
    out = Image.alpha_composite(layers["body"], layers["overlay"])
    out = Image.alpha_composite(out, layers["emissive"])
    if traits.transparency > 0:
        alpha = out.getchannel("A").point(lambda a: _chan(a * (1.0 - traits.transparency)))
        out.putalpha(alpha)
    return out


def traits_transparency(group_profile: str, axis_code: str) -> float:
    """便捷：主體透明度（AI 開放度／神話種存在維度）。"""
    return entity_traits(group_profile, axis_code).transparency


# ---------------------------------------------------------------------------
# 地形 tile（16×16，對空間群組）
# ---------------------------------------------------------------------------


def _tile_corridor(draw: ImageDraw.ImageDraw, s: int) -> None:
    draw.rectangle([0, 0, s, s], fill=(92, 92, 100, 255))
    wall = max(2, s // 4)
    draw.rectangle([0, 0, s, wall], fill=(52, 54, 60, 255))
    draw.rectangle([0, s - wall, s, s], fill=(52, 54, 60, 255))
    for x in (s // 3, (2 * s) // 3):
        draw.line([x, wall, x, s - wall], fill=(120, 120, 130, 255), width=1)


def _tile_lake(draw: ImageDraw.ImageDraw, s: int) -> None:
    draw.rectangle([0, 0, s, s], fill=WATER_BLUE + (255,))
    deep = _shade(WATER_BLUE, -0.25)
    draw.rectangle([0, int(s * 0.7), s, s], fill=deep + (255,))
    wave = (200, 235, 248, 255)
    for wy, (wx0, wx1) in (
        (s // 4 + 1, (1, s // 3)),
        (s // 2, (s // 2, (5 * s) // 6)),
        ((3 * s) // 4 - 1, (s // 4, (2 * s) // 3)),
    ):
        draw.line([wx0, wy, max(wx0 + 1, wx1), wy], fill=wave, width=1)


def _tile_toxic(draw: ImageDraw.ImageDraw, s: int) -> None:
    draw.rectangle([0, 0, s, s], fill=(74, 108, 58, 255))
    draw.rectangle([0, 0, s // 3, s // 3], fill=(58, 86, 46, 255))
    draw.rectangle([(2 * s) // 3, (2 * s) // 3, s, s], fill=(64, 96, 50, 255))
    bubble = (158, 196, 120, 255)
    for bx, by in ((s // 4, (2 * s) // 3), (s // 2, s // 3), ((3 * s) // 4, s // 2)):
        r = max(1, s // 12)
        draw.ellipse([bx - r, by - r, bx + r, by + r], fill=bubble)


def _tile_market(draw: ImageDraw.ImageDraw, s: int) -> None:
    draw.rectangle([0, 0, s, s], fill=(148, 108, 78, 255))
    band = max(2, s // 4)
    awning = [(178, 60, 56, 255), (238, 230, 216, 255)]
    for i, x in enumerate(range(0, s, 2)):
        draw.rectangle([x, 0, x + 1, band], fill=awning[i % 2])
    crate = (176, 132, 64, 255)
    edge = (132, 96, 44, 255)
    for cx0, cy0 in ((s // 6, (2 * s) // 3), ((3 * s) // 5, (3 * s) // 5)):
        cw = max(3, s // 4)
        draw.rectangle([cx0, cy0, cx0 + cw, cy0 + cw], fill=crate, outline=edge, width=1)


_TERRAIN_PAINTERS: Dict[str, Callable[[ImageDraw.ImageDraw, int], None]] = {
    "corridor": _tile_corridor,
    "lake": _tile_lake,
    "toxic_zone": _tile_toxic,
    "market": _tile_market,
}


def render_terrain_tile(kind: str, size: int = TILE_SIZE) -> Image.Image:
    """空間群組地形 tile：毒氣區 / 走廊 / 湖 / 市場（計畫 §5.2-2）。"""
    if size < 8:
        raise ValueError(f"tile size must be >= 8, got {size}")
    painter = _TERRAIN_PAINTERS.get(kind)
    if painter is None:
        raise ValueError(f"unknown terrain kind: {kind!r}; expected one of {TILE_KINDS}")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    painter(ImageDraw.Draw(img), size)
    return img


# ---------------------------------------------------------------------------
# Atlas + JSON 幀表
# ---------------------------------------------------------------------------


def build_atlas(
    frames: Dict[str, Image.Image], columns: int = 8
) -> Tuple[Image.Image, Dict[str, object]]:
    """同尺寸精靈打包成網格 atlas + JSON 幀表（名稱排序、決定性排版）。

    Returns:
        (atlas RGBA 圖, 幀表 dict：``{"meta": {...}, "frames": {name: {x,y,w,h}}}``)
    """
    if not frames:
        raise ValueError("frames must not be empty")
    if columns < 1:
        raise ValueError(f"columns must be >= 1, got {columns}")
    sizes = {im.size for im in frames.values()}
    if len(sizes) != 1:
        raise ValueError(f"all frames must share one size, got {sorted(sizes)}")
    w, h = sizes.pop()
    cols = min(columns, len(frames))
    rows = math.ceil(len(frames) / cols)
    atlas = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
    table: Dict[str, object] = {
        "meta": {
            "version": ATLAS_META_VERSION,
            "generator": "ai.multimodal.primitives.game_sprites",
            "frame_size": [w, h],
            "columns": cols,
            "count": len(frames),
        },
        "frames": {},
    }
    frames_tbl: Dict[str, Dict[str, int]] = table["frames"]  # type: ignore[assignment]
    for i, name in enumerate(sorted(frames)):
        x = (i % cols) * w
        y = (i // cols) * h
        atlas.paste(frames[name], (x, y))
        frames_tbl[name] = {"x": x, "y": y, "w": w, "h": h}
    return atlas, table


def save_atlas(
    out_dir: Path, name: str, frames: Dict[str, Image.Image], columns: int = 8
) -> Tuple[Path, Path]:
    """打包並寫出 ``<name>.png`` + ``<name>.json``（生成資料不入庫）。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    atlas, table = build_atlas(frames, columns=columns)
    png_path = out / f"{name}.png"
    json_path = out / f"{name}.json"
    atlas.save(png_path, format="PNG")
    json_path.write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return png_path, json_path


def entity_frame_name(group_profile: str, axis_code: str) -> str:
    """精靈幀名：``物種_N-C-P``（去譜系前綴，保證 atlas 內唯一）。"""
    return f"{group_profile}_{_normalize_code(axis_code)}"


def render_entity_set(codes: Sequence[Tuple[str, str]], size: int = 64) -> Dict[str, Image.Image]:
    """批量渲染 ``[(group_profile, axis_code), ...]`` → 幀 dict。"""
    out: Dict[str, Image.Image] = {}
    for profile, code in codes:
        name = entity_frame_name(profile, code)
        if name in out:
            raise ValueError(f"duplicate frame name: {name!r}")
        out[name] = render_entity_sprite(code, profile, size=size)
    return out


def default_entity_codes() -> Tuple[Tuple[str, str], ...]:
    """預設內容花名冊：四軸系×代表性軸位（含計畫例：物種 N-C-P、義體 C4）。"""
    return (
        ("物種", "N-H-P"),
        ("物種", "S-S-P"),
        ("物種", "F-C-M2"),
        ("物種", "N-C-P"),  # 計畫例：類原型→獸形輪廓
        ("義體人", "C1-H1-B1"),
        ("義體人", "C2-H2-B2"),
        ("義體人", "C4-H3-B3"),  # 計畫例：全身義體→金屬高光+意識上傳光
        ("AI", "F0-A0-O0"),
        ("AI", "F1-A1-O0"),
        ("AI", "F3-A3-O2"),
        ("神話種", "D1-O3-M1"),
        ("神話種", "D3-O1-M1"),
        ("神話種", "D2-O2-M2"),
        (BASE_PROFILE, "base"),
    )


def render_terrain_set(size: int = TILE_SIZE) -> Dict[str, Image.Image]:
    """全部地形 kind 的 tile dict（幀名 ``terrain_<kind>``）。"""
    return {f"terrain_{kind}": render_terrain_tile(kind, size) for kind in TILE_KINDS}


def to_png_bytes(img: Image.Image) -> bytes:
    """RGBA 圖 → PNG bytes（承襲 game_materials.to_bytes）。"""
    return to_bytes(img, "PNG")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    """再生成 entity/terrain atlas 到指定目錄（供 M6 內容灌入）。"""
    parser = argparse.ArgumentParser(description="Generate game sprite atlases")
    parser.add_argument("out_dir", type=Path, help="output directory for atlas png/json")
    parser.add_argument("--size", type=int, default=64, choices=ENTITY_SIZES)
    parser.add_argument("--columns", type=int, default=8)
    args = parser.parse_args(argv)

    entity = render_entity_set(default_entity_codes(), size=args.size)
    p1, p2 = save_atlas(args.out_dir, "entity_atlas", entity, columns=args.columns)
    terrain = render_terrain_set()
    p3, p4 = save_atlas(args.out_dir, "terrain_atlas", terrain, columns=args.columns)
    for p in (p1, p2, p3, p4):
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
