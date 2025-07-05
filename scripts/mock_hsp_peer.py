# scripts/mock_hsp_peer.py
import asyncio
import json
import time
import uuid
from datetime import datetime, timezone

# We need to ensure that 'src' is in PYTHONPATH if running this script directly
# This adds the project root to sys.path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hsp.connector import HSPConnector
from src.hsp.types import HSPMessageEnvelope, HSPFactPayload #, HSPTaskRequestPayload, HSPTaskResultPayload # Add more as needed

# Define other payload types that might be used by the mock, even if just for type hinting
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPEnvironmentalStatePayload


class MockHSPPeer:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int = 1883):
        self.ai_id = ai_id
        self.connector = HSPConnector(
            ai_id=self.ai_id,
            broker_address=broker_address,
            broker_port=broker_port,
            client_id_suffix="mock_peer" # Unique suffix for MQTT client ID
        )
        self.connector.register_on_generic_message_callback(self.handle_generic_hsp_message)
        self.connector.register_on_fact_callback(self.handle_fact_message)
        # self.connector.register_on_task_request_callback(self.handle_task_request_message) # Example for future

    def handle_generic_hsp_message(self, envelope: HSPMessageEnvelope, topic: str) -> None:
        print(f"\n[MockPeer-{self.ai_id}] Received generic HSP message on MQTT topic '{topic}':")
        print(f"  Msg ID  : {envelope.get('message_id')}")
        print(f"  Sender  : {envelope.get('sender_ai_id')}")
        print(f"  Type    : {envelope.get('message_type')}")
        # Avoid printing large payloads in generic handler unless debugging
        # print(f"  Payload: {json.dumps(envelope.get('payload'), indent=2)}")

    def handle_fact_message(self, fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None:
        print(f"\n[MockPeer-{self.ai_id}] Received FACT from '{sender_ai_id}' (MQTT topic: '{full_envelope.get('recipient_ai_id')}'):")
        statement_nl = fact_payload.get('statement_nl', 'N/A')
        statement_structured = fact_payload.get('statement_structured', {})
        statement_to_print = statement_nl if statement_nl != 'N/A' else statement_structured

        print(f"  Fact ID    : {fact_payload.get('id')}")
        print(f"  Statement  : {statement_to_print}")
        print(f"  Confidence : {fact_payload.get('confidence_score')}")

    # Example for handling task requests - would require HSPConnector to have a specific callback registration for this
    # def handle_task_request_message(self, task_payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope):
    #     print(f"\n[MockPeer-{self.ai_id}] Received TASK REQUEST from {sender_id}")
    #     capability_requested = task_payload.get('capability_id_filter') or task_payload.get('capability_name_filter')
    #     print(f"  Capability: {capability_requested}")
    #     print(f"  Parameters: {task_payload.get('parameters')}")
    #     # Mock sending a result
    #     if capability_requested == "mock_echo_v1" and envelope.get('correlation_id'):
    #         result_payload = HSPTaskResultPayload(
    #             result_id=f"taskres_{uuid.uuid4().hex}",
    #             request_id=task_payload['request_id'], # type: ignore # request_id is required
    #             executing_ai_id=self.ai_id,
    #             status="success",
    #             payload={"echoed_data": task_payload.get('parameters')},
    #             timestamp_completed=datetime.now(timezone.utc).isoformat()
    #         )
    #         # The connector would need a method like send_response or send_task_result
    #         # self.connector.send_hsp_response(result_payload, "HSP::TaskResult_v0.1", envelope['sender_ai_id'], envelope['correlation_id'])
    #         print(f"  MockPeer: Would send TaskResult for request {task_payload.get('request_id')}")


    async def run_loop(self):
        """Main loop for the mock peer to publish sample data periodically."""
        fact_counter = 0
        env_counter = 0
        while self.connector.is_connected:
            await asyncio.sleep(15) # Action every 15 seconds

            # Alternate between publishing a fact and an environmental state
            if fact_counter <= env_counter:
                fact_counter += 1
                print(f"\n[MockPeer-{self.ai_id}] Periodic action: Publishing sample fact {fact_counter}...")
                self.publish_sample_fact(fact_counter)
            else:
                env_counter += 1
                print(f"\n[MockPeer-{self.ai_id}] Periodic action: Publishing sample environment state {env_counter}...")
                self.publish_sample_environmental_state(env_counter)


    def publish_sample_fact(self, counter: int):
        if not self.connector.is_connected:
            return

        fact_id = f"mock_fact_{self.ai_id.replace(':', '_')}_{counter}_{uuid.uuid4().hex[:4]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        topic = "hsp/knowledge/facts/general"

        if counter % 2 == 0: # Publish a structured fact (semantic triple)
            fact_payload = HSPFactPayload(
                id=fact_id,
                statement_type="semantic_triple",
                statement_structured={ # type: ignore
                    "subject_uri": f"hsp:entity:mock_subject_{counter}",
                    "predicate_uri": "hsp:property:has_status",
                    "object_literal": f"active_state_{counter}",
                    "object_datatype": "xsd:string"
                },
                statement_nl=f"Mock subject {counter} has status active_state_{counter}.", # Optional NL representation
                source_ai_id=self.ai_id,
                timestamp_created=timestamp,
                confidence_score=0.98,
                tags=["sample_mock_fact", "structured_triple"]
            )
            print(f"[MockPeer-{self.ai_id}] Publishing STRUCTURED sample fact to '{topic}' (ID: {fact_payload['id']})")
        else: # Publish a natural language fact
            fact_payload = HSPFactPayload(
                id=fact_id,
                statement_type="natural_language",
                statement_nl=f"This is sample natural language fact number {counter} from {self.ai_id} about a random event.",
                source_ai_id=self.ai_id,
                timestamp_created=timestamp,
                confidence_score=0.92,
                tags=["sample_mock_fact", "natural_language"]
            )
            print(f"[MockPeer-{self.ai_id}] Publishing NL sample fact to '{topic}' (ID: {fact_payload['id']})")

        self.connector.publish_fact(fact_payload, topic=topic)


    def publish_sample_environmental_state(self, counter: int):
        """Example of the mock peer publishing something."""
        if not self.connector.is_connected:
            return

        payload = HSPEnvironmentalStatePayload( # type: ignore # TypedDict should be fine
            update_id=f"env_update_{uuid.uuid4().hex[:6]}",
            source_ai_id=self.ai_id, # This AI is the source
            phenomenon_type="hsp:event:MockPeerHeartbeat",
            parameters={"count": counter, "status": "alive", "peer_id": self.ai_id},
            timestamp_observed=datetime.now(timezone.utc).isoformat(),
            scope_type="global"
        )
        topic = "hsp/environment/peer_updates" # CLI peer doesn't subscribe to this by default
        print(f"[MockPeer-{self.ai_id}] Publishing sample environmental state to '{topic}' (ID: {payload['update_id']})")

        envelope = self.connector._build_hsp_envelope(
            payload=payload,
            message_type="HSP::EnvironmentalState_v0.1",
            recipient_ai_id_or_topic=topic,
            communication_pattern="publish"
        )
        self.connector._send_hsp_message(envelope, mqtt_topic=topic)


    async def start(self):
        print(f"[MockPeer-{self.ai_id}] Attempting to connect...")
        if self.connector.connect(): # This starts the MQTT client's own network loop thread
            # Wait briefly for the on_connect callback to fire and set self.connector.is_connected
            await asyncio.sleep(1)

            if self.connector.is_connected:
                print(f"[MockPeer-{self.ai_id}] Successfully connected to MQTT broker.")
                # Subscribe to topics of interest
                self.connector.subscribe("hsp/knowledge/facts/#") # All facts
                self.connector.subscribe(f"hsp/requests/{self.ai_id}/#") # Task requests for this mock AI (example)
                self.connector.subscribe("hsp/knowledge/facts/user_statements") # From LearningManager
                self.connector.subscribe("hsp/knowledge/facts/user_preferences") # From LearningManager
                self.connector.subscribe("hsp/knowledge/facts/general") # From LearningManager default

                print(f"[MockPeer-{self.ai_id}] Subscribed to relevant topics. Listening...")

                # Start a task for periodic publishing
                asyncio.create_task(self.run_loop())

                # Keep the main start task alive to listen (or until KeyboardInterrupt)
                # The actual listening happens in the MQTT client's thread.
                # This loop is just to keep the script running.
                while True:
                    await asyncio.sleep(1)
            else:
                print(f"[MockPeer-{self.ai_id}] Failed to establish connection after connect() call.")
        else:
            print(f"[MockPeer-{self.ai_id}] Initial MqttClient.connect() call failed or did not initiate connection.")

    def stop(self):
        print(f"[MockPeer-{self.ai_id}] Stopping...")
        self.connector.disconnect()
        print(f"[MockPeer-{self.ai_id}] Disconnected.")


async def main_async_runner():
    peer_id = f"did:hsp:mock_peer_{uuid.uuid4().hex[:8]}"
    print(f"--- Starting Mock HSP Peer --- \nID: {peer_id}")
    # Ensure MQTT broker is running at localhost:1883
    peer = MockHSPPeer(ai_id=peer_id, broker_address="localhost", broker_port=1883)

    try:
        await peer.start()
    except KeyboardInterrupt:
        print(f"\n[MockPeer-{peer_id}] KeyboardInterrupt received.")
    except Exception as e:
        print(f"[MockPeer-{peer_id}] An error occurred: {e}")
    finally:
        print(f"[MockPeer-{peer_id}] Shutting down...")
        peer.stop()
        # Allow time for MQTT disconnect to complete
        await asyncio.sleep(1)
        print(f"[MockPeer-{peer_id}] Exited.")

if __name__ == "__main__":
    # To run this:
    # 1. Ensure MQTT broker is running (e.g., `docker run -it -p 1883:1883 -p 9001:9001 eclipse-mosquitto`)
    # 2. Run this script: python scripts/mock_hsp_peer.py
    # 3. Separately, run your main AI application which also connects to HSP and publishes.

    # Add a simple check for paho-mqtt
    try:
        import paho.mqtt.client
    except ImportError:
        print("Error: paho-mqtt library not found. Please install it: pip install paho-mqtt")
        sys.exit(1)

    asyncio.run(main_async_runner())
```
