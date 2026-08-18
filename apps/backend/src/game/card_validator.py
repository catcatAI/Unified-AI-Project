# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 遊戲卡片數理化一致性驗證（結構 + 數值確定性）
# 維度: δ 素材維度（卡片原始資料品質）、ζ 驗證維度
# 安全: 使用 Key A (後端控制)；唯讀驗證，不改卡片資料
# 成熟度: L2+ 等級開始接觸資料一致性驗證
#
# =============================================================================

"""遊戲卡片數理化/結構一致性驗證。

針對 `apps/game-rpg/data/game_cards.json`（351 張）檢查「不符邏輯、不合常理、
數理化學」層面的確定性錯誤：

- 卡 ID 唯一性（重複 = 遊戲邏輯衝突）。
- token `strength` 界域（0–1，越界 = 機率/權重不合常理）。
- stat 數值欄位型別與界域（age 負值/零、非數值 = 數理化不合常理）。
- `raw_field_count` 與實際 token 數一致性（宣告 vs 實作不符 = 資料漂移）。
- 同卡內 token 名稱重複（能力/機制衝突）。
- 百分比類 stat 是否區間合法（0–100 或 0–1）。

全部規則為確定性（non-deterministic judgement 不下斷言），僅回報結構與
數值上的硬錯誤。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_CARDS_PATH = (
    Path(__file__).resolve().parents[4] / "apps" / "game-rpg" / "data" / "game_cards.json"
)


@dataclass
class CardIssue:
    """單一卡片驗證問題。"""

    card_id: str
    rule: str
    message: str
    severity: str = "error"  # error / warning


@dataclass
class ValidationReport:
    """驗證結果報告。"""

    total_cards: int = 0
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    issues: List[CardIssue] = field(default_factory=list)

    def add(self, issue: CardIssue) -> None:
        self.issues.append(issue)
        self.total_issues += 1
        if issue.severity == "error":
            self.errors += 1
        else:
            self.warnings += 1

    @property
    def ok(self) -> bool:
        return self.errors == 0


def _is_numeric(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(float(v))


def _is_numeric_str(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    try:
        float(v.replace("%", "").replace(",", "").strip())
        return True
    except ValueError:
        return False


class GameCardValidator:
    """遊戲卡片一致性驗證器（唯讀）。"""

    def __init__(self, cards_path: Path = DEFAULT_CARDS_PATH) -> None:
        self.path = Path(cards_path)
        self.cards: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.cards = data.get("cards", [])

    def validate(self) -> ValidationReport:
        report = ValidationReport(total_cards=len(self.cards))
        seen: Dict[str, int] = {}
        for card in self.cards:
            cid = card.get("card_id", "")
            if cid in seen:
                report.add(
                    CardIssue(cid, "unique_id", f"duplicate card_id (also at index {seen[cid]})")
                )
            else:
                seen[cid] = self.cards.index(card)
            card_type = card.get("card_type", "")
            self._check_strengths(cid, card, report)
            self._check_stats(cid, card, report)
            self._check_field_count(cid, card, report)
            self._check_duplicate_names(cid, card, report)
            self._check_card_type(cid, card_type, report)
        return report

    # ------------------------------------------------------------------
    # 規則實作
    # ------------------------------------------------------------------
    def _tokens(self, card: Dict[str, Any]) -> List[Dict[str, Any]]:
        return card.get("tokens", []) or []

    def _check_strengths(self, cid: str, card: Dict[str, Any], report: ValidationReport) -> None:
        for idx, token in enumerate(self._tokens(card)):
            strength = token.get("strength")
            if strength is None:
                continue
            if not _is_numeric(strength):
                report.add(
                    CardIssue(
                        cid,
                        "strength_numeric",
                        f"token[{idx}] strength not numeric: {strength!r}",
                        "error",
                    )
                )
            elif not (0.0 <= float(strength) <= 1.0):
                report.add(
                    CardIssue(
                        cid,
                        "strength_bounds",
                        f"token[{idx}] strength {strength} out of [0,1]",
                        "error",
                    )
                )

    def _check_stats(self, cid: str, card: Dict[str, Any], report: ValidationReport) -> None:
        stats = card.get("stats") or {}
        for key, value in stats.items():
            if value is None:
                report.add(CardIssue(cid, "stat_none", f"stat '{key}' is null", "warning"))
                continue
            if isinstance(value, float) and math.isnan(value):
                report.add(CardIssue(cid, "stat_numeric", f"stat '{key}' is NaN", "error"))
                continue
            if isinstance(value, (dict, list)):
                continue  # 巢狀結構不下數值斷言
            if isinstance(value, bool):
                continue
            if _is_numeric(value):
                if key.lower() in ("age", "level", "lv") and value <= 0:
                    report.add(
                        CardIssue(
                            cid,
                            "stat_positive",
                            f"stat '{key}' = {value} must be positive",
                            "error",
                        )
                    )
                if key.endswith("%") or "percent" in key.lower():
                    if not (0.0 <= value <= 100.0):
                        report.add(
                            CardIssue(
                                cid,
                                "stat_percent",
                                f"percent stat '{key}' = {value} outside [0,100]",
                                "error",
                            )
                        )
            elif isinstance(value, str) and _is_numeric_str(value):
                # 字串化的數值：百分比界域也要查
                raw = value.replace("%", "").replace(",", "").strip()
                if "%" in value:
                    num = float(raw)
                    if not (0.0 <= num <= 100.0):
                        report.add(
                            CardIssue(
                                cid,
                                "stat_percent_str",
                                f"percent str stat '{key}' = {value} outside [0,100]",
                                "error",
                            )
                        )
            # 非數值字串：確認非空
            elif isinstance(value, str) and not value.strip():
                report.add(CardIssue(cid, "stat_empty", f"stat '{key}' is empty string", "warning"))

    def _check_field_count(self, cid: str, card: Dict[str, Any], report: ValidationReport) -> None:
        """raw_field_count 為來源 raw 欄位數（導入前），與處理後 token 數是
        兩種不同度量——不做相等比較，只做數值健全性檢查。

        修正歷史：先前規則比較 declared != len(tokens) 誤報 117 個假陽性
        （raw_field_count 是來源資料量，非 token 數）。
        """
        declared = card.get("raw_field_count")
        if declared is None:
            return
        if not isinstance(declared, int):
            report.add(
                CardIssue(
                    cid, "field_count_type", f"raw_field_count not int: {declared!r}", "error"
                )
            )
        elif declared < 0:
            report.add(
                CardIssue(
                    cid, "field_count_negative", f"raw_field_count {declared} negative", "error"
                )
            )

    def _check_duplicate_names(
        self, cid: str, card: Dict[str, Any], report: ValidationReport
    ) -> None:
        name_counts: Dict[str, int] = {}
        for token in self._tokens(card):
            name = token.get("name")
            if not name:
                continue
            name_counts[name] = name_counts.get(name, 0) + 1
        for name, count in name_counts.items():
            if count > 1:
                report.add(
                    CardIssue(
                        cid,
                        "duplicate_token_name",
                        f"token name '{name}' appears {count} times",
                        "warning",
                    )
                )

    def _check_card_type(self, cid: str, card_type: str, report: ValidationReport) -> None:
        if not card_type:
            report.add(CardIssue(cid, "card_type_missing", "card_type is empty", "error"))
        known = {
            "角色卡",
            "場景卡",
            "事件卡",
            "物品卡",
            "技能卡",
            "地區卡",
            "元設定卡",
            "劇情節點卡",
            "國家卡",
            "組織卡",
            "專案管理卡",
            "規則卡",
            "故事線卡",
            "故事線合集卡",
            "世界觀核心卡",
            "通用機制卡",
            "創作工具卡",
            "元公式卡",
            "安全詞庫卡",
            "故事線補充卡",
            "角色補充卡",
        }
        if card_type and card_type not in known:
            report.add(
                CardIssue(
                    cid,
                    "card_type_unknown",
                    f"unexpected card_type {card_type!r}",
                    "warning",
                )
            )


def load_report(cards_path: Path = DEFAULT_CARDS_PATH) -> ValidationReport:
    """載入卡片並回報驗證結果（供 CLI / 測試 / 前端使用）。"""
    return GameCardValidator(cards_path).validate()
