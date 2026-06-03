import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PredictiveMaintenanceEngine:
    """
    Engine for predictive maintenance, identifying potential failures before they occur.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else {}
        self.sensor_data_history: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("PredictiveMaintenanceEngine initialized.")

    def ingest_sensor_data(self, sensor_id: str, data: Dict[str, Any]) -> None:
        """Ingests new sensor data for analysis."""
        if sensor_id not in self.sensor_data_history:
            self.sensor_data_history[sensor_id] = []
        self.sensor_data_history[sensor_id].append(
            {"timestamp": datetime.now().isoformat(), "data": data}
        )
        logger.debug(f"Ingested data for sensor {sensor_id}: {data}")

    def analyze_for_anomalies(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes historical sensor data for anomalies indicating potential failures.
        Uses deviation-from-mean detection on the sensor's value history.
        """
        history = self.sensor_data_history.get(sensor_id)
        if not history or len(history) < self.config.get("min_history_for_analysis", 5):
            logger.debug(f"Not enough history for sensor {sensor_id} to analyze.")
            return None

        # Simple anomaly detection: check if latest value is significantly different from average
        latest_data = history[-1]["data"]
        if "value" in latest_data:
            values = [entry["data"]["value"] for entry in history if "value" in entry["data"]]
            if values:
                average_value = sum(values) / len(values)
                if abs(latest_data["value"] - average_value) > self.config.get(
                    "anomaly_threshold", 20
                ):
                    anomaly = {
                        "sensor_id": sensor_id,
                        "timestamp": latest_data["timestamp"],
                        "type": "value_deviation",
                        "current_value": latest_data["value"],
                        "average_value": average_value,
                        "message": f"Sensor value {latest_data['value']} deviates significantly from average {average_value:.2f}",
                    }
                    logger.warning(f"Anomaly detected for sensor {sensor_id}: {anomaly['message']}", exc_info=True)
                    return anomaly
        return None

    def predict_failure(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Predicts potential future failures based on current and historical data.
        Computes likelihood from anomaly frequency and deviation magnitude.
        """
        history = self.sensor_data_history.get(sensor_id)
        if not history:
            return None

        total_readings = len(history)
        anomaly_count = 0
        latest_deviation = 0.0

        for i, entry in enumerate(history):
            data = entry["data"]
            if "value" not in data:
                continue
            vals = [h["data"]["value"] for h in history[:i] if "value" in h["data"]]
            if not vals:
                continue
            avg = sum(vals) / len(vals)
            deviation = abs(data["value"] - avg)
            threshold = self.config.get("anomaly_threshold", 20)
            if deviation > threshold:
                anomaly_count += 1
                if i == len(history) - 1:
                    latest_deviation = deviation

        if anomaly_count == 0:
            return None

        anomaly_freq = anomaly_count / total_readings
        deviation_ratio = min(latest_deviation / max(self.config.get("anomaly_threshold", 20), 1), 5.0)
        likelihood = min(anomaly_freq * 0.5 + deviation_ratio * 0.1, 0.95)

        prediction_time = datetime.now() + timedelta(
            hours=self.config.get("prediction_horizon_hours", 24)
        )
        prediction = {
            "sensor_id": sensor_id,
            "predicted_failure_time": prediction_time.isoformat(),
            "likelihood": round(likelihood, 2),
            "anomaly_count": anomaly_count,
            "total_readings": total_readings,
            "details": f"{anomaly_count}/{total_readings} readings deviated from mean (latest deviation: {latest_deviation:.2f})",
        }
        logger.critical(f"Failure predicted for sensor {sensor_id}: {prediction['details']}", exc_info=True)
        return prediction


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("--- PredictiveMaintenanceEngine Example Usage ---")

    engine = PredictiveMaintenanceEngine(
        config={
            "min_history_for_analysis": 3,
            "anomaly_threshold": 10,
            "prediction_horizon_hours": 48,
        }
    )

    # Ingest some data
    engine.ingest_sensor_data("temp_sensor_1", {"value": 25.0})
    engine.ingest_sensor_data("temp_sensor_1", {"value": 26.0})
    engine.ingest_sensor_data("temp_sensor_1", {"value": 27.0})
    engine.ingest_sensor_data("temp_sensor_1", {"value": 38.0})  # Anomaly

    # Analyze and predict
    logger.info("\n--- Analyzing temp_sensor_1 ---")
    prediction = engine.predict_failure("temp_sensor_1")
    if prediction:
        logger.info(f"Prediction for temp_sensor_1: {prediction}")
    else:
        logger.error("No immediate failure predicted for temp_sensor_1.", exc_info=True)

    engine.ingest_sensor_data("pressure_sensor_A", {"value": 100.0})
    engine.ingest_sensor_data("pressure_sensor_A", {"value": 101.0})
    engine.ingest_sensor_data("pressure_sensor_A", {"value": 102.0})

    logger.info("\n--- Analyzing pressure_sensor_A ---")
    prediction = engine.predict_failure("pressure_sensor_A")
    if prediction:
        logger.info(f"Prediction for pressure_sensor_A: {prediction}")
    else:
        logger.error("No immediate failure predicted for pressure_sensor_A.", exc_info=True)

    logger.info("\n--- PredictiveMaintenanceEngine Example Finished ---")
