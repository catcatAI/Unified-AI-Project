import pytest
import socket

def is_mqtt_broker_available():
    """
    Checks if the MQTT broker is available by attempting to create a socket connection.
    """
    try:
        with socket.create_connection(("127.0.0.1", 1883), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False
    except Exception:
        return False
