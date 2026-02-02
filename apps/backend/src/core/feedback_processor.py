"""
Angela AI v6.0 - Feedback Processor
反馈处理器

Processes execution feedback, generates learning signals, updates HSM/CDM,
and adjusts behavior strategies based on action results.

Features:
- Execution result collection and analysis
- Action effectiveness evaluation
- Learning signal generation
- HSM/CDM memory updates
- Behavior strategy adjustment
- Multi-layer feedback processing

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import json
import uuid
from pathlib import Path
from collections import deque

if TYPE_CHECKING:
    from .feedback_loop_engine import FeedbackSignal, FeedbackLayer, FeedbackType


class EvaluationMetric(Enum):
    """评估指标 / Evaluation metrics"""
    SUCCESS_RATE = ("成功率", "Success rate")
    EXECUTION_TIME = ("执行时间", "Execution time")
    USER_SATISFACTION = ("用户满意度", "User satisfaction")
    CONTEXT_ADEQUACY = ("上下文适宜性", "Context adequacy")
    TIMELINESS = ("及时性", "Timeliness")
    RESOURCE_EFFICIENCY = ("资源效率", "Resource efficiency")


class LearningSignalType(Enum):
    """学习信号类型 / Learning signal types"""
    POSITIVE_REINFORCEMENT = ("正向强化", "Positive reinforcement")
    NEGATIVE_CORRECTION = ("负向纠正", "Negative correction")
    PATTERN_DISCOVERY = ("模式发现", "Pattern discovery")
    ERROR_RECOVERY = ("错误恢复", "Error recovery")
    STRATEGY_OPTIMIZATION = ("策略优化", "Strategy optimization")


@dataclass
class ActionEvaluation:
    """行动评估 / Action effectiveness evaluation"""
    action_id: str
    action_type: str
    success: bool
    execution_time_ms: float
    metrics: Dict[EvaluationMetric, float]
    context: Dict[str, Any]
    timestamp: datetime
    overall_score: float = 0.0
    
    def __post_init__(self):
        """Calculate overall score from metrics"""
        if self.metrics:
            self.overall_score = sum(self.metrics.values()) / len(self.metrics)


@dataclass
class LearningSignal:
    """学习信号 / Learning signal for HSM/CDM"""
    signal_id: str
    signal_type: LearningSignalType
    source_action: str
    signal_strength: float  # 0-1
    data: Dict[str, Any]
    hsm_update: Optional[Dict[str, Any]] = None
    cdm_update: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyAdjustment:
    """策略调整 / Behavior strategy adjustment"""
    adjustment_id: str
    trigger_signal: str
    target_behavior: str
    adjustment_type: str  # increase, decrease, modify, replace
    adjustment_value: float
    expected_outcome: str
    confidence: float
    timestamp: datetime


@dataclass
class FeedbackHistory:
    """反馈历史 / Historical feedback data"""
    action_type: str
    feedback_count: int = 0
    success_count: int = 0
    average_score: float = 0.0
    last_feedback_time: Optional[datetime] = None
    recent_scores: deque = field(default_factory=lambda: deque(maxlen=100))


class FeedbackProcessor:
    """
    反馈处理器主类 / Main feedback processor
    
    Processes feedback from action execution and generates learning updates.
    Connects action results to memory systems (HSM) and learning systems (CDM).
    
    Key Responsibilities:
    1. Collect and analyze execution results
    2. Evaluate action effectiveness
    3. Generate learning signals
    4. Update HSM with new experiences
    5. Update CDM with learning data
    6. Adjust behavior strategies
    
    Example:
        >>> processor = FeedbackProcessor(
        ...     hsm=hsm,
        ...     cdm=cdm,
        ...     feedback_loop_engine=engine
        ... )
        >>> await processor.initialize()
        >>> 
        >>> # Process feedback signal
        >>> await processor.process_feedback(feedback_signal)
        >>> 
        >>> # Get learning recommendations
        >>> recommendations = processor.get_learning_recommendations()
    """
    
    def __init__(
        self,
        hsm: Optional[Any] = None,
        cdm: Optional[Any] = None,
        feedback_loop_engine: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # System references
        self.hsm = hsm
        self.cdm = cdm
        self.feedback_loop_engine = feedback_loop_engine
        
        # Feedback tracking
        self.feedback_history: Dict[str, FeedbackHistory] = {}
        self.recent_evaluations: deque = deque(maxlen=1000)
        self.learning_signals: deque = deque(maxlen=500)
        self.strategy_adjustments: List[StrategyAdjustment] = []
        
        # Processing state
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
        self._pending_feedback: asyncio.Queue = asyncio.Queue()
        
        # Thresholds
        self.success_threshold = self.config.get("success_threshold", 0.7)
        self.learning_trigger_threshold = self.config.get("learning_trigger_threshold", 0.5)
        self.strategy_adjustment_threshold = self.config.get("strategy_adjustment_threshold", 0.3)
        
        # Callbacks
        self._learning_callbacks: List[Callable[[LearningSignal], None]] = []
        self._strategy_callbacks: List[Callable[[StrategyAdjustment], None]] = []
        
        # Metrics
        self.processing_metrics = {
            "feedback_processed": 0,
            "learning_signals_generated": 0,
            "strategy_adjustments": 0,
            "hsm_updates": 0,
            "cdm_updates": 0
        }
    
    async def initialize(self):
        """Initialize the feedback processor"""
        print("[FeedbackProcessor] Initializing...")
        
        self._running = True
        
        # Start background processing
        self._processing_task = asyncio.create_task(self._processing_loop())
        
        # Load historical data if available
        await self._load_history()
        
        print("[FeedbackProcessor] Initialization complete")
    
    async def shutdown(self):
        """Shutdown the feedback processor"""
        print("[FeedbackProcessor] Shutting down...")
        
        self._running = False
        
        # Cancel processing task
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Save history
        await self._save_history()
        
        print("[FeedbackProcessor] Shutdown complete")
    
    async def _processing_loop(self):
        """Background processing loop"""
        while self._running:
            try:
                # Get pending feedback (with timeout)
                feedback = await asyncio.wait_for(
                    self._pending_feedback.get(),
                    timeout=1.0
                )
                
                # Process feedback
                await self._process_single_feedback(feedback)
                
            except asyncio.TimeoutError:
                # No feedback to process, continue
                pass
            except Exception as e:
                print(f"[FeedbackProcessor] Processing error: {e}")
    
    async def process_feedback(self, feedback: 'FeedbackSignal'):
        """
        Process a feedback signal
        
        Args:
            feedback: Feedback signal to process
        """
        await self._pending_feedback.put(feedback)
        self.processing_metrics["feedback_processed"] += 1
    
    async def _process_single_feedback(self, feedback: 'FeedbackSignal'):
        """Process a single feedback signal"""
        try:
            # Step 1: Evaluate action effectiveness
            evaluation = await self._evaluate_action(feedback)
            if evaluation:
                self.recent_evaluations.append(evaluation)
            
            # Step 2: Update feedback history
            await self._update_history(feedback, evaluation)
            
            # Step 3: Generate learning signal
            learning_signal = await self._generate_learning_signal(feedback, evaluation)
            if learning_signal:
                self.learning_signals.append(learning_signal)
                self.processing_metrics["learning_signals_generated"] += 1
                
                # Notify learning callbacks
                for callback in self._learning_callbacks:
                    try:
                        callback(learning_signal)
                    except Exception:
                        pass
                
                # Update HSM and CDM
                await self._update_memory_systems(learning_signal)
            
            # Step 4: Check if strategy adjustment needed
            if evaluation and evaluation.overall_score < self.strategy_adjustment_threshold:
                adjustment = await self._generate_strategy_adjustment(feedback, evaluation)
                if adjustment:
                    self.strategy_adjustments.append(adjustment)
                    self.processing_metrics["strategy_adjustments"] += 1
                    
                    # Notify strategy callbacks
                    for callback in self._strategy_callbacks:
                        try:
                            callback(adjustment)
                        except Exception:
                            pass
            
        except Exception as e:
            print(f"[FeedbackProcessor] Error processing feedback: {e}")
    
    async def _evaluate_action(self, feedback: 'FeedbackSignal') -> Optional[ActionEvaluation]:
        """Evaluate action effectiveness from feedback"""
        action_id = feedback.action_id
        
        # Get action details from feedback loop engine if available
        action_type = "unknown"
        execution_time_ms = 0.0
        success = feedback.value > 0.5
        context = feedback.data
        
        # Try to get more details from feedback loop engine
        if self.feedback_loop_engine:
            # Look for completed cycle with this action
            cycles = self.feedback_loop_engine.get_completed_cycles(limit=100)
            for cycle in cycles:
                if cycle.action_id == action_id:
                    if cycle.decision:
                        action_type = cycle.decision.action_type
                    if cycle.execution_result:
                        execution_time_ms = cycle.latency_ms
                        success = cycle.execution_result.get("success", False)
                    break
        
        # Calculate evaluation metrics
        metrics = {}
        
        # Success rate metric
        metrics[EvaluationMetric.SUCCESS_RATE] = 1.0 if success else 0.0
        
        # Execution time metric (faster is better, up to a point)
        if execution_time_ms < 100:  # < 100ms is excellent
            metrics[EvaluationMetric.EXECUTION_TIME] = 1.0
        elif execution_time_ms < 500:  # < 500ms is good
            metrics[EvaluationMetric.EXECUTION_TIME] = 0.8
        elif execution_time_ms < 1000:  # < 1s is acceptable
            metrics[EvaluationMetric.EXECUTION_TIME] = 0.6
        else:
            metrics[EvaluationMetric.EXECUTION_TIME] = 0.4
        
        # User satisfaction (from feedback value)
        metrics[EvaluationMetric.USER_SATISFACTION] = feedback.value
        
        # Context adequacy (simplified)
        metrics[EvaluationMetric.CONTEXT_ADEQUACY] = 0.7
        
        # Timeliness (based on feedback type)
        if feedback.feedback_type.value[0] == "即时反馈":
            metrics[EvaluationMetric.TIMELINESS] = 1.0
        else:
            metrics[EvaluationMetric.TIMELINESS] = 0.7
        
        # Resource efficiency (placeholder)
        metrics[EvaluationMetric.RESOURCE_EFFICIENCY] = 0.8
        
        return ActionEvaluation(
            action_id=action_id,
            action_type=action_type,
            success=success,
            execution_time_ms=execution_time_ms,
            metrics=metrics,
            context=context,
            timestamp=datetime.now()
        )
    
    async def _update_history(self, feedback: 'FeedbackSignal', evaluation: Optional[ActionEvaluation]):
        """Update feedback history"""
        if not evaluation:
            return
        
        action_type = evaluation.action_type
        
        if action_type not in self.feedback_history:
            self.feedback_history[action_type] = FeedbackHistory(action_type=action_type)
        
        history = self.feedback_history[action_type]
        history.feedback_count += 1
        if evaluation.success:
            history.success_count += 1
        history.last_feedback_time = datetime.now()
        history.recent_scores.append(evaluation.overall_score)
        
        # Update average score
        history.average_score = sum(history.recent_scores) / len(history.recent_scores)
    
    async def _generate_learning_signal(
        self, 
        feedback: 'FeedbackSignal', 
        evaluation: Optional[ActionEvaluation]
    ) -> Optional[LearningSignal]:
        """Generate learning signal from feedback"""
        if not evaluation:
            return None
        
        # Determine signal type
        if evaluation.success and evaluation.overall_score > 0.8:
            signal_type = LearningSignalType.POSITIVE_REINFORCEMENT
        elif not evaluation.success:
            signal_type = LearningSignalType.NEGATIVE_CORRECTION
        elif evaluation.overall_score < 0.5:
            signal_type = LearningSignalType.ERROR_RECOVERY
        else:
            signal_type = LearningSignalType.STRATEGY_OPTIMIZATION
        
        # Calculate signal strength
        signal_strength = evaluation.overall_score
        
        # Create HSM update
        hsm_update = {
            "action_type": evaluation.action_type,
            "context": evaluation.context,
            "outcome": "success" if evaluation.success else "failure",
            "score": evaluation.overall_score,
            "timestamp": datetime.now().isoformat()
        }
        
        # Create CDM update
        cdm_update = {
            "type": "execution_feedback",
            "metrics": {k.value[0]: v for k, v in evaluation.metrics.items()},
            "success": evaluation.success,
            "prediction_error": abs(0.5 - evaluation.overall_score),
            "strategy_effectiveness": evaluation.overall_score
        }
        
        return LearningSignal(
            signal_id=str(uuid.uuid4()),
            signal_type=signal_type,
            source_action=feedback.action_id,
            signal_strength=signal_strength,
            data={
                "feedback_layer": feedback.layer.value[0],
                "feedback_type": feedback.feedback_type.value[0],
                "evaluation": evaluation.__dict__ if evaluation else {}
            },
            hsm_update=hsm_update,
            cdm_update=cdm_update,
            timestamp=datetime.now()
        )
    
    async def _update_memory_systems(self, learning_signal: LearningSignal):
        """Update HSM and CDM with learning signal"""
        # Update HSM
        if self.hsm and learning_signal.hsm_update:
            try:
                if hasattr(self.hsm, 'store_experience'):
                    await self.hsm.store_experience(learning_signal.hsm_update)
                elif hasattr(self.hsm, 'update_from_feedback'):
                    await self.hsm.update_from_feedback(learning_signal.hsm_update)
                
                self.processing_metrics["hsm_updates"] += 1
            except Exception as e:
                print(f"[FeedbackProcessor] HSM update error: {e}")
        
        # Update CDM
        if self.cdm and learning_signal.cdm_update:
            try:
                if hasattr(self.cdm, 'integrate_execution_feedback'):
                    await self.cdm.integrate_execution_feedback(learning_signal.cdm_update)
                elif hasattr(self.cdm, 'compute_delta'):
                    delta = self.cdm.compute_delta(learning_signal.cdm_update)
                    if hasattr(self.cdm, 'should_trigger_learning'):
                        if self.cdm.should_trigger_learning(delta):
                            if hasattr(self.cdm, 'integrate_knowledge'):
                                self.cdm.integrate_knowledge(learning_signal.cdm_update, delta)
                
                self.processing_metrics["cdm_updates"] += 1
            except Exception as e:
                print(f"[FeedbackProcessor] CDM update error: {e}")
    
    async def _generate_strategy_adjustment(
        self, 
        feedback: 'FeedbackSignal',
        evaluation: ActionEvaluation
    ) -> Optional[StrategyAdjustment]:
        """Generate behavior strategy adjustment"""
        action_type = evaluation.action_type
        
        # Get history for this action type
        history = self.feedback_history.get(action_type)
        if not history or history.feedback_count < 3:
            return None  # Not enough data
        
        # Determine adjustment type
        if history.average_score < 0.3:
            adjustment_type = "replace"
            adjustment_value = -0.5
        elif history.average_score < 0.5:
            adjustment_type = "modify"
            adjustment_value = -0.3
        elif evaluation.success:
            adjustment_type = "increase"
            adjustment_value = 0.2
        else:
            adjustment_type = "decrease"
            adjustment_value = -0.2
        
        # Generate expected outcome
        if adjustment_type in ["increase", "modify"]:
            expected_outcome = "improved_success_rate"
        else:
            expected_outcome = "avoid_similar_failures"
        
        return StrategyAdjustment(
            adjustment_id=str(uuid.uuid4()),
            trigger_signal=feedback.action_id,
            target_behavior=action_type,
            adjustment_type=adjustment_type,
            adjustment_value=adjustment_value,
            expected_outcome=expected_outcome,
            confidence=abs(adjustment_value),
            timestamp=datetime.now()
        )
    
    async def _save_history(self):
        """Save feedback history to file"""
        try:
            history_path = Path("~/.angela/feedback_history.json").expanduser()
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            history_data = {
                "feedback_history": {
                    k: {
                        "action_type": v.action_type,
                        "feedback_count": v.feedback_count,
                        "success_count": v.success_count,
                        "average_score": v.average_score,
                        "last_feedback_time": v.last_feedback_time.isoformat() if v.last_feedback_time else None
                    }
                    for k, v in self.feedback_history.items()
                },
                "strategy_adjustments": [
                    {
                        "adjustment_id": adj.adjustment_id,
                        "target_behavior": adj.target_behavior,
                        "adjustment_type": adj.adjustment_type,
                        "adjustment_value": adj.adjustment_value,
                        "expected_outcome": adj.expected_outcome,
                        "timestamp": adj.timestamp.isoformat()
                    }
                    for adj in self.strategy_adjustments[-100:]  # Last 100
                ],
                "metrics": self.processing_metrics,
                "saved_at": datetime.now().isoformat()
            }
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[FeedbackProcessor] Save history error: {e}")
    
    async def _load_history(self):
        """Load feedback history from file"""
        try:
            history_path = Path("~/.angela/feedback_history.json").expanduser()
            
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # Load feedback history
                for k, v in history_data.get("feedback_history", {}).items():
                    self.feedback_history[k] = FeedbackHistory(
                        action_type=v["action_type"],
                        feedback_count=v["feedback_count"],
                        success_count=v["success_count"],
                        average_score=v["average_score"],
                        last_feedback_time=datetime.fromisoformat(v["last_feedback_time"]) if v.get("last_feedback_time") else None
                    )
                
                print(f"[FeedbackProcessor] Loaded history for {len(self.feedback_history)} action types")
                
        except Exception as e:
            print(f"[FeedbackProcessor] Load history error: {e}")
    
    # ========== Public API ==========
    
    def register_learning_callback(self, callback: Callable[[LearningSignal], None]):
        """Register callback for learning signals"""
        self._learning_callbacks.append(callback)
    
    def register_strategy_callback(self, callback: Callable[[StrategyAdjustment], None]):
        """Register callback for strategy adjustments"""
        self._strategy_callbacks.append(callback)
    
    def get_learning_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get learning recommendations based on feedback history"""
        recommendations = []
        
        # Find action types with low performance
        for action_type, history in self.feedback_history.items():
            if history.feedback_count >= 5 and history.average_score < self.success_threshold:
                recommendations.append({
                    "action_type": action_type,
                    "issue": "low_success_rate",
                    "current_score": history.average_score,
                    "success_rate": history.success_count / history.feedback_count,
                    "recommendation": "review_and_improve",
                    "priority": "high" if history.average_score < 0.3 else "medium"
                })
        
        # Sort by priority and score
        recommendations.sort(key=lambda x: (x["priority"] != "high", x["current_score"]))
        
        return recommendations[:limit]
    
    def get_performance_report(self, action_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance report for action type(s)"""
        if action_type:
            history = self.feedback_history.get(action_type)
            if history:
                return {
                    "action_type": action_type,
                    "feedback_count": history.feedback_count,
                    "success_rate": history.success_count / history.feedback_count if history.feedback_count > 0 else 0,
                    "average_score": history.average_score,
                    "recent_trend": self._calculate_trend(list(history.recent_scores))
                }
            return {}
        
        # Overall report
        all_scores = []
        total_feedback = 0
        total_success = 0
        
        for history in self.feedback_history.values():
            all_scores.extend(history.recent_scores)
            total_feedback += history.feedback_count
            total_success += history.success_count
        
        return {
            "overall_average_score": sum(all_scores) / len(all_scores) if all_scores else 0,
            "overall_success_rate": total_success / total_feedback if total_feedback > 0 else 0,
            "total_feedback_processed": total_feedback,
            "action_types_tracked": len(self.feedback_history),
            "processing_metrics": self.processing_metrics
        }
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend from score history"""
        if len(scores) < 10:
            return "insufficient_data"
        
        # Compare first half to second half
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        
        diff = second_half - first_half
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    def get_recent_learning_signals(self, limit: int = 50) -> List[LearningSignal]:
        """Get recent learning signals"""
        return list(self.learning_signals)[-limit:]
    
    def get_strategy_adjustments(self, limit: int = 100) -> List[StrategyAdjustment]:
        """Get recent strategy adjustments"""
        return self.strategy_adjustments[-limit:]
    
    async def clear_history(self):
        """Clear all feedback history"""
        self.feedback_history.clear()
        self.recent_evaluations.clear()
        self.learning_signals.clear()
        self.strategy_adjustments.clear()
        self.processing_metrics = {
            "feedback_processed": 0,
            "learning_signals_generated": 0,
            "strategy_adjustments": 0,
            "hsm_updates": 0,
            "cdm_updates": 0
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 70)
        print("Angela AI v6.0 - Feedback Processor Demo")
        print("反馈处理器演示")
        print("=" * 70)
        
        processor = FeedbackProcessor()
        await processor.initialize()
        
        # Create mock feedback signals
        from feedback_loop_engine import FeedbackSignal, FeedbackLayer, FeedbackType
        
        print("\n1. Processing sample feedback signals:")
        
        # Success feedback
        success_signal = FeedbackSignal(
            signal_id="test_1",
            action_id="action_1",
            layer=FeedbackLayer.COGNITIVE,
            feedback_type=FeedbackType.IMMEDIATE,
            value=0.9,
            data={"user_response": "positive"},
            timestamp=datetime.now()
        )
        await processor.process_feedback(success_signal)
        print("   Processed success feedback")
        
        # Failure feedback
        failure_signal = FeedbackSignal(
            signal_id="test_2",
            action_id="action_2",
            layer=FeedbackLayer.PHYSIOLOGICAL,
            feedback_type=FeedbackType.DELAYED,
            value=0.2,
            data={"error": "timeout"},
            timestamp=datetime.now()
        )
        await processor.process_feedback(failure_signal)
        print("   Processed failure feedback")
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Show metrics
        print("\n2. Processing metrics:")
        for key, value in processor.processing_metrics.items():
            print(f"   {key}: {value}")
        
        # Show recommendations
        print("\n3. Learning recommendations:")
        recommendations = processor.get_learning_recommendations()
        if recommendations:
            for rec in recommendations:
                print(f"   - {rec['action_type']}: {rec['recommendation']} (priority: {rec['priority']})")
        else:
            print("   No recommendations yet (need more data)")
        
        # Show performance report
        print("\n4. Performance report:")
        report = processor.get_performance_report()
        for key, value in report.items():
            print(f"   {key}: {value}")
        
        await processor.shutdown()
        
        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
    
    asyncio.run(demo())
