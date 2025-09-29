import argparse
import requests
import json
import sys
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import asyncio
import importlib

# Add the backend src directory to the Python path
project_root = Path(__file__).parent.parent.parent.parent
backend_src = project_root / "apps" / "backend" / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_src))

# Core imports - 修复导入路径
try:
    # 动态导入模块
    core_services = importlib.import_module('core_services')
    hsp_types = importlib.import_module('hsp.types')
    
    # 使用getattr获取函数和变量
    initialize_services = getattr(core_services, 'initialize_services')
    get_services = getattr(core_services, 'get_services')
    shutdown_services = getattr(core_services, 'shutdown_services')
    DEFAULT_OPERATIONAL_CONFIGS = getattr(core_services, 'DEFAULT_OPERATIONAL_CONFIGS')
    
    # 使用getattr获取类型
    HSPFactPayload = getattr(hsp_types, 'HSPFactPayload')
    HSPMessageEnvelope = getattr(hsp_types, 'HSPMessageEnvelope')
    HSPCapabilityAdvertisementPayload = getattr(hsp_types, 'HSPCapabilityAdvertisementPayload')
    HSPTaskResultPayload = getattr(hsp_types, 'HSPTaskResultPayload')
except ImportError as e:
    print(f"导入核心服务模块失败: {e}")
    print("请确保后端服务已正确安装")
    sys.exit(1)

from .error_handler import error_handler

# --- CLI Specific AI ID ---
cli_ai_id = f"did:hsp:cli_ai_instance_{uuid.uuid4().hex[:6]}"

# --- HSP Callbacks for CLI ---
# These callbacks will now use services obtained from get_services()
def cli_handle_incoming_hsp_fact(fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        print(f"\n[CLI App] HSP Fact Received from '{sender_ai_id}':")
        print(f"  Fact ID: {fact_payload.get('id')}, Statement: {fact_payload.get('statement_nl') or fact_payload.get('statement_structured')}")
        if learning_manager:
            print(f"  Forwarding to LearningManager for processing...")
            # Note: LearningManager's process_and_store_hsp_fact might call ContentAnalyzer internally
            learning_manager.process_and_store_hsp_fact(fact_payload, sender_ai_id, full_envelope)
        else:
            print("  LearningManager not available via core_services, cannot process HSP fact.")
    except Exception as e:
        error_handler.handle_exception(e, "cli_handle_incoming_hsp_fact")

def cli_handle_incoming_capability_advertisement(cap_payload: HSPCapabilityAdvertisementPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    try:
        services = get_services()
        service_discovery_module = services.get("service_discovery")
        print(f"\n[CLI App] HSP Capability Advertisement Received from '{sender_ai_id}':")
        print(f"  Capability ID: {cap_payload.get('capability_id')}, Name: {cap_payload.get('name')}")
        if service_discovery_module:
            service_discovery_module.process_capability_advertisement(cap_payload, sender_ai_id, full_envelope)
        else:
            print("  ServiceDiscoveryModule not available via core_services, cannot process capability advertisement.")
    except Exception as e:
        error_handler.handle_exception(e, "cli_handle_incoming_capability_advertisement")

def cli_handle_incoming_task_result(result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    try:
        # This is a generic handler for task results if CLI were to directly observe them.
        # However, DialogueManager handles task results it initiated.
        # This callback might be useful if CLI itself sends a task request and needs to handle the result directly.
        # For now, DM's own callback registered in its __init__ (via core_services) handles results for DM-initiated tasks.
        print(f"\n[CLI App] Generic HSP TaskResult Received from '{sender_ai_id}' for CorrID '{full_envelope.get('correlation_id')}':")
        print(f"  Status: {result_payload.get('status')}, Payload: {result_payload.get('payload')}")
    except Exception as e:
        error_handler.handle_exception(e, "cli_handle_incoming_task_result")


def setup_cli_hsp_callbacks():
    """Registers CLI-specific HSP callbacks AFTER core services are initialized."""
    try:
        services = get_services()
        hsp_connector = services.get("hsp_connector")
        if hsp_connector:
            # The core_services.initialize_services already registers:
            # - LearningManager's fact callback
            # - ServiceDiscoveryModule's capability advertisement callback
            # - DialogueManager's task result callback (via DM's __init__)

            # If CLI needs to *additionally* or *differently* handle these, register here.
            # For example, to just print *all* facts, not just those processed by LM:
            # hsp_connector.register_on_fact_callback(cli_handle_incoming_hsp_fact)
            # For now, we rely on the service-level registrations done in core_services.
            print("CLI App: Core service HSP callbacks are expected to be registered by initialize_services.")
            error_handler.log_info("CLI App: Core service HSP callbacks are expected to be registered by initialize_services.")
            # If we wanted the CLI to also directly see all facts (in addition to LM), we could do:
            # hsp_connector.register_on_fact_callback(cli_handle_incoming_hsp_fact) # This would make CLI print them too.
            # hsp_connector.register_on_capability_advertisement_callback(cli_handle_incoming_capability_advertisement) # If SDM wasn't already doing it.
            # hsp_connector.register_on_task_result_callback(cli_handle_incoming_task_result) # If CLI needs to see ALL task results.

        else:
            error_message = "CLI App: HSPConnector not available from core_services. Cannot register CLI HSP callbacks."
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
            session_id=f"cli_session_{uuid.uuid4().hex[:6]}" # Unique session for each query
        )
        print(f"AI: {response_text}")
        error_handler.log_info(f"Received response from DialogueManager: '{response_text}'")
    except Exception as e:
        error_handler.handle_exception(e, "handle_query")


async def handle_publish_fact(args):
    try:
        services = get_services()
        hsp_connector = services.get("hsp_connector")
        # The AI ID used for publishing should be the one this CLI instance was initialized with.
        # core_services.initialize_services takes an ai_id.
        # We stored it as `cli_ai_id` at the top of this script for clarity.

        # Retrieve the AI ID that the services were initialized with
        # This assumes that the services (like DM) store their ai_id
        dm_instance = services.get("dialogue_manager")
        current_instance_ai_id = dm_instance.ai_id if dm_instance else cli_ai_id


        if not hsp_connector or not hsp_connector.is_connected:
            error_message = "HSPConnector not ready for publishing."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"CLI: Publishing a manual fact via HSP as AI '{current_instance_ai_id}': '{args.fact_statement}'")
        error_handler.log_info(f"Publishing a manual fact via HSP as AI '{current_instance_ai_id}': '{args.fact_statement}'")
        fact_id = f"manual_cli_fact_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        hsp_payload = HSPFactPayload(
            id=fact_id,
            statement_type="natural_language",
            statement_nl=args.fact_statement,
            source_ai_id=current_instance_ai_id,
            timestamp_created=timestamp,
            confidence_score=args.confidence,
            weight=1.0, #type: ignore
            tags=["manual_cli_fact"] #type: ignore
        )

        learning_manager_instance = services.get("learning_manager")
        topic = args.topic or (learning_manager_instance.default_hsp_fact_topic if learning_manager_instance else "hsp/knowledge/facts/cli_manual") #type: ignore

        # Optional: wait for internal echo on hsp.internal.fact
        _echo_cb: Optional[Callable] = None
        echo_event: Optional[asyncio.Event] = None
        echoed_envelope: Dict[str, Any] = {}
        if getattr(args, 'wait_echo', False):
            echo_event = asyncio.Event()
            def echo_callback(envelope: HSPMessageEnvelope):
                try:
                    payload = envelope.get("payload") or {}
                    if isinstance(payload, dict) and payload.get("id") == fact_id:
                        # Capture the envelope and signal
                        echoed_envelope["envelope"] = envelope
                        if echo_event:
                            echo_event.set()
                except Exception as e:
                    error_handler.log_error(f"Error in echo callback: {str(e)}")
                    # Non-fatal: just ignore echo parsing issues
                    pass
            # Subscribe before publishing to avoid missing the echo
            try:
                hsp_connector.internal_bus.subscribe("hsp.internal.fact", echo_callback)
                _echo_cb = echo_callback
            except Exception as e:
                error_handler.log_error(f"Failed to subscribe to internal bus: {str(e)}")
                # If internal bus subscription fails, continue without echo waiting
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

        # If echo waiting enabled, await the event with timeout and then unsubscribe
        if getattr(args, 'wait_echo', False) and echo_event is not None and _echo_cb is not None:
            try:
                timeout_sec = getattr(args, 'echo_timeout', 3.0) or 3.0
                await asyncio.wait_for(echo_event.wait(), timeout=timeout_sec)
                env = echoed_envelope.get("envelope") or {}
                payload = (env.get("payload") if isinstance(env, dict) else None) or {}
                echo_message = "Received internal echo for published fact:"
                print("CLI: " + echo_message)
                error_handler.log_info(echo_message)
                print(f"  Echo MessageID: {env.get('message_id')} | Sender: {env.get('sender_ai_id')}")
                print(f"  Echo Fact ID: {payload.get('id')} | Statement: {payload.get('statement_nl') or payload.get('statement_structured')}")
            except asyncio.TimeoutError:
                timeout_message = f"Timed out waiting for internal echo of fact '{fact_id}' after {getattr(args, 'echo_timeout', 3.0) or 3.0} seconds."
                print(f"CLI: {timeout_message}")
                error_handler.log_warning(timeout_message)
            except Exception as e:
                error_handler.handle_exception(e, "waiting for echo")
            finally:
                try:
                    hsp_connector.internal_bus.unsubscribe("hsp.internal.fact", _echo_cb)
                except Exception as e:
                    error_handler.log_error(f"Failed to unsubscribe from internal bus: {str(e)}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_publish_fact")


# 新增：模型管理命令
async def handle_model_list(args):
    """列出所有可用的AI模型"""
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print("📋 可用的AI模型:")
        print("=" * 50)
        
        # 获取模型列表（这里需要根据实际实现调整）
        # 假设有一个方法可以获取模型信息
        models = getattr(learning_manager, 'get_available_models', lambda: [])()
        if not models:
            print("未找到可用模型")
            return
            
        for model in models:
            print(f"  - {model}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_model_list")


async def handle_model_info(args):
    """显示模型详细信息"""
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"🔍 模型信息: {args.model_name}")
        print("=" * 50)
        
        # 获取模型详细信息（这里需要根据实际实现调整）
        model_info = getattr(learning_manager, 'get_model_info', lambda x: {})(args.model_name)
        if not model_info:
            print(f"未找到模型 '{args.model_name}' 的信息")
            return
            
        for key, value in model_info.items():
            print(f"  {key}: {value}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_model_info")


# 新增：训练管理命令
async def handle_train_start(args):
    """启动模型训练"""
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"🚀 启动模型训练: {args.model_name}")
        print("=" * 50)
        
        # 启动训练（这里需要根据实际实现调整）
        result = getattr(learning_manager, 'start_training', lambda x, y: {"status": "started"})(args.model_name, vars(args))
        print(f"训练状态: {result.get('status', 'unknown')}")
        if 'message' in result:
            print(f"消息: {result['message']}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_train_start")


async def handle_train_status(args):
    """查看训练状态"""
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print("📊 训练状态:")
        print("=" * 50)
        
        # 获取训练状态（这里需要根据实际实现调整）
        status = getattr(learning_manager, 'get_training_status', lambda: {"status": "unknown"})()
        for key, value in status.items():
            print(f"  {key}: {value}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_train_status")


# 新增：数据管理命令
async def handle_data_list(args):
    """列出训练数据集"""
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print("📂 训练数据集:")
        print("=" * 50)
        
        # 获取数据集列表（这里需要根据实际实现调整）
        datasets = getattr(learning_manager, 'list_datasets', lambda: [])()
        if not datasets:
            print("未找到数据集")
            return
            
        for dataset in datasets:
            print(f"  - {dataset}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_data_list")


async def handle_data_info(args):
    """显示数据集详细信息"""
    try:
        services = get_services()
        learning_manager = services.get("learning_manager")
        if not learning_manager:
            error_message = "LearningManager not available from core_services."
            error_handler.log_error(error_message)
            print(f"CLI Error: {error_message}")
            return

        print(f"🔍 数据集信息: {args.dataset_name}")
        print("=" * 50)
        
        # 获取数据集详细信息（这里需要根据实际实现调整）
        dataset_info = getattr(learning_manager, 'get_dataset_info', lambda x: {})(args.dataset_name)
        if not dataset_info:
            print(f"未找到数据集 '{args.dataset_name}' 的信息")
            return
            
        for key, value in dataset_info.items():
            print(f"  {key}: {value}")
    except Exception as e:
        error_handler.handle_exception(e, "handle_data_info")


async def main_cli_logic():
    try:
        parser = argparse.ArgumentParser(description="Unified-AI-Project Command Line Interface")
        subparsers = parser.add_subparsers(dest="command", help="Available commands", required=False)

        query_parser = subparsers.add_parser("query", help="Send a query to the AI")
        query_parser.add_argument("query_text", type=str, help="The query text to send to the AI")
        query_parser.set_defaults(func=handle_query)

        publish_parser = subparsers.add_parser("publish_fact", help="Manually publish a fact via HSP")
        publish_parser.add_argument("fact_statement", type=str, help="The statement of the fact")
        publish_parser.add_argument("--confidence", type=float, default=0.9, help="Confidence score (0.0-1.0)")
        publish_parser.add_argument("--topic", type=str, help="HSP topic to publish to")
        # New: optional echo/wait flags
        publish_parser.add_argument("--echo", "--wait", dest="wait_echo", action="store_true", help="Wait for internal echo (hsp.internal.fact) and print it")
        publish_parser.add_argument("--echo-timeout", type=float, default=3.0, help="Seconds to wait for internal echo (default: 3.0)")
        # New: test-friendly flag to skip post-command sleep
        publish_parser.add_argument("--no-post-sleep", action="store_true", help="Skip post-command listening sleep (for tests)")
        publish_parser.set_defaults(func=handle_publish_fact)

        # 新增：模型管理子命令
        model_parser = subparsers.add_parser("model", help="Model management commands")
        model_subparsers = model_parser.add_subparsers(dest="model_command", help="Model management sub-commands")
        
        # 列出模型
        model_list_parser = model_subparsers.add_parser("list", help="List all available models")
        model_list_parser.set_defaults(func=handle_model_list)
        
        # 模型信息
        model_info_parser = model_subparsers.add_parser("info", help="Show model information")
        model_info_parser.add_argument("model_name", type=str, help="Model name")
        model_info_parser.set_defaults(func=handle_model_info)

        # 新增：训练管理子命令
        train_parser = subparsers.add_parser("train", help="Training management commands")
        train_subparsers = train_parser.add_subparsers(dest="train_command", help="Training management sub-commands")
        
        # 启动训练
        train_start_parser = train_subparsers.add_parser("start", help="Start model training")
        train_start_parser.add_argument("model_name", type=str, help="Model name to train")
        train_start_parser.add_argument("--preset", type=str, help="Training preset")
        train_start_parser.add_argument("--resume", action="store_true", help="Resume training from checkpoint")
        train_start_parser.set_defaults(func=handle_train_start)
        
        # 训练状态
        train_status_parser = train_subparsers.add_parser("status", help="Show training status")
        train_status_parser.set_defaults(func=handle_train_status)

        # 新增：数据管理子命令
        data_parser = subparsers.add_parser("data", help="Data management commands")
        data_subparsers = data_parser.add_subparsers(dest="data_command", help="Data management sub-commands")
        
        # 列出数据集
        data_list_parser = data_subparsers.add_parser("list", help="List all datasets")
        data_list_parser.set_defaults(func=handle_data_list)
        
        # 数据集信息
        data_info_parser = data_subparsers.add_parser("info", help="Show dataset information")
        data_info_parser.add_argument("dataset_name", type=str, help="Dataset name")
        data_info_parser.set_defaults(func=handle_data_info)

        print(f"--- Unified-AI-Project CLI (Instance AI ID will be: {cli_ai_id}) ---")
        error_handler.log_info(f"--- Unified-AI-Project CLI (Instance AI ID will be: {cli_ai_id}) ---")

        # Initialize core services
        # For CLI, we might want to use MockHAM and MockLLM by default.
        # core_services.initialize_services can be extended to accept flags for this.
        config = {
            "mcp": {
                "mqtt_broker_address": "localhost",
                "mqtt_broker_port": 1883,
                "enable_fallback": True,
                "fallback_config": {}
            }
        }
        await initialize_services(
            config=config,
            ai_id=cli_ai_id,
            use_mock_ham=True, # Use MockHAM for CLI
            
            operational_configs=DEFAULT_OPERATIONAL_CONFIGS
        )
        services = get_services()
        service_discovery_module = services.get("service_discovery")
        if service_discovery_module:
            service_discovery_module.start_cleanup_task()
        setup_cli_hsp_callbacks() # Register any CLI-specific callbacks if needed

        try:
            if len(sys.argv) <= 1 :
                 parser.print_help(sys.stderr)
                 # Keep CLI running to listen for HSP messages if no command is given
                 print("\nCLI: No command provided. Listening for HSP messages for 60 seconds (Ctrl+C to exit)...")
                 error_handler.log_info("CLI: No command provided. Listening for HSP messages for 60 seconds (Ctrl+C to exit)...")
                 await asyncio.sleep(60)
                 return # Exit the function gracefully

            args = parser.parse_args()
            if hasattr(args, 'func'):
                if asyncio.iscoroutinefunction(args.func):
                    await args.func(args)
                else:
                    args.func(args)
                # If it was not a query, keep alive briefly for HSP messages
                if args.command != "query":
                     print("\nCLI: Task complete. Listening for HSP messages for a few seconds (Ctrl+C to exit)...")
                     error_handler.log_info("CLI: Task complete. Listening for HSP messages for a few seconds (Ctrl+C to exit)...")
                     if not getattr(args, 'no_post_sleep', False):
                         await asyncio.sleep(10)

            else: # Should be caught by len(sys.argv) check if truly no command
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
            await shutdown_services() # From core_services
            print("CLI: Exiting.")
            error_handler.log_info("CLI: Exiting.")
    except Exception as e:
        error_handler.handle_exception(e, "main_cli_logic")


if __name__ == '__main__':
    asyncio.run(main_cli_logic())
if __name__ == '__main__':
    asyncio.run(main_cli_logic())if __name__ == '__main__':
    asyncio.run(main_cli_logic())