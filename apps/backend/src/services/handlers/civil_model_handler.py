"""Civil modeling handler: parameters -> calc/DXF/STL/STEP/FEM (chat-callable)."""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys

logger = logging.getLogger(__name__)

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
PY = sys.executable


def _num(text, keys, default):
    for k in keys:
        m = re.search(k + r"\s*[=：:]\s*(\d+(?:\.\d+)?)", text)
        if m:
            return float(m.group(1))
    return default


class CivilModelHandler:
    """Handles civil modeling intents: calc, drawing, 3D, CAD, analysis."""

    def __init__(self, model_bus=None):
        self._model_bus = model_bus

    async def handle(self, text: str, intent: str = "civil") -> str:
        t = text or ""
        try:
            if any(k in t for k in ("FEM", "有限元", "分析", "撓度", "应力", "應力")):
                return await self._fem_beam(t)
            if any(k in t for k in ("STEP", "FreeCAD", "freecad")):
                return await self._freecad_beam(t)
            if any(k in t for k in ("STL", "3D", "三維", "立體", "渲染", "模型")):
                return await self._blender_beam(t)
            if any(k in t for k in ("DXF", "圖紙", "图纸", "截面", "出圖", "drawing")):
                return await self._dxf_section(t)
            return await self._calc(t)
        except Exception as e:
            logger.error(f"CivilModelHandler error: {e}", exc_info=True)
            return f"（結構建模）執行失敗：{e}"

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

    async def _calc(self, text):
        p = self._beam_params(text)
        code, out = await self._run(
            [PY, os.path.join(SCRIPTS, "civil_components.py"), "--component", "beam",
             "--json", json.dumps(p)], 60,
        )
        if code != 0:
            return f"（結構計算）失敗：{out[-300:]}"
        try:
            r = json.loads(out[out.index("{"):out.rindex("}") + 1])
        except Exception:
            return f"（結構計算）解析失敗：{out[-300:]}"
        return (f"（結構計算）梁 b={p['b']:.0f} d={p['d']:.0f} As={p['As']:.0f}："
                f"M_Rd={r.get('M_Rd_kNm')}kNm，x={r.get('x_mm')}mm"
                + (f"，彎矩{'✅' if r.get('bending_ok') else '❌'}" if "bending_ok" in r else ""))

    async def _dxf_section(self, text):
        p = self._beam_params(text)
        code, out = await self._run(
            [PY, os.path.join(SCRIPTS, "civil_dxf.py"), "--b", str(p["b"]),
             "--d", str(p["d"])], 60,
        )
        ok = "✅" in out
        return f"（出圖）梁截面 DXF {'✅ 已生成（data/.cache/beam_section.dxf）' if ok else '❌ ' + out[-200:]}"

    async def _blender_beam(self, text):
        p = self._beam_params(text)
        code, out = await self._run(
            ["blender", "--background", "--python",
             os.path.join(SCRIPTS, "civil_blender.py"), "--",
             "--b", str(p["b"]), "--d", str(p["d"]), "--L", str(p["L"]),
             "--out", "/tmp/girder_chat.stl"], 240,
        )
        ok = "BLENDER:" in out
        return f"（3D 建模）Blender 梁 STL {'✅ /tmp/girder_chat.stl' if ok else '❌ ' + out[-200:]}"

    async def _freecad_beam(self, text):
        p = self._beam_params(text)
        code, out = await self._run(
            [PY, os.path.join(SCRIPTS, "civil_freecad.py"),
             "--b", str(p["b"]), "--d", str(p["d"]), "--L", str(p["L"]),
             "--out", "/tmp/girder_chat.step"], 500,
        )
        ok = "FC-BBOX" in out
        tail = [ln.strip()[:80] for ln in out.splitlines() if "FC-BBOX" in ln]
        return f"（CAD 建模）FreeCAD STEP {'✅ ' + (tail[0] if tail else '') if ok else '❌ ' + out[-200:]}"

    async def _fem_beam(self, text):
        return ("（有限元）完整 FEM 需約 10 分鐘交互會話（flatpak 多次啟動）；"
                "已驗證鏈路：求解器可跑、結果可讀、線性成立（單位標定排隊）。"
                "請先用「梁計算」定參數，再指定載荷工況。")
