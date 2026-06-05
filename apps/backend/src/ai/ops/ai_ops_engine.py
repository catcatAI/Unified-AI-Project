import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyResult:
    anomaly_type: str
    severity: Severity
    confidence: float
    description: str
    recommended_actions: list


class AIOpsEngine:
    """
    AI Ops Engine for managing and optimizing AI operations.
    This includes monitoring, anomaly detection, and automated responses.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else {}
        self.monitoring_active = False
        self.anomaly_history: List[Dict[str, Any]] = []
        self.anomaly_type_counts: Dict[str, int] = {}
        self.anomaly_threshold = self.config.get("anomaly_threshold", 0.1)
        self.prediction_window = self.config.get("prediction_window", 24)
        self.min_data_points = self.config.get("min_data_points", 100)
        self.system_states: List[Dict[str, Any]] = []
        logger.info("AIOpsEngine initialized.")

    def start_monitoring(self) -> bool:
        """Starts the AI Ops monitoring process."""
        if self.monitoring_active:
            logger.warning("Monitoring is already active.", exc_info=True)
            return False
        self.monitoring_active = True
        logger.info("AI Ops monitoring started.")
        return True

    def stop_monitoring(self) -> bool:
        """Stops the AI Ops monitoring process."""
        if not self.monitoring_active:
            logger.warning("Monitoring is not active.", exc_info=True)
            return False
        self.monitoring_active = False
        logger.info("AI Ops monitoring stopped.")
        return True

    def detect_anomaly(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detects anomalies in the provided data and returns a structured report.

        Args:
            data: Data dict with at minimum 'value' and optionally 'metric', 'type'.

        Returns:
            Anomaly report dict if detected, None otherwise.
        """
        logger.debug(f"Detecting anomaly in data: {data}")
        value = data.get("value")
        threshold = self.config.get("anomaly_threshold", 100)
        metric = data.get("metric", "unknown")
        anomaly_type = data.get("type", "threshold_exceeded")

        if value is not None and value > threshold:
            report = {
                "timestamp": datetime.now().isoformat(),
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "anomaly_type": anomaly_type,
                "message": data.get("message", f"Value {value} exceeds threshold {threshold}"),
            }
            self._log_to_history(report)
            self.anomaly_type_counts[anomaly_type] = self.anomaly_type_counts.get(anomaly_type, 0) + 1
            logger.warning(f"Anomaly detected: {report['message']}", exc_info=True)
            return report
        return None

    def automated_response(self, anomaly_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triggers an automated response to a detected anomaly.
        Routes response action based on anomaly type.
        """
        logger.info(f"Triggering automated response for anomaly: {anomaly_details}")
        anomaly_type = anomaly_details.get("anomaly_type", "unknown")
        metric = anomaly_details.get("metric", "unknown")
        value = anomaly_details.get("value", 0)

        actions = {
            "threshold_exceeded": f"Scaling resources for metric '{metric}' (value {value})",
            "memory_leak": f"Restarting service for metric '{metric}'",
            "latency_spike": f"Throttling requests for metric '{metric}'",
            "error_rate": f"Notifying operator for metric '{metric}' (value {value})",
        }
        action = actions.get(anomaly_type, f"Logged anomaly on metric '{metric}'")

        response = {
            "status": "response_initiated",
            "anomaly_type": anomaly_type,
            "metric": metric,
            "action_taken": action,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(f"Automated response: {action}")
        return response

    def _log_to_history(self, entry: Dict[str, Any]) -> None:
        """
        Logs an anomaly entry to the internal history.
        """
        self.anomaly_history.append(entry)
        logger.debug(f"Anomaly logged to history (total: {len(self.anomaly_history)})")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the AIOps engine."""
        return {
            "monitoring_active": self.monitoring_active,
            "config": self.config,
            "anomaly_count": len(self.anomaly_history),
            "anomaly_type_counts": dict(self.anomaly_type_counts),
            "timestamp": datetime.now().isoformat(),
        }


    async def initialize(self) -> None:
        logger.info("AIOpsEngine initialized async")

    async def collect_system_metrics(self, component_id: str, component_type: str, metrics: Dict[str, float]) -> None:
        state = {
            "component_id": component_id,
            "component_type": component_type,
            "timestamp": datetime.now().isoformat(),
            "state": metrics,
        }
        self.system_states.append(state)

    async def detect_anomalies(self, component_id: str, metrics: Dict[str, float]) -> List[AnomalyResult]:
        anomalies = []
        cpu = metrics.get("cpu_usage", 0)
        memory = metrics.get("memory_usage", 0)
        error_rate = metrics.get("error_rate", 0)
        response_time = metrics.get("response_time", 0)

        if cpu > 90:
            anomalies.append(AnomalyResult(
                anomaly_type="high_cpu",
                severity=Severity.HIGH,
                confidence=0.9,
                description=f"CPU usage at {cpu}%",
                recommended_actions=["Scale CPU resources", "Optimize CPU-intensive tasks"],
            ))
        if memory > 85:
            anomalies.append(AnomalyResult(
                anomaly_type="high_memory",
                severity=Severity.HIGH,
                confidence=0.85,
                description=f"Memory usage at {memory}%",
                recommended_actions=["Increase memory", "Optimize memory usage"],
            ))
        if error_rate > 5.0:
            anomalies.append(AnomalyResult(
                anomaly_type="high_error_rate",
                severity=Severity.CRITICAL,
                confidence=0.95,
                description=f"Error rate at {error_rate}%",
                recommended_actions=["Investigate error sources", "Restart service"],
            ))
        if response_time > 1000:
            anomalies.append(AnomalyResult(
                anomaly_type="high_response_time",
                severity=Severity.HIGH,
                confidence=0.8,
                description=f"Response time at {response_time}ms",
                recommended_actions=["Optimize query performance", "Scale horizontally"],
            ))
        return anomalies

    async def predict_capacity_needs(self) -> Dict[str, Any]:
        if len(self.system_states) < 10:
            return {"error": "數據不足"}
        cpu_values = [s["state"].get("cpu_usage", 50) for s in self.system_states if "state" in s]
        if not cpu_values:
            return {"error": "數據不足"}
        current_cpu = cpu_values[-1]
        total_cpu = sum(cpu_values)
        avg_cpu = total_cpu / len(cpu_values)
        trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing" if cpu_values[-1] < cpu_values[0] else "stable"
        predicted_cpu = avg_cpu * 1.2
        confidence = min(0.9, 0.5 + len(cpu_values) * 0.02)
        return {
            "predicted_cpu": round(predicted_cpu, 2),
            "current_cpu": current_cpu,
            "trend": trend,
            "confidence": round(confidence, 2),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info("--- AIOpsEngine Example Usage ---")

    engine = AIOpsEngine(config={"anomaly_threshold": 150})
    logger.info(f"Initial status: {engine.get_status()}")

    engine.start_monitoring()
    logger.info(f"Status after starting monitoring: {engine.get_status()}")

    # Test anomaly detection
    logger.info("\n--- Testing Anomaly Detection ---")
    data1 = {"metric": "cpu_usage", "value": 80}
    data2 = {"metric": "memory_leak", "value": 180, "message": "High memory usage detected", "type": "memory_leak"}

    report1 = engine.detect_anomaly(data1)
    if report1:
        logger.info(f"Anomaly detected for data1. Response: {engine.automated_response(report1)}")
    else:
        logger.info("No anomaly detected for data1.")

    report2 = engine.detect_anomaly(data2)
    if report2:
        logger.info(f"Anomaly detected for data2. Response: {engine.automated_response(report2)}")
    else:
        logger.info("No anomaly detected for data2.")

    engine.stop_monitoring()
    logger.info(f"Status after stopping monitoring: {engine.get_status()}")

    logger.info("\n--- AIOpsEngine Example Finished ---")
