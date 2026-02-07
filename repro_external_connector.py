from apps.backend.src.core.hsp.external.external_connector import ExternalConnector

try:
    print("Attempting to instantiate ExternalConnector with broker_address...")
    ec = ExternalConnector(broker_address="localhost")
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
