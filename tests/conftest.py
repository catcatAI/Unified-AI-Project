import pytest
# Delay imports of paho and socket until they are actually needed within a function call,
# as conftest is loaded very early by pytest.
# import paho.mqtt.client as mqtt
# import socket

# --- Configuration for MQTT Broker (used by tests needing a live broker) ---
# These could be moved to a more central test config if needed.
MQTT_BROKER_ADDRESS = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_CONNECT_TIMEOUT = 2  # Seconds for connection attempt

_mqtt_broker_available = None # Cache the result

def is_mqtt_broker_available(address=MQTT_BROKER_ADDRESS, port=MQTT_BROKER_PORT, timeout=MQTT_CONNECT_TIMEOUT) -> bool:
    """
    Checks if an MQTT broker is available at the given address and port.
    Caches the result to avoid repeated checks during a test session.
    """
    global _mqtt_broker_available
    if _mqtt_broker_available is not None:
        return _mqtt_broker_available

    import paho.mqtt.client as mqtt  # Import here
    import socket  # Import here

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pytest_mqtt_check")
    # Set a short timeout for the socket connection attempt itself
    # Note: client.connect() has its own keepalive, but the initial socket connection
    # can hang if the host is unreachable or port is firewalled.
    # Paho's connect() can be blocking. We need a non-blocking way or a timeout on the socket itself.
    # However, paho's connect() itself doesn't take a direct socket timeout.
    # We can try a direct socket connection test first for a quicker check.

    s = None
    try:
        s = socket.create_connection((address, port), timeout=timeout)
        # If connection is successful, broker is likely there, but not necessarily an MQTT broker.
        # A full client.connect() is better but can hang longer.
        # For a quick check, this is often sufficient to see if *something* is listening.
        _mqtt_broker_available = True
        print(f"\nINFO: MQTT check: Successfully connected to {address}:{port}. Broker assumed available.")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        _mqtt_broker_available = False
        print(f"\nINFO: MQTT check: Failed to connect to {address}:{port} (timeout={timeout}s). Broker assumed unavailable. Error: {e}")
    finally:
        if s:
            s.close()

    # More robust check with Paho client, but this can be slower if broker is down.
    # For now, the socket check is a pragmatic first pass for CI environments.
    # If more accuracy is needed, uncomment and adapt the Paho client connect test:
    # try:
    #     client.connect(address, port, keepalive=timeout*2) # keepalive > timeout
    #     client.disconnect()
    #     _mqtt_broker_available = True
    # except (socket.timeout, ConnectionRefusedError, OSError) as e: # Catching OSError for broader network issues
    #     _mqtt_broker_available = False
    #     print(f"MQTT check: Failed to connect to {address}:{port}. Broker unavailable. Error: {e}")
    # finally:
    #     # Ensure loop is stopped if started, though for a simple connect/disconnect it might not be needed.
    #     client.loop_stop(force=True)


    return _mqtt_broker_available

# Example of how to use it in a test file:
# from .conftest import is_mqtt_broker_available
# @pytest.mark.skipif(not is_mqtt_broker_available(), reason="MQTT broker not available")
# def test_something_requiring_mqtt():
#     assert True

# This fixture could also be used directly in tests if preferred
@pytest.fixture(scope="session")
def mqtt_broker_check():
    return is_mqtt_broker_available()
