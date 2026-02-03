import datetime
from datetime import datetime, timezone
from typing import Any


class HSPProtocolConverter:
    """Handles HSP protocol conversion and extensibility logic.
    This class transforms data between different protocol versions or external formats
    and the internal HSP format.
    """

    def __init__(self, target_hsp_version: str = "1.0"):
        self.target_hsp_version = target_hsp_version
        print(
            f"HSPProtocolConverter initialized for HSP version {self.target_hsp_version}.",
        )

    def convert_to_hsp(self, data: dict[str, Any]) -> dict[str, Any]:
        """Converts external data format to HSP format.
        Wraps the original data with protocol version and timestamp.
        """
        print(
            f"Converting data to HSP format (version {self.target_hsp_version}): {data}",
        )
        return {
            "hsp_protocol_version": self.target_hsp_version,
            "timestamp": datetime.datetime.now(timezone.utc).isoformat(),
            "original_data": data,
        }

    def convert_from_hsp(self, hsp_data: dict[str, Any]) -> dict[str, Any]:
        """Converts HSP data format to an external format.
        Checks the protocol version and extracts the original data.
        """
        print(f"Converting HSP data from HSP format: {hsp_data}")
        if hsp_data.get("hsp_protocol_version") == self.target_hsp_version:
            return hsp_data.get("original_data", {})
        print(
            f"Warning: HSP protocol version mismatch. Expected {self.target_hsp_version}, got {hsp_data.get('hsp_protocol_version')}",
        )
        return {"error": "Protocol version mismatch", "hsp_data": hsp_data}


if __name__ == "__main__":
    converter = HSPProtocolConverter()

    sample_data = {"event": "agent_registered", "agent_id": "agent123"}
    hsp_converted = converter.convert_to_hsp(sample_data)
    print(f"HSP Converted: {hsp_converted}")

    external_converted = converter.convert_from_hsp(hsp_converted)
    print(f"External Converted: {external_converted}")
