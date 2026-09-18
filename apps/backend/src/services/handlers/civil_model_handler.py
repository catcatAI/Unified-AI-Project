"""Civil modeling handler: parameters -> calc/DXF/STL/STEP/FEM (chat-callable)."""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys

logger = logging.getLogger(__name__)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
PY = sys.executable

# 非結構守衛（與 classifier _CIVIL_FALSE_POSITIVE 同源）：主板/電路板/黑板
# 含「板」字但非土木構件；主流程分類器已攔，此為末端直調的第二道門。
# 注意：裸「板」（樓板/板配筋）是合法土木輸入，不得攔。
_NON_STRUCTURAL = re.compile(
    r"(主板|主機板|主机板|電路板|电路板|\bPCB\b|黑板|平板電腦|平板电脑|" r"\bB\d{3,4}[A-Z]*\b)",
    re.IGNORECASE,
)


def _num(text, keys, default):
    for k in keys:
        # 單字母鍵防子串誤撞（如 M_Ed=400 中的 d=）：鍵前須非字母/下劃線
        m = re.search(r"(?<![A-Za-z_])" + k + r"\s*[=：:]\s*(\d+(?:\.\d+)?)", text)
        if m:
            return float(m.group(1))
    return default


class CivilModelHandler:
    """Handles civil modeling intents: calc, drawing, 3D, CAD, analysis."""

    def __init__(self, model_bus=None):
        self._model_bus = model_bus

    async def handle(self, text: str, intent: str = "civil") -> str:
        t = text or ""
        if _NON_STRUCTURAL.search(t):
            return "（結構建模）非結構構件請求：主板/電路板/黑板不在土木範圍。"
        try:
            if any(k in t for k in ("FEM", "有限元", "撓度", "挠度")):
                return await self._fem_beam(t)
            if any(k in t for k in ("STEP", "FreeCAD", "freecad")):
                return await self._freecad_beam(t)
            if any(k in t for k in ("STL", "3D", "三維", "立體", "渲染", "模型")):
                return await self._blender_beam(t)
            comp = self._detect_component(t)
            # 出圖器只會畫梁截面：非梁構件（如柱截面計算）不得進 DXF，
            # 否則柱查詢會拿到一張梁圖（曾實測誤入）。
            if comp == "beam" and any(
                k in t for k in ("DXF", "圖紙", "图纸", "截面", "出圖", "drawing")
            ):
                return await self._dxf_section(t)
            if any(
                k in t for k in ("配多少", "配筋多少", "需要多少", "設計", "设计", "size", "sizing")
            ):
                return await self._size(t, comp)
            if comp != "beam":
                return await self._calc_component(t, comp)
            return await self._calc(t)
        except Exception as e:
            logger.error(f"CivilModelHandler error: {e}", exc_info=True)
            return f"（結構建模）執行失敗：{e}"

    @staticmethod
    def _detect_component(text):
        for comp, keys in [
            ("column", ["柱", "column", "墩", "pier"]),
            ("slab", ["板", "slab", "樓板"]),
            ("box", ["箱", "box", "箱梁"]),
            ("tbeam", ["T梁", "T梁", "tbeam", "t-beam"]),
            ("steel", ["鋼", "钢", "steel", "桁架", "truss", "桿件"]),
            ("prestressed", ["預力", "预力", "prestress", "預應力", "预应力"]),
        ]:
            if any(k in text for k in keys):
                return comp
        return "beam"

    def _beam_params(self, text):
        return {
            "b": _num(text, ["b", "寬", "宽"], 300.0),
            "d": _num(text, ["d", "高"], 450.0),
            "L": _num(text, ["L", "跨", "長", "长"], 6000.0),
            "As": _num(text, ["As", "配筋"], 1256.0),
        }

    async def _run(self, cmd, timeout):
        try:
            p = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, timeout=timeout
            )
            return p.returncode, (p.stdout + p.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            return 124, "超時"

    async def _calc(self, text) -> str:
        p = self._beam_params(text)
        code, out = await self._run(
            [
                PY,
                os.path.join(SCRIPTS, "civil_components.py"),
                "--component",
                "beam",
                "--json",
                json.dumps(p),
            ],
            60,
        )
        if code != 0:
            return f"（結構計算）失敗：{out[-300:]}"
        try:
            r = json.loads(out[out.index("{") : out.rindex("}") + 1])
        except Exception:
            return f"（結構計算）解析失敗：{out[-300:]}"
        return (
            f"（結構計算）梁 b={p['b']:.0f} d={p['d']:.0f} As={p['As']:.0f}："
            f"M_Rd={r.get('M_Rd_kNm')}kNm，x={r.get('x_mm')}mm"
            + (f"，彎矩{'✅' if r.get('bending_ok') else '❌'}" if "bending_ok" in r else "")
        )

    SIZE_VARY = {
        "beam": "As",
        "column": "As",
        "slab": "As",
        "box": "As",
        "tbeam": "As",
        "steel": "A",
        "prestressed": "P_kN",
    }

    async def _size(self, text, comp) -> str:
        vary = self.SIZE_VARY.get(comp, "As")
        p = {k: v for k, v in self._all_vals(text).items() if k in self.COMP_KEYS[comp]}
        code, out = await self._run(
            [
                PY,
                os.path.join(SCRIPTS, "civil_autosize.py"),
                "--component",
                comp,
                "--vary",
                vary,
                "--json",
                json.dumps(p),
            ],
            120,
        )
        if code != 0:
            return f"（定尺寸）失敗：{out[-300:]}"
        try:
            r = json.loads(out[out.index("{") : out.rindex("}") + 1])
        except Exception:
            return f"（定尺寸）解析失敗：{out[-300:]}"
        if not r.get("ok"):
            return f"（定尺寸）不可達：{r.get('reason', '')[:120]}"
        # autosize 下界直通時鍵為 value 而非 vary 名（如 As），兩鍵兼容。
        return f"（定尺寸）{comp} {vary}={r.get(vary, r.get('value'))} ✅"

    COMP_KEYS = {
        "beam": ["b", "d", "As", "M_Ed_kNm", "V_Ed_kN", "Asw_s", "L"],
        "column": ["b", "h", "As", "N_Ed_kN"],
        "slab": ["h", "cover", "As", "M_Ed_kNm"],
        "box": ["B", "H", "tw", "tf_top", "tf_bot", "As", "M_Ed_kNm"],
        "tbeam": ["bw", "hf", "l0", "bi", "d", "As", "M_Ed_kNm"],
        "steel": ["A", "Iy", "L", "N_Ed_kN"],
        "prestressed": ["b", "h", "P_kN", "e_mm", "M_kNm"],
    }
    COMP_NUM_KEYS = [
        "b",
        "h",
        "d",
        "L",
        "As",
        "B",
        "H",
        "tw",
        "tf_top",
        "tf_bot",
        "bw",
        "hf",
        "l0",
        "bi",
        "A",
        "Iy",
        "N_Ed_kN",
        "M_Ed_kNm",
        "M_kNm",
        "P_kN",
        "e_mm",
        "cover",
        "Asw_s",
        "V_Ed_kN",
    ]

    @staticmethod
    def _all_vals(text):
        num = lambda keys, default: _num(text, keys, default)
        return {
            "b": num(["b", "寬", "宽"], 300.0),
            "h": num(["h"], 300.0),
            "d": num(["d", "高"], 450.0),
            "L": num(["L", "跨", "長", "长"], 6000.0),
            "As": num(["As", "配筋"], 1256.0),
            "B": num(["B"], 8000.0),
            "H": num(["H"], 2000.0),
            "tw": num(["tw"], 300.0),
            "tf_top": num(["tf_top"], 250.0),
            "tf_bot": num(["tf_bot"], 250.0),
            "bw": num(["bw"], 300.0),
            "hf": num(["hf"], 150.0),
            "l0": num(["l0"], 20000.0),
            "bi": num(["bi"], 2000.0),
            "A": num(["A"], 7600.0),
            "Iy": num(["Iy"], 45.9e6),
            "N_Ed_kN": num(["N_Ed", "軸力", "轴力"], 0.0),
            "M_Ed_kNm": num(["M_Ed", "彎矩", "弯矩"], 0.0),
            "M_kNm": num(["M_kNm"], 8000.0),
            "P_kN": num(["P_kN", "預力", "预力"], 12000.0),
            "e_mm": num(["e_mm", "偏心"], 500.0),
            "cover": num(["cover"], 40.0),
            "Asw_s": 0.0,
            "V_Ed_kN": 0.0,
        }

    async def _calc_component(self, text, comp) -> str:
        p = {k: v for k, v in self._all_vals(text).items() if k in self.COMP_KEYS[comp]}
        code, out = await self._run(
            [
                PY,
                os.path.join(SCRIPTS, "civil_components.py"),
                "--component",
                comp,
                "--json",
                json.dumps(p),
            ],
            60,
        )
        if code != 0:
            return f"（結構計算）失敗：{out[-300:]}"
        try:
            r = json.loads(out[out.index("{") : out.rindex("}") + 1])
        except Exception:
            return f"（結構計算）解析失敗：{out[-300:]}"
        keys = [
            k
            for k in (
                "M_Rd_kNm",
                "N_Rd_kN",
                "N_t_Rd_kN",
                "N_b_Rd_kN",
                "M_Rd_kNm_per_m",
                "sigma_top_MPa",
                "self_weight_kN_m",
                "beff_mm",
            )
            if k in r
        ]
        oks = [
            k
            for k in ("bending_ok", "axial_ok", "tension_ok", "buckling_ok", "stress_ok")
            if k in r
        ]
        detail = "，".join(f"{k}={r[k]}" for k in keys[:4])
        verdict = "".join(f"{'✅' if r[k] else '❌'}" for k in oks)
        return f"（結構計算）{comp}：{detail}{verdict}"

    async def _dxf_section(self, text) -> str:
        p = self._beam_params(text)
        code, out = await self._run(
            [PY, os.path.join(SCRIPTS, "civil_dxf.py"), "--b", str(p["b"]), "--d", str(p["d"])],
            60,
        )
        ok = "✅" in out
        return f"（出圖）梁截面 DXF {'✅ 已生成（data/.cache/beam_section.dxf）' if ok else '❌ ' + out[-200:]}"

    async def _blender_beam(self, text) -> str:
        p = self._beam_params(text)
        code, out = await self._run(
            [
                "blender",
                "--background",
                "--python",
                os.path.join(SCRIPTS, "civil_blender.py"),
                "--",
                "--b",
                str(p["b"]),
                "--d",
                str(p["d"]),
                "--L",
                str(p["L"]),
                "--out",
                "/tmp/girder_chat.stl",
            ],
            240,
        )
        ok = "BLENDER:" in out
        return (
            f"（3D 建模）Blender 梁 STL {'✅ /tmp/girder_chat.stl' if ok else '❌ ' + out[-200:]}"
        )

    async def _freecad_beam(self, text) -> str:
        p = self._beam_params(text)
        code, out = await self._run(
            [
                PY,
                os.path.join(SCRIPTS, "civil_freecad.py"),
                "--b",
                str(p["b"]),
                "--d",
                str(p["d"]),
                "--L",
                str(p["L"]),
                "--out",
                "/tmp/girder_chat.step",
            ],
            500,
        )
        ok = "FC-BBOX" in out
        tail = [ln.strip()[:80] for ln in out.splitlines() if "FC-BBOX" in ln]
        return f"（CAD 建模）FreeCAD STEP {'✅ ' + (tail[0] if tail else '') if ok else '❌ ' + out[-200:]}"

    async def _fem_beam(self, text) -> str:
        return (
            "（有限元）完整 FEM 需約 10 分鐘交互會話（flatpak 多次啟動）；"
            "已驗證鏈路：求解器可跑、結果可讀、線性成立（單位標定排隊）。"
            "請先用「梁計算」定參數，再指定載荷工況。"
        )
