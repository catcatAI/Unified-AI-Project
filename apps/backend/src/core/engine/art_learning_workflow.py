# =============================================================================
# ANGELA-MATRIX: L4[創造層] βδ [A] L4+
# =============================================================================
# 職責: 藝術學習工作流 (Art Learning Workflow).
# 維度: 認知學習 (β) 與視覺呈現 (γ) 的自動化接軌。
# =============================================================================

import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import math
from core.bio.biological_integrator import BiologicalIntegrator

from core.interfaces.service_registry import get_registry

logger = logging.getLogger(__name__)

class WorkflowStage(Enum):
    """工作流阶段 / Workflow stages"""
    RESEARCH = ("研究", "Search for tutorials and references")
    ANALYSIS = ("分析", "Analyze images and techniques")
    PRACTICE = ("练习", "Practice and skill acquisition")
    EVOLUTION = ("演化", "Evolve aesthetics based on feedback")
    COMPLETE = ("完成", "Workflow complete")

class LearningObjective:
    """代表 Angela 當前的藝術或美學學習目標"""
    def __init__(self, name: str, priority: float = 0.5):
        self.name = name
        self.priority = priority
        self.progress = 0.0
        self.milestones = []

    def update_progress(self, increment: float) -> None:
        """Update progress by a given increment, capped at 1.0."""
        self.progress = min(1.0, self.progress + increment)

# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [A] [L5+]
# [Task N.22.1] 工作流資料類補完 / Workflow Data Class Completion
# =============================================================================

@dataclass
class WorkflowProgress:
    """工作流進度追蹤器 / Workflow progress tracker"""
    stage: WorkflowStage = WorkflowStage.RESEARCH
    stage_completion: dict = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    quality_scores: List[float] = field(default_factory=list)

    def get_bottleneck_stage(self) -> Optional[str]:
        """識別完成度最低的瓶頸階段 / Find lowest-completion stage"""
        if not self.stage_completion:
            return None
        return min(self.stage_completion, key=self.stage_completion.get)

    def overall_progress(self) -> float:
        """整體進度 0-1 / Overall progress 0-1"""
        if not self.stage_completion:
            return 0.0
        total_stages = len(WorkflowStage) - 1  # exclude COMPLETE
        return min(1.0, sum(self.stage_completion.values()) / max(1, total_stages))

    def record_quality(self, score: float) -> None:
        """Record a quality score, clamped to [0, 1]."""
        self.quality_scores.append(max(0.0, min(1.0, score)))

    def average_quality(self) -> float:
        """Calculate the average quality score."""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores) / len(self.quality_scores)


@dataclass
class SkillAssessment:
    """
    [Native AL] 技能評估 — Power Law 習得曲線
    mastery = 1 - exp(-k * practice_count)
    k 由用戶反饋自適應調整。
    """
    skill_name: str
    practice_count: int = 0
    decay_constant: float = 0.1   # AL-adjustable learning rate k
    user_feedback_scores: List[float] = field(default_factory=list)

    def mastery_level(self) -> float:
        """Power Law 成熟度 / Power Law mastery score 0-1"""
        return 1.0 - math.exp(-self.decay_constant * self.practice_count)

    def update_from_feedback(self, score: float) -> None:
        """
        [AL] 根據用戶反饋調整衰減常數 k。
        正反饋 → 加速學習曲線；負反饋 → 放緩。
        """
        self.user_feedback_scores.append(max(0.0, min(1.0, score)))
        self.practice_count += 1
        if score > 0.7:
            self.decay_constant = min(0.5, self.decay_constant * 1.05)
        elif score < 0.3:
            self.decay_constant = max(0.01, self.decay_constant * 0.95)

    def sessions_to_target(self, target: float = 0.8) -> int:
        """估計達到目標成熟度所需的練習次數"""
        if target >= 1.0 or self.decay_constant <= 0:
            return 9999
        needed = -math.log(1.0 - target) / self.decay_constant
        return max(0, int(needed) - self.practice_count)


@dataclass
class GenerationResult:
    """
    生成結果記錄 — 構成 (state, output, feedback) 訓練三元組
    供後續 AL 更新使用。
    """
    input_emotion_state: dict            # γ 維度快照
    generated_params: dict               # 輸出的色彩/Live2D 參數
    user_feedback: Optional[float] = None   # -1.0 壞 ~ +1.0 好
    timestamp: datetime = field(default_factory=datetime.now)

    def is_positive(self) -> bool:
        """Check if user feedback is positive."""
        return self.user_feedback is not None and self.user_feedback > 0.1

    def is_negative(self) -> bool:
        """Check if user feedback is negative."""
        return self.user_feedback is not None and self.user_feedback < -0.1


@dataclass
class WorkflowConfig:
    """工作流配置 / Workflow configuration"""
    max_research_tutorials: int = 5
    analysis_timeout_s: float = 30.0
    practice_target_mastery: float = 0.8
    auto_evolve_on_feedback: bool = True
    al_learning_rate: float = 0.05      # AL 全域學習率


class ArtLearningWorkflow:
    """
    Angela 的外觀演化協調器 (2030 Standard).
    負責將 L1 的生物脈動 轉化為 L4 的美學演化，最終在 L6 渲染層實體化。
    """
    def __init__(self, bio_integrator=None, art_learning_system=None, avatar_generator=None,
                 live2d_integration=None, physiological_tactile=None, cyber_identity=None):
        self.bio = bio_integrator
        self.art_system = art_learning_system
        self.avatar_generator = avatar_generator
        self.live2d_integration = live2d_integration
        self.physiological_tactile = physiological_tactile
        self.cyber_identity = cyber_identity
        self.current_overrides = {}
        self.last_logged_emotion = None

    async def update_visual_state(self) -> Dict[str, Any]:
        """[L1 -> L4 Sync] 根據當前生物指標，計算最新的色彩覆蓋。"""
        if self.bio is None:
            return {}
        bio_state = self.bio.get_biological_state()
        if self.art_system is not None:
            self.current_overrides = self.art_system.get_color_overrides(bio_state)
        else:
            self.current_overrides = self._default_color_overrides(bio_state)

        emotion = bio_state.get("dominant_emotion", "neutral")
        if emotion != self.last_logged_emotion:
            logger.info(f"🎨 [L4-Workflow] Aesthetic shift based on '{emotion}'.")
            self.last_logged_emotion = emotion

        return self.current_overrides

    def process_user_aesthetic_feedback(self, feedback_text: str) -> None:
        """[L4-Evolution] 根據用戶在對話中對外觀的評價進行學習。"""
        if self.art_system is not None:
            self.art_system.learn_from_feedback(feedback_text, str(self.current_overrides))

    @staticmethod
    def _default_color_overrides(bio_state: Dict[str, Any]) -> Dict[str, Any]:
        emotion = bio_state.get("dominant_emotion", "neutral")
        energy = bio_state.get("energy_level", 0.5)
        color_map = {
            "happy": {"warmth": 0.8, "saturation": 0.7 + energy * 0.3},
            "sad": {"warmth": 0.3, "saturation": 0.4},
            "angry": {"warmth": 0.9, "saturation": 0.9, "hue_shift": 0.1},
            "calm": {"warmth": 0.5, "saturation": 0.5, "brightness": 0.6 + energy * 0.4},
            "neutral": {"warmth": 0.5, "saturation": 0.5},
        }
        return color_map.get(emotion, color_map["neutral"])

# 單例模式初始化 (由 BiologicalIntegrator 驅動)
_instance = None
def get_art_workflow(bio=None) -> None:
    """Get the art workflow by bio."""
    global _instance
    if _instance is None and bio is not None:
        _instance = ArtLearningWorkflow(bio)
        get_registry().register("art_learning_workflow", _instance)
    return _instance
