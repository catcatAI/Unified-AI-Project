"""
Code Inspector Integration — 新架構整合橋接
==========================================

將 CodeInspector 的檢查結果與 StateMatrixAdapter 的新架構整合：
- 檢查結果 → TemporalState（代碼質量時間序列）
- 檢查指標 → InfluenceSpace（軸間影響）
- 新模式發現 → AllocationPolicy（分配決策）
- 圖譜演化 → TemporalState（依賴追蹤）
- 自動修復 → RippleNode（漣漪效應）
- 學習反饋 → NegativityDetector（θ 自糾）

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
