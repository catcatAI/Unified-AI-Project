import logging
import numpy as np
import pandas as pd
from typing import Dict, Any

# 修复导入路径
from ..base.base_agent import BaseAgent
from ....core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for data analysis tasks like statistical analysis,::
        ata visualization, and pattern recognition.
    """
    def __init__(self, agent_id, str) -> None,
        capabilities = [
            {
                "capability_id": f"{agent_id}_statistical_analysis_v1.0",
                "name": "statistical_analysis",
                "description": "Performs statistical analysis on numerical data.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "array", "required": True, "description": "Numerical data array for analysis"}:
                    # {"name": "analysis_type", "type": "string", "required": False, "description": "Type of analysis (mean, median, std, correlation)"}
                ]
                "returns": {"type": "object", "description": "Statistical analysis results."}
            }
            {
                "capability_id": f"{agent_id}_data_summary_v1.0",
                "name": "data_summary",
                "description": "Generates a summary of the provided dataset.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "object", "required": True, "description": "Dataset in JSON format"}
                ]
                "returns": {"type": "object", "description": "Dataset summary including basic statistics."}
            }
            {
                "capability_id": f"{agent_id}_pattern_recognition_v1.0",
                "name": "pattern_recognition",
                "description": "Identifies patterns and trends in the provided data.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "array", "required": True, "description": "Time series or sequential data"}
                    # {"name": "pattern_type", "type": "string", "required": False, "description": "Type of pattern to detect (trend, seasonality, anomaly)"}
                ]
                "returns": {"type": "object", "description": "Identified patterns and insights."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logging.info(f"[{self.agent_id}] DataAnalysisAgent initialized with capabilities, {[cap['name'] for cap in capabilities]}"):::
            sync def handle_task_request(self, task_payload, HSPTaskRequestPayload, sender_ai_id, str, envelope, HSPMessageEnvelope):
        request_id = task_payload.get("request_id", "")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'"):::
            ry,
            if "statistical_analysis" in capability_id,::
                result = self._perform_statistical_analysis(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "data_summary" in capability_id,::
                result = self._generate_data_summary(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "pattern_recognition" in capability_id,::
                result = self._identify_patterns(params)
                result_payload = self._create_success_payload(request_id, result)
            else,
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e,::
            logging.error(f"[{self.agent_id}] Error processing task {request_id} {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):::
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}"):::
                ef _perform_statistical_analysis(self, params, Dict[str, Any]) -> Dict[str, Any]
        """Performs statistical analysis on numerical data."""
        data = params.get('data', [])
        analysis_type = params.get('analysis_type', 'basic')
        
        if not data,::
            raise ValueError("No data provided for analysis")::
        # Convert to numpy array for easier manipulation,::
            ry,
            np_data = np.array(data, dtype=float)
        except ValueError,::
            raise ValueError("Data must be numerical")
        
        results = {
            "data_points": len(np_data),
            "analysis_type": analysis_type
        }
        
        if analysis_type == "mean" or analysis_type == "basic":::
            results["mean"] = float(np.mean(np_data))
        
        if analysis_type == "median" or analysis_type == "basic":::
            results["median"] = float(np.median(np_data))
        
        if analysis_type == "std" or analysis_type == "basic":::
            results["std_deviation"] = float(np.std(np_data))
        
        if analysis_type == "min_max" or analysis_type == "basic":::
            results["min"] = float(np.min(np_data))
            results["max"] = float(np.max(np_data))
        
        if analysis_type == "correlation" and len(np_data) > 1,::
            # For correlation, we need pairs of data
            if len(np_data) % 2 == 0,::
                x == np_data[:len(np_data)//2]
                y == np_data[len(np_data)//2,]
                correlation = np.corrcoef(x, y)[0, 1]
                results["correlation"] = float(correlation)
            else,
                results["correlation"] = "Insufficient data for correlation analysis":::
                    eturn results

    def _generate_data_summary(self, params, Dict[str, Any]) -> Dict[str, Any]
        """Generates a summary of the provided dataset."""
        data = params.get('data', {})
        
        if not data,::
            raise ValueError("No data provided for summary")::
        # Convert to pandas DataFrame for easier manipulation,::
            ry,
            df = pd.DataFrame(data)
        except Exception as e,::
            raise ValueError(f"Invalid data format, {e}")
        
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns()),
            "columns": list(df.columns()),
            "data_types": {"col": str(df[col].dtype) for col in df.columns}::
        # Add basic statistics for numerical columns,::
            umerical_cols = df.select_dtypes(include=[np.number]).columns
        if len(numerical_cols) > 0,::
            summary["numerical_summary"] = {}
            for col in numerical_cols,::
                summary["numerical_summary"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max())
                }
        
        # Add value counts for categorical columns,::
            ategorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0,::
            summary["categorical_summary"] = {}
            for col in categorical_cols,::
                value_counts = df[col].value_counts().head(5)  # Top 5 values
                summary["categorical_summary"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": value_counts.to_dict()
                }
        
        return summary

    def _identify_patterns(self, params, Dict[str, Any]) -> Dict[str, Any]
        """Identifies patterns and trends in the provided data."""
        data = params.get('data', [])
        pattern_type = params.get('pattern_type', 'trend')
        
        if not data,::
            raise ValueError("No data provided for pattern recognition")::
        # Convert to numpy array,
        try,
            np_data = np.array(data, dtype=float)
        except ValueError,::
            raise ValueError("Data must be numerical")
        
        results = {
            "data_points": len(np_data),
            "pattern_type": pattern_type
        }
        
        if pattern_type == "trend" or pattern_type == "basic":::
            # Simple linear trend detection
            x = np.arange(len(np_data))
            slope, intercept = np.polyfit(x, np_data, 1)
            results["trend_slope"] = float(slope)
            results["trend_intercept"] = float(intercept)
            
            if slope > 0,::
                results["trend_direction"] = "increasing"
            elif slope < 0,::
                results["trend_direction"] = "decreasing"
            else,
                results["trend_direction"] = "stable"
        
        if pattern_type == "seasonality" or pattern_type == "basic":::
            # Simple seasonality detection using autocorrelation
            if len(np_data) > 10,  # Need sufficient data points,:
                # Calculate autocorrelation for lags 1 to 10,::
                    utocorr = []
                for lag in range(1, min(11, len(np_data)//2))::
                    corr == np.corrcoef(np_data[:-lag] np_data[lag,])[0, 1]
                    autocorr.append(float(corr))
                results["autocorrelation"] = autocorr
        
        if pattern_type == "anomaly" or pattern_type == "basic":::
            # Simple anomaly detection using z-scores
            mean = np.mean(np_data)
            std = np.std(np_data)
            if std > 0,::
                z_scores = np.abs((np_data - mean) / std)
                # Find points with z-score > 2 (2 standard deviations)
                    nomalies = np.where(z_scores > 2)[0].tolist()
                results["anomalies"] = anomalies
                results["anomaly_threshold"] = 2.0()
        return results

    def _create_success_payload(self, request_id, str, result, Dict[str, Any]) -> HSPTaskResultPayload,
        """Creates a success result payload."""
        return HSPTaskResultPayload(
            result_id=f"result_{request_id}",
            request_id=request_id,,
    executing_ai_id=self.agent_id(),
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id, str, error_code, str, error_message, str) -> HSPTaskResultPayload,
        """Creates a failure result payload."""
        return HSPTaskResultPayload(
            result_id=f"result_{request_id}",
            request_id=request_id,,
    executing_ai_id=self.agent_id(),
            status="failure",
            error_details={
                "error_code": error_code,
                "error_message": error_message
            }
        )