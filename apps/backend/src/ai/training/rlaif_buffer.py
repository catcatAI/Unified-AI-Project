# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""
RLAIF 緩衝 (梯度解耦的 LLM 質檢，vvv 坑2)

設計: 90% Step 用基礎像素/結構 Loss (主訓練循環, 不阻塞), 10% Step 抽樣
送異步隊列 -> MLLM/本地 CLIP 打偏好分 (win/lose) -> DPO loss 僅更新
SharedLatentSpace 與 PrimitiveDiffusion 的輕量參數 (<5% 參數), 主循環不等待.

默認禁用 (compute.multimodal_train.rlaif_enabled=false)，需顯式開啟才生效，
因此不增加默認算力/烤機風險。
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PreferencePair:
    """DPO 偏好對: win 比 lose 更符合結構/語義."""

    prompt: str
    win_vec: np.ndarray   # [263] winning primitive vector
    lose_vec: np.ndarray  # [263]
    score_win: float
    score_lose: float


class RLAIFBuffer:
    """異步 RLAIF 緩衝，梯度與主訓練解耦.

    - 主循環每 10 步抽 1 batch 入隊 (不阻塞)
    - 後台任務用 CLIP/LLM 打分產生 PreferencePair
    - DPO 更新僅觸及 SharedLatentSpace W/b 與 PrimitiveDiffusion 最後層
    """

    def __init__(self, max_size: int = 256, sample_rate: float = 0.1) -> None:
        self._queue: deque[Tuple[str, np.ndarray]] = deque(maxlen=max_size)
        self._pairs: deque[PreferencePair] = deque(maxlen=max_size)
        self.sample_rate = sample_rate
        self._step = 0
        self.enabled = False
        try:
            from core.system.config.magic_numbers import _get

            self.enabled = bool(_get("multimodal_train.rlaif_enabled", False))
        except Exception as e:
            logger.debug(f"RLAIF config load failed: {e}", exc_info=True)

    def maybe_enqueue(self, prompt: str, vec: np.ndarray) -> bool:
        """主訓練循環調用: 10% 抽樣入隊，返回是否入隊."""
        if not self.enabled:
            return False
        self._step += 1
        if self._step % max(1, int(1 / self.sample_rate)) != 0:
            return False
        self._queue.append((prompt, vec.copy()))
        return True

    async def score_pending(self, scorer=None) -> int:
        """後台異步打分: scorer(prompt, vec)->score, 無 scorer 用啟發式."""
        if not self._queue:
            return 0
        scored: List[Tuple[str, np.ndarray, float]] = []
        while self._queue:
            prompt, vec = self._queue.popleft()
            try:
                if scorer is not None:
                    score = float(await scorer(prompt, vec) if asyncio.iscoroutinefunction(scorer) else scorer(prompt, vec))
                else:
                    # Heuristic: vector 的非零密度與範圍作為結構分
                    nz = float(np.count_nonzero(vec)) / max(len(vec), 1)
                    spread = float(np.std(vec))
                    score = 0.5 * nz + 0.5 * min(spread * 2, 1.0)
            except Exception as e:
                logger.debug("RLAIF score failed: %s", e)
                score = 0.5
            scored.append((prompt, vec, score))
        # Pair adjacent as win/lose
        for i in range(0, len(scored) - 1, 2):
            p1, v1, s1 = scored[i]
            p2, v2, s2 = scored[i + 1]
            if abs(s1 - s2) < 1e-6:
                continue
            win, lose = (p1, v1, s1, p2, v2, s2) if s1 > s2 else (p2, v2, s2, p1, v1, s1)
            # win prompt is arbitrary; use winning prompt
            self._pairs.append(PreferencePair(prompt=win[0], win_vec=win[1], lose_vec=lose[1], score_win=win[2], score_lose=lose[2]))
        return len(scored)

    def dpo_loss(self, beta: float = 0.1) -> Optional[Dict[str, float]]:
        """計算 DPO loss (僅統計，不更新權重). Call site 決定是否反向.

        L = -log σ(β * (r_win - r_lose)), r = dot(win_vec, lose_vec) proxy.
        Returns None if no pairs.
        """
        if not self._pairs:
            return None
        losses: List[float] = []
        for p in list(self._pairs)[-32:]:
            # Proxy reward: cosine-like dot (vectors already ~[0,1])
            r_win = float(np.dot(p.win_vec, p.win_vec) / max(np.linalg.norm(p.win_vec), 1e-8))
            r_lose = float(np.dot(p.lose_vec, p.lose_vec) / max(np.linalg.norm(p.lose_vec), 1e-8))
            # Use score gap as reward proxy (heuristic scorer)
            gap = (p.score_win - p.score_lose) * beta
            loss = -np.log(1 / (1 + np.exp(-gap)) + 1e-8)
            losses.append(float(loss))
        return {"loss": float(np.mean(losses)), "pairs": len(losses)}

    def clear(self) -> None:
        self._queue.clear()
        self._pairs.clear()

    def stats(self) -> Dict[str, Any]:
        return {"queued": len(self._queue), "pairs": len(self._pairs), "enabled": self.enabled, "step": self._step}
