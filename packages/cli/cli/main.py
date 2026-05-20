import argparse
import json
import sys
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import asyncio
import importlib
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent.parent
backend_src = project_root / "apps" / "backend" / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_src))

try:
    core_services = importlib.import_module('core_services')
    hsp_types = importlib.import_module('hsp.types')

    initialize_services = getattr(core_services, 'initialize_services')
    get_services = getattr(core_services, 'get_services')
    shutdown_services = getattr(core_services, 'shutdown_services')
    DEFAULT_OPERATIONAL_CONFIGS = getattr(core_services, 'DEFAULT_OPERATIONAL_CONFIGS')

    HSPFactPayload = getattr(hsp_types, 'HSPFactPayload')
    HSPMessageEnvelope = getattr(hsp_types, 'HSPMessageEnvelope')
    HSPCapabilityAdvertisementPayload = getattr(hsp_types, 'HSPCapabilityAdvertisementPayload')
    HSPTaskResultPayload = getattr(hsp_types, 'HSPTaskResultPayload')
except ImportError as e:
    print(f"Failed to import core service modules: {e}")
    print("Ensure the backend service is properly installed")
    sys.exit(1)

from .error_handler import error_handler

cli_ai_id = f"did:hsp:cli_ai_instance_{uuid.uuid4().hex[:6]}"


def cli_handle_incoming_hsp_fact(fact_payload: Any, sender_ai_id: str,
                                  full_envelope: HSPMessageEnvelope):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        print(f"\n[CLI App] HSP Fact Received from '{sender_ai_id}':")
        print(f"  Fact ID: {fact_payload.get('id')} Statement: "
              f"{fact_payload.get('statement_nl') or fact_payload.get('statement_structured')}")
        if learning_manager:
            print("  Forwarding to LearningManager for processing...")
            learning_manager.process_and_store_hsp_fact(fact_payload, sender_ai_id, full_envelope)
        else:
            print("  LearningManager not available, cannot process HSP fact.")
    except Exception as e:
        error_handler.handle_exception(e, "cli_handle_incoming_hsp_fact")


def cli_handle_incoming_capability_advertisement(cap_payload: Any, sender_ai_id: str,
                                                  full_envelope: HSPMessageEnvelope):
    try:
        services = get_services()
        service_discovery_module = services.get("service_discovery")
        print(f"\n[CLI App] HSP Capability Advertisement Received from '{sender_ai_id}':")
        print(f"  Capability ID: {cap_payload.get('capability_id')} "
              f"Name: {cap_payload.get('name')}")
        if service_discovery_module:
            service_discovery_module.process_capability_advertisement(
                cap_payload, sender_ai_id, full_envelope)
        else:
            print("  ServiceDiscoveryModule not available, cannot process advertisement.")
    except Exception as e:
        error_handler.handle_exception(e, "cli_handle_incoming_capability_advertisement")


def cli_handle_incoming_task_result(result_payload: Any, sender_ai_id: str,
                                     full_envelope: HSPMessageEnvelope):
    try:
        print(f"\n[CLI App] Generic HSP TaskResult Received from '{sender_ai_id}' "
              f"for CorrID '{full_envelope.get('correlation_id')}':")
        print(f"  Status: {result_payload.get('status')} "
              f"Payload: {result_payload.get('payload')}")
    except Exception as e:
        error_handler.handle_exception(e, "cli_handle_incoming_task_result")


def setup_cli_hsp_callbacks():
    try:
        services = get_services()
        hsp_connector = services.get("hsp_connector")
        if hsp_connector:
            print("CLI App: Core service HSP callbacks are expected to be "
                  "registered by initialize_services.")
            error_handler.log_info(
                "CLI App: Core service HSP callbacks are expected to be "
                "registered by initialize_services.")
        else:
            error_message = ("CLI App: HSPConnector not available from core_services. "
                             "Cannot register CLI HSP callbacks.")
            print(f"CLI Error: {error_message}")
            error_handler.log_error(error_message)
    except Exception as e:
        error_handler.handle_exception(e, "setup_cli_hsp_callbacks")


async def handle_query(args):
    try:
        services = get_services()
        dialogue_manager = services.get("dialogue_manager")
        if not dialogue_manager:
            error_message = "DialogueManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"CLI: Sending query to DialogueManager: '{args.query_text}'")
        error_handler.log_info(f"Sending query to DialogueManager: '{args.query_text}'")

        response_text = await dialogue_manager.get_simple_response(
            user_input=args.query_text,
            user_id="cli_user",
            session_id=f"cli_session_{uuid.uuid4().hex[:6]}",
        )
        print(f"AI: {response_text}")
        error_handler.log_info(f"Received response from DialogueManager: '{response_text}'")
    except Exception as e:
        error_handler.handle_exception(e, "handle_query")


async def handle_publish_fact(args):
    try:
        services = get_services()
        hsp_connector = services.get("hsp_connector")
        dm_instance = services.get("dialogue_manager")
        current_instance_ai_id = dm_instance.ai_id if dm_instance else cli_ai_id

        if not hsp_connector or not hsp_connector.is_connected:
            error_message = "HSPConnector not ready for publishing."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"CLI: Publishing a manual fact via HSP as AI "
              f"'{current_instance_ai_id}': '{args.fact_statement}'")
        error_handler.log_info(
            f"Publishing a manual fact via HSP as AI "
            f"'{current_instance_ai_id}': '{args.fact_statement}'")
        fact_id = f"manual_cli_fact_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        hsp_payload = HSPFactPayload(
            id=fact_id,
            statement_type="natural_language",
            statement_nl=args.fact_statement,
            source_ai_id=current_instance_ai_id,
            timestamp_created=timestamp,
            confidence_score=args.confidence,
            weight=1.0,
            tags=["manual_cli_fact"],
        )

        learning_manager_instance = services.get("learning_manager")
        topic = args.topic or (
            learning_manager_instance.default_hsp_fact_topic
            if learning_manager_instance
            else "hsp/knowledge/facts/cli_manual"
        )

        _echo_cb: Optional[Callable] = None
        echo_event: Optional[asyncio.Event] = None
        echoed_envelope: Dict[str, Any] = {}

        if getattr(args, 'wait_echo', False):
            echo_event = asyncio.Event()

            def echo_callback(envelope: HSPMessageEnvelope):
                try:
                    payload = envelope.get("payload") or {}
                    if isinstance(payload, dict) and payload.get("id") == fact_id:
                        echoed_envelope["envelope"] = envelope
                        if echo_event:
                            echo_event.set()
                except Exception as exc:
                    error_handler.log_error(f"Error in echo callback: {str(exc)}")

            try:
                hsp_connector.internal_bus.subscribe("hsp.internal.fact", echo_callback)
                _echo_cb = echo_callback
            except Exception as exc:
                error_handler.log_error(f"Failed to subscribe to internal bus: {str(exc)}")
                _echo_cb = None
                echo_event = None

        success = await hsp_connector.publish_fact(hsp_payload, topic)
        if success:
            success_message = f"Manual fact '{fact_id}' published to topic '{topic}'."
            print(f"CLI: {success_message}")
            error_handler.log_info(success_message)
        else:
            error_message = f"Failed to publish manual fact to topic '{topic}'."
            print(f"CLI: {error_message}")
            error_handler.log_error(error_message)

        if getattr(args, 'wait_echo', False) and echo_event is not None and _echo_cb is not None:
            try:
                timeout_sec = getattr(args, 'echo_timeout', 3.0) or 3.0
                await asyncio.wait_for(echo_event.wait(), timeout=timeout_sec)
                env = echoed_envelope.get("envelope") or {}
                payload = (env.get("payload") if isinstance(env, dict) else None) or {}
                echo_message = "Received internal echo for published fact."
                print("CLI: " + echo_message)
                error_handler.log_info(echo_message)
                print(f"  Echo MessageID: {env.get('message_id')} | "
                      f"Sender: {env.get('sender_ai_id')}")
                print(f"  Echo Fact ID: {payload.get('id')} | "
                      f"Statement: {payload.get('statement_nl') or payload.get('statement_structured')}")
            except asyncio.TimeoutError:
                timeout_message = (f"Timed out waiting for internal echo of fact "
                                   f"'{fact_id}' after {getattr(args, 'echo_timeout', 3.0) or 3.0} seconds.")
                print(f"CLI: {timeout_message}")
                error_handler.log_warning(timeout_message)
            except Exception as exc:
                error_handler.handle_exception(exc, "waiting for echo")
            finally:
                try:
                    hsp_connector.internal_bus.unsubscribe("hsp.internal.fact", _echo_cb)
                except Exception as exc:
                    error_handler.log_error(f"Failed to unsubscribe: {str(exc)}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_publish_fact")


async def handle_model_list(args):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print("Available AI models:")
        print("=" * 50)
        models = getattr(learning_manager, 'get_available_models', lambda: [])()
        if not models:
            print("No models found")
            return
        for model in models:
            print(f"  - {model}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_model_list")


async def handle_model_info(args):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"Model info: {args.model_name}")
        print("=" * 50)
        model_info = getattr(learning_manager, 'get_model_info', lambda x: {})(args.model_name)
        if not model_info:
            print(f"Model '{args.model_name}' not found")
            return
        for key, value in model_info.items():
            print(f"  {key}: {value}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_model_info")


async def handle_train_start(args):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"Starting training for: {args.model_name}")
        print("=" * 50)
        result = getattr(learning_manager, 'start_training',
                         lambda x, y: {"status": "started"})(args.model_name, vars(args))
        print(f"Training status: {result.get('status', 'unknown')}")
        if 'message' in result:
            print(f"Message: {result['message']}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_train_start")


async def handle_train_status(args):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print("Training status:")
        print("=" * 50)
        status = getattr(learning_manager, 'get_training_status',
                         lambda: {"status": "unknown"})()
        for key, value in status.items():
            print(f"  {key}: {value}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_train_status")


async def handle_data_list(args):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print("Training datasets:")
        print("=" * 50)
        datasets = getattr(learning_manager, 'list_datasets', lambda: [])()
        if not datasets:
            print("No datasets found")
            return
        for dataset in datasets:
            print(f"  - {dataset}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_data_list")


async def handle_data_info(args):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"Dataset info: {args.dataset_name}")
        print("=" * 50)
        dataset_info = getattr(learning_manager, 'get_dataset_info',
                               lambda x: {})(args.dataset_name)
        if not dataset_info:
            print(f"Dataset '{args.dataset_name}' not found")
            return
        for key, value in dataset_info.items():
            print(f"  {key}: {value}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_data_info")


async def main_cli_logic():
    try:
        parser = argparse.ArgumentParser(
            description="Unified-AI-Project Command Line Interface")
        subparsers = parser.add_subparsers(dest="command", help="Available commands",
                                           required=False)

        query_parser = subparsers.add_parser("query", help="Send a query to the AI")
        query_parser.add_argument("query_text", type=str,
                                  help="The query text to send to the AI")
        query_parser.set_defaults(func=handle_query)

        publish_parser = subparsers.add_parser(
            "publish_fact", help="Manually publish a fact via HSP")
        publish_parser.add_argument("fact_statement", type=str,
                                    help="The statement of the fact")
        publish_parser.add_argument("--confidence", type=float, default=0.9,
                                    help="Confidence score (0.0-1.0)")
        publish_parser.add_argument("--topic", type=str, help="HSP topic to publish to")
        publish_parser.add_argument("--echo", "--wait", dest="wait_echo",
                                    action="store_true",
                                    help="Wait for internal echo and print it")
        publish_parser.add_argument("--echo-timeout", type=float, default=3.0,
                                    help="Seconds to wait for internal echo (default: 3.0)")
        publish_parser.add_argument("--no-post-sleep", action="store_true",
                                    help="Skip post-command listening sleep (for tests)")
        publish_parser.set_defaults(func=handle_publish_fact)

        model_parser = subparsers.add_parser("model",
                                             help="Model management commands")
        model_subparsers = model_parser.add_subparsers(
            dest="model_command", help="Model management sub-commands")
        model_list_parser = model_subparsers.add_parser(
            "list", help="List all available models")
        model_list_parser.set_defaults(func=handle_model_list)
        model_info_parser = model_subparsers.add_parser(
            "info", help="Show model information")
        model_info_parser.add_argument("model_name", type=str, help="Model name")
        model_info_parser.set_defaults(func=handle_model_info)

        train_parser = subparsers.add_parser("train",
                                             help="Training management commands")
        train_subparsers = train_parser.add_subparsers(
            dest="train_command", help="Training management sub-commands")
        train_start_parser = train_subparsers.add_parser(
            "start", help="Start model training")
        train_start_parser.add_argument("model_name", type=str,
                                        help="Model name to train")
        train_start_parser.add_argument("--preset", type=str,
                                        help="Training preset")
        train_start_parser.add_argument("--resume", action="store_true",
                                        help="Resume training from checkpoint")
        train_start_parser.set_defaults(func=handle_train_start)
        train_status_parser = train_subparsers.add_parser(
            "status", help="Show training status")
        train_status_parser.set_defaults(func=handle_train_status)

        data_parser = subparsers.add_parser("data",
                                            help="Data management commands")
        data_subparsers = data_parser.add_subparsers(
            dest="data_command", help="Data management sub-commands")
        data_list_parser = data_subparsers.add_parser(
            "list", help="List all datasets")
        data_list_parser.set_defaults(func=handle_data_list)
        data_info_parser = data_subparsers.add_parser(
            "info", help="Show dataset information")
        data_info_parser.add_argument("dataset_name", type=str,
                                      help="Dataset name")
        data_info_parser.set_defaults(func=handle_data_info)

        print(f"--- Unified-AI-Project CLI (Instance AI ID: {cli_ai_id}) ---")
        error_handler.log_info(
            f"--- Unified-AI-Project CLI (Instance AI ID: {cli_ai_id}) ---")

        config = {
            "mcp": {
                "mqtt_broker_address": "localhost",
                "mqtt_broker_port": 1883,
                "enable_fallback": True,
                "fallback_config": {},
            }
        }
        await initialize_services(
            config=config,
            ai_id=cli_ai_id,
            use_mock_ham=True,
            operational_configs=DEFAULT_OPERATIONAL_CONFIGS,
        )
        services = get_services()
        service_discovery_module = services.get("service_discovery")
        if service_discovery_module:
            service_discovery_module.start_cleanup_task()
        setup_cli_hsp_callbacks()

        try:
            if len(sys.argv) <= 1:
                parser.print_help(sys.stderr)
                print("\nCLI: No command provided. Listening for HSP messages "
                      "for 60 seconds (Ctrl+C to exit)...")
                error_handler.log_info(
                    "CLI: No command provided. Listening for HSP messages "
                    "for 60 seconds (Ctrl+C to exit)...")
                await asyncio.sleep(60)
                return

            args = parser.parse_args()
            if hasattr(args, 'func'):
                if asyncio.iscoroutinefunction(args.func):
                    await args.func(args)
                else:
                    args.func(args)
                if args.command != "query":
                    print("\nCLI: Task complete. Listening for HSP messages "
                          "for a few seconds (Ctrl+C to exit)...")
                    error_handler.log_info(
                        "CLI: Task complete. Listening for HSP messages "
                        "for a few seconds (Ctrl+C to exit)...")
                    if not getattr(args, 'no_post_sleep', False):
                        await asyncio.sleep(10)
            else:
                parser.print_help(sys.stderr)

        except KeyboardInterrupt:
            print("\nCLI: Keyboard interrupt received. Shutting down...")
            error_handler.log_info("CLI: Keyboard interrupt received. Shutting down...")
        except Exception as e:
            error_message = f"\nCLI Error: An unexpected error occurred: {e}"
            print(error_message)
            error_handler.log_error(error_message)
        finally:
            print("CLI: Initiating service shutdown...")
            error_handler.log_info("CLI: Initiating service shutdown...")
            if service_discovery_module:
                service_discovery_module.stop_cleanup_task()
            await shutdown_services()
            print("CLI: Exiting.")
            error_handler.log_info("CLI: Exiting.")
    except Exception as e:
        error_handler.handle_exception(e, "main_cli_logic")


if __name__ == '__main__':
    asyncio.run(main_cli_logic())
