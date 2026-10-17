# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M2 測試：step 量化吸附 + 定點模式（計畫 §6.3 M2 驗收）。

驗收：0.01 step 往返無漂移；step=0 連續不量化。附：半遠離零、軸級覆寫、
定點格索引往返、非 fsm 數值/fsm 字串分流。
"""

from __future__ import annotations

import pytest
from engine import AxisSpec
from engine.quantize import (
    from_fixed,
    quantize,
    quantize_auto,
    quantize_axis,
    quantize_fixed,
)


class TestQuantizeDriftFree:
    @pytest.mark.parametrize(
        "value",
        [0.0, 1.0, 1.01, 1.014, 1.015, 1.016, -2.675, -0.005, 99.999, 12345.678],
    )
    def test_hundredth_step_roundtrip_no_drift(self, value):
        # M2 驗收：0.01 step 往返無漂移（落格 + 再量化不變）
        q = quantize(value, 0.01)
        assert quantize(q, 0.01) == q
        cents = q * 100
        assert abs(cents - round(cents)) < 1e-6  # 在 0.01 格點上

    @pytest.mark.parametrize("step", [0.01, 0.1, 0.25, 1.0, 0.5])
    def test_idempotent_across_steps(self, step):
        for v in (0.0, 3.3, -7.77, 12.5):
            q = quantize(v, step)
            assert quantize(q, step) == q

    def test_step_zero_is_continuous_no_quantize(self):
        # M2 驗收：0=連續不量化
        v = 3.141592653589793
        assert quantize(v, 0) == v

    def test_negative_step_raises(self):
        with pytest.raises(ValueError):
            quantize(1.0, -0.01)

    def test_half_away_from_zero(self):
        # 2.5 @ step1 → 3（half-away；banker's 會給 2）
        assert quantize(2.5, 1.0) == 3.0
        assert quantize(-2.5, 1.0) == -3.0

    def test_snaps_to_nearest_grid(self):
        assert quantize(1.014, 0.01) == 1.01
        assert quantize(1.016, 0.01) == 1.02
        assert quantize(-1.016, 0.01) == -1.02


class TestFixedPointMode:
    def test_quantize_fixed_returns_grid_index(self):
        assert quantize_fixed(1.237, 0.01) == 124
        assert quantize_fixed(-1.237, 0.01) == -124
        assert quantize_fixed(5.0, 0.5) == 10

    def test_fixed_roundtrip_matches_quantize(self):
        for v in (0.0, 2.675, -0.005, 100.001):
            idx = quantize_fixed(v, 0.01)
            assert isinstance(idx, int)
            assert from_fixed(idx, 0.01) == quantize(v, 0.01)

    def test_fixed_requires_positive_step(self):
        with pytest.raises(ValueError):
            quantize_fixed(1.0, 0)
        with pytest.raises(ValueError):
            from_fixed(3, 0)

    def test_auto_mode_switch(self):
        assert quantize_auto(1.237, 0.01, fixed=False) == 1.24
        assert quantize_auto(1.237, 0.01, fixed=True) == 124
        assert isinstance(quantize_auto(1.237, 0.01, fixed=True), int)


class TestAxisOverride:
    def make_spec(self, kind="discrete", step=1.0):
        if kind == "fsm":
            return AxisSpec("phase", "fsm", states=("a", "b"))
        if kind == "continuous":
            return AxisSpec("x", "continuous", step=step)
        return AxisSpec("n", "discrete", step=step)

    def test_spec_step_used_without_override(self):
        spec = self.make_spec("continuous", step=0.1)
        assert quantize_axis(1.24, spec) == 1.2

    def test_override_beats_spec_step(self):
        # 軸級覆寫：spec step 1.0，覆寫 0.01 → 貼 0.01 格
        spec = self.make_spec("discrete", step=1.0)
        assert quantize_axis(1.237, spec, override_step=0.01) == 1.24

    def test_override_zero_disables_quantize(self):
        spec = self.make_spec("discrete", step=1.0)
        v = 1.237
        assert quantize_axis(v, spec, override_step=0) == v

    def test_fsm_passes_through(self):
        spec = self.make_spec("fsm")
        assert quantize_axis("a", spec, override_step=0.01) == "a"

    def test_non_numeric_passes_through(self):
        spec = self.make_spec("continuous", step=0.1)
        assert quantize_axis(True, spec) is True
        assert quantize_axis("s", spec) == "s"

    def test_negative_override_raises(self):
        spec = self.make_spec("continuous", step=0.1)
        with pytest.raises(ValueError):
            quantize_axis(1.0, spec, override_step=-0.5)
