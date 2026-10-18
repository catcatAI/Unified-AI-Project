# =============================================================================
# ANGELA-MATRIX: [L4] [α] [A] [L7]
# =============================================================================
"""自主研究模組 — 專案AI自產《後續研究與升級路徑完整報告》。

- `upgrade_research.run_upgrade_research()`：自己查（可重現量測+外部查證）
  → 自己想（自有模型體檢+規則推導候選+透明公式擇優）→ 自己寫（資料填充模板
  +LLM 僅逐段潤色/數字指紋守護）→ validate_report 零容忍驗證。
"""

from __future__ import annotations

from .upgrade_research import derive_candidates, gather_facts, run_upgrade_research, validate_report

__all__ = ["run_upgrade_research", "gather_facts", "derive_candidates", "validate_report"]
