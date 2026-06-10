# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    timestamp: datetime
    cpu_cores: float = 0.0
    memory_gb: float = 0.0
    disk_gb: float = 0.0
    network_mbps: float = 0.0
    gpu_count: int = 0


@dataclass
class CapacityPrediction:
    resource_type: str
    predicted_value: float
    confidence: float
    urgency: str
    recommendation: str
    timestamp: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class ScalingPlan:
    plan_id: str
    resource_type: str
    scaling_action: str
    auto_approve: bool = False
    status: str = "pending"


class CapacityPlanner:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.prediction_window = self.config.get("prediction_window", 24)
        self.prediction_window_hours = self.prediction_window
        self.scaling_threshold = self.config.get("scaling_threshold", 0.8)
        self.min_data_points = self.config.get("min_data_points", 168)
        self.cost_per_cpu = self.config.get("cost_per_cpu", 0.05)
        self.cost_per_gb = self.config.get("cost_per_gb", 0.01)
        self.usage_history: list[dict] = []
        self.capacity_plans: dict[str, ScalingPlan] = {}

    async def initialize(self) -> None:
        logger.info("CapacityPlanner initialized")

    async def collect_resource_usage(self, metrics: dict[str, float]) -> None:
        usage = ResourceUsage(
            timestamp=datetime.now(),
            cpu_cores=metrics.get("cpu_usage", 0) / 100 * 4,
            memory_gb=metrics.get("memory_usage", 0) / 100 * 8,
            disk_gb=metrics.get("disk_usage", 100),
            network_mbps=metrics.get("network_mbps", 100),
        )
        self.usage_history.append({"timestamp": usage.timestamp.isoformat(), "usage": usage})

    async def _predict_cpu_needs(self, usage: ResourceUsage) -> Optional[dict]:
        if len(self.usage_history) < 10:
            return None
        total_cpu = sum(h["usage"].cpu_cores for h in self.usage_history)
        avg_cpu = total_cpu / len(self.usage_history)
        predicted_cpu = avg_cpu * 1.2
        return {
            "predicted_cpu": round(predicted_cpu, 2),
            "recommendation": f"Scale from {usage.cpu_cores:.1f} to {predicted_cpu:.1f} cores",
            "urgency": "high" if predicted_cpu > usage.cpu_cores * 1.5 else "medium",
        }

    def _analyze_capacity_trends(self, history: list) -> dict:
        if len(history) < 2:
            return {"cpu_trend": "stable", "memory_trend": "stable", "disk_trend": "stable"}
        first_cpu = history[0]["usage"].cpu_cores
        last_cpu = history[-1]["usage"].cpu_cores
        cpu_trend = "increasing" if last_cpu > first_cpu * 1.05 else "decreasing" if last_cpu < first_cpu * 0.95 else "stable"

        first_mem = history[0]["usage"].memory_gb
        last_mem = history[-1]["usage"].memory_gb
        mem_trend = "increasing" if last_mem > first_mem * 1.05 else "decreasing" if last_mem < first_mem * 0.95 else "stable"

        first_disk = history[0]["usage"].disk_gb
        last_disk = history[-1]["usage"].disk_gb
        disk_trend = "increasing" if last_disk > first_disk * 1.05 else "decreasing" if last_disk < first_disk * 0.95 else "stable"

        return {"cpu_trend": cpu_trend, "memory_trend": mem_trend, "disk_trend": disk_trend}

    async def get_capacity_predictions(self, resource_type: str) -> list[CapacityPrediction]:
        return []

    async def get_scaling_plans(self, resource_type: Optional[str] = None) -> list[ScalingPlan]:
        return list(self.capacity_plans.values())

    async def get_capacity_report(self) -> dict:
        return {"utilization_trends": {}}

    async def approve_scaling_plan(self, plan_id: str, approver: str) -> dict:
        if plan_id in self.capacity_plans:
            self.capacity_plans[plan_id].status = "approved"
        return {"success": True, "plan_id": plan_id}
