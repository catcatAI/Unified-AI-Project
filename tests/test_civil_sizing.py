"""Civil sizing chain guards (R5): verdict keys, autosize, handler routing.

零需求誤判「不可達」修復 + steel/prestressed 定尺寸 + 終驗 + 非結構守衛。
Pure checks import scripts directly (no subprocess); handler tests run the
real scripts (seconds each, verified artifacts, no mocks).
"""

import asyncio
import json
import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import civil_components as cc
from civil_autosize import FUNCS, size

DB_PATH = os.path.join(PROJECT_ROOT, "data", "materials", "civil_materials.json")


@pytest.fixture(scope="module")
def db():
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestVerdictKeysAlwaysEmitted:
    """零需求時 verdict 鍵必須存在（空真），否則 autosize 誤判不可達。"""

    def test_beam_zero_demand(self, db):
        r = cc.beam(db, b=300, d=500, As=1256, M_Ed_kNm=0.0)
        assert r["bending_ok"] is True

    def test_column_zero_demand(self, db):
        r = cc.column(db, b=400, h=400, As=1608, N_Ed_kN=0.0)
        assert r["axial_ok"] is True

    def test_slab_zero_demand(self, db):
        r = cc.slab(db, h=150, cover=25, As=500, M_Ed_kNm=0.0)
        assert r["bending_ok"] is True

    def test_box_zero_demand(self, db):
        r = cc.box_girder(db, M_Ed_kNm=0.0)
        assert r["bending_ok"] is True

    def test_tbeam_zero_demand(self, db):
        r = cc.t_beam(db, M_Ed_kNm=0.0)
        assert r["bending_ok"] is True

    def test_tbeam_out_of_flange_explicit_false(self, db):
        r = cc.t_beam(db, As=60000.0, M_Ed_kNm=100.0)
        assert r["M_Rd_kNm"] == 0.0
        assert r["bending_ok"] is False

    def test_steel_zero_demand(self, db):
        r = cc.steel_member(db, A=7600.0, N_Ed_kN=0.0)
        assert r["tension_ok"] is True
        assert r["buckling_ok"] is True


class TestAutosize:
    def test_beam_zero_demand_passes(self, db):
        r = size(
            db,
            "beam",
            "As",
            1.0,
            20000.0,
            {"b": 300, "d": 500, "M_Ed_kNm": 0.0, "V_Ed_kN": 0.0, "Asw_s": 0.0, "L": 8000},
        )
        assert r["ok"] is True

    def test_beam_absurd_demand_still_unreachable(self, db):
        r = size(
            db,
            "beam",
            "As",
            1.0,
            20000.0,
            {"b": 300, "d": 500, "M_Ed_kNm": 1e9, "V_Ed_kN": 0.0, "Asw_s": 0.0, "L": 8000},
        )
        assert r["ok"] is False
        assert "不可達" in r["reason"]

    def test_steel_supported(self, db):
        assert "steel" in FUNCS and "prestressed" in FUNCS
        r = size(
            db,
            "steel",
            "A",
            1.0,
            20000.0,
            {"Iy": 45.9e6, "L": 5000.0, "N_Ed_kN": 1500.0},
        )
        assert r["ok"] is True
        assert r["check"] is True

    def test_prestressed_supported(self, db):
        r = size(
            db,
            "prestressed",
            "P_kN",
            1.0,
            40000.0,
            {"b": 1000, "h": 1500, "e_mm": 500, "M_kNm": 8000},
        )
        assert r["ok"] is True
        assert r["check"] is True


class TestCivilHandlerMainFlow:
    """Handler 端到端（真腳本）：定尺寸鍵名、柱不誤入梁出圖、非結構守衛。"""

    def _handle(self, text):
        from services.handlers.civil_model_handler import CivilModelHandler

        return asyncio.run(CivilModelHandler().handle(text))

    def test_size_zero_demand_reports_value(self):
        out = self._handle("梁跨度8米配筋多少 b=300 d=500 L=8000")
        assert "As=1.0" in out and "✅" in out

    def test_column_calc_not_dxf(self):
        out = self._handle("柱截面計算 b=400 h=400 N_Ed=1500")
        assert "column" in out and "N_Rd_kN" in out
        assert "DXF" not in out

    def test_beam_dxf_still_works(self):
        out = self._handle("梁截面出圖 b=300 d=500")
        assert "DXF" in out and "✅" in out

    def test_non_structural_refused(self):
        out = self._handle("B550M主板")
        assert "非結構構件" in out

    def test_legit_slab_passes_guard(self):
        out = self._handle("板配筋計算 h=150 As=500")
        assert "非結構構件" not in out
        assert "M_Rd_kNm_per_m" in out
