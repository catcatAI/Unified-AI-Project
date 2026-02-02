from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel

class HSPPacketType(str, Enum):
    """Enum for HSP Packet Types."""
    HANDSHAKE = "HANDSHAKE"
    HEARTBEAT = "HEARTBEAT"
    DATA = "DATA"
    COMMAND = "COMMAND"
    ACK = "ACK"
    ERROR = "ERROR"

class HSPPriority(str, Enum):
    """Enum for HSP Packet Priority."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class HSPPacket(BaseModel):
    """Standard HSP Packet Structure."""
    packet_id: str
    type: HSPPacketType
    source_id: str
    target_id: str
    payload: Dict[str, Any]
    priority: HSPPriority = HSPPriority.NORMAL
    timestamp: float
    checksum: Optional[str] = None

    class Config:
        use_enum_values = True
