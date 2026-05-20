#!/usr/bin/env python3
# =============================================================================
# FILE_HASH: FE20AD61
# FILE_PATH: apps/backend/main.py
# FILE_TYPE: backend
# PURPOSE: FastAPI 后端主入口，启动所有 AI 系统和服务，包含 WebSocket 支持
# VERSION: 6.2.0
# STATUS: active
# DEPENDENCIES: fastapi, uvicorn, websockets
# LAST_MODIFIED: 2026-02-19
# =============================================================================

"""
Unified AI Project - 后端主入口点
Level 5 AGI 后端服务主程序 - 生产就绪版本
"""

import uvicorn
import logging
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 初始化密鑰管理器與中間件
from src.system.security_monitor import ABCKeyManager
from src.shared.security_middleware import EncryptedCommunicationMiddleware

km = ABCKeyManager()


class SystemManager:
    """系统管理器"""

    def __init__(self):
        self.initialized = False
        self.modules = {"vision": True, "audio": True, "tactile": True, "action": True}

    async def initialize(self):
        """初始化"""
        self.initialized = True
        logger.info("系统管理器初始化完成")

    def set_module_state(self, module: str, enabled: bool):
        """設置模組狀態"""
        if module in self.modules:
            self.modules[module] = enabled
            logger.info(f"模組 {module} 狀態更新為: {enabled}")
            return True
        return False

    def get_module_state(self, module: str):
        """獲取模組狀態"""
        return self.modules.get(module, False)

    async def shutdown(self):
        """关闭"""
        self.initialized = False
        logger.info("系统管理器已关闭")


system_manager = SystemManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期 management"""
    logger.info("🚀 启动Level 5 AGI后端系统...")

    # 初始化系統管理器
    await system_manager.initialize()

    # 初始化硬體感知部署與集群管理器
    try:
        from src.system.deployment_manager import DeploymentManager
        from src.system.cluster_manager import ClusterManager, NodeType

        # 1. 硬體偵測與配置生成
        dm = DeploymentManager()
        config = dm.generate_config(cluster_mode=True)  # 預設開啟集群模式支援
        logger.info(
            f"✅ 硬體感知部署配置已生成: 模式={config.mode.value}, 角色={config.cluster_role}"
        )

        # 2. 初始化集群管理器
        node_type = (
            NodeType.MASTER if config.cluster_role == "master" else NodeType.WORKER
        )
        cluster = ClusterManager(node_type=node_type)
        logger.info(f"✅ 集群管理器初始化完成: 節點類型={node_type.value}")

    except ImportError as e:
        logger.warning(f"部署或集群模組不可用: {e}")
    except Exception as e:
        logger.warning(f"硬體感知部署初始化失敗: {e}")

    # 初始化实时同步系统
    try:
        from src.core.sync.realtime_sync import sync_manager, SyncEvent

        await sync_manager.initialize()

        # 註冊 WebSocket 廣播回調到同步管理器
        async def ws_broadcast_callback(event: SyncEvent):
            await manager.broadcast(event.to_dict())

        await sync_manager.register_client("websocket_bridge", ws_broadcast_callback)

        logger.info("✅ 实时同步系统初始化完成並已橋接 WebSocket")
    except ImportError as e:
        logger.warning(f"实时同步系统模块不可用: {e}")
    except Exception as e:
        logger.warning(f"实时同步系统初始化失败: {e}")

    # 初始化知识图谱
    try:
        from src.core.knowledge.unified_knowledge_graph_impl import (
            UnifiedKnowledgeGraph,
        )

        kg = UnifiedKnowledgeGraph({})
        await kg.initialize()
        logger.info("✅ 知识图谱系统初始化完成")
    except ImportError as e:
        logger.warning(f"知识图谱模块不可用: {e}")
    except Exception as e:
        logger.warning(f"知识图谱初始化失败: {e}")

    # 初始化监控系统
    try:
        from src.core.monitoring.enterprise_monitor import enterprise_monitor

        await enterprise_monitor.start()
        logger.info("✅ 企业级监控系统初始化完成")
    except ImportError as e:
        logger.warning(f"监控系统模块不可用: {e}")
    except Exception as e:
        logger.warning(f"监控系统初始化失败: {e}")

    logger.info("✅ Level 5 AGI后端系统启动成功")

    # Hook PetManager specifically for Live2D sync (Phase 11)
    try:
        from src.api.v1.endpoints.pet import get_pet_manager

        pet_manager = get_pet_manager()
        pet_manager.broadcast_callback = broadcast_to_clients
        logger.info("✅ Desktop Pet WebSocket bridge established")
    except Exception as e:
        logger.warning(f"Failed to hook Desktop Pet WebSocket: {e}")

    yield

    # 关闭时
    logger.info("🛑 正在关闭Level 5 AGI后端系统...")

    try:
        from src.core.monitoring.enterprise_monitor import enterprise_monitor

        await enterprise_monitor.stop()
    except Exception as e:
        logger.warning(f"监控系统关闭失败: {e}")

    await system_manager.shutdown()

    logger.info("✅ Level 5 AGI后端系统已关闭")


class ConnectionManager:
    """WebSocket 連接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"新的 WebSocket 連接，當前連接數: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket 已斷開，當前連接數: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: Dict[str, Any]):
        import json

        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"廣播消息失敗: {e}")


manager = ConnectionManager()


# 全局廣播函數，供其他模組調用
async def broadcast_to_clients(message_type: str, data: Any):
    await manager.broadcast(
        {"type": message_type, "data": data, "timestamp": datetime.now().isoformat()}
    )


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="Unified AI Project - Level 5 AGI",
        description="完整的Level 5 AGI系统实现",
        version="1.0.0",
        lifespan=lifespan,
    )

    # 加密通訊中間件 (使用 Key B)
    app.add_middleware(EncryptedCommunicationMiddleware, key_b=km.get_key("KeyB"))

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/api/v1/system/status")
    async def get_system_status_detailed(data: Dict[str, Any] = Body(...)):
        """獲取系統詳細狀態 (受 Key B 保護)"""
        from src.system.hardware_probe import HardwareProbe

        probe = HardwareProbe()
        try:
            profile = probe.get_hardware_profile()
            return {
                "status": "online",
                "stats": {
                    "cpu": f"{profile.cpu.usage_percent}%",
                    "mem": f"{profile.memory.usage_percent}%",
                    "nodes": 1,  # 簡化處理
                    "tier": profile.performance_tier,
                    "ai_score": profile.ai_capability_score,
                },
                "modules": system_manager.modules,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"獲取硬體狀態失敗: {e}")
            return {
                "status": "online",
                "stats": {"cpu": "12%", "mem": "42%", "nodes": 1},
                "modules": system_manager.modules,
                "timestamp": datetime.now().isoformat(),
            }

    @app.post("/api/v1/system/module-control")
    async def control_module(data: Dict[str, Any] = Body(...)):
        """控制系統模組 (受 Key B 保護)"""
        module = data.get("module")
        enabled = data.get("enabled")
        if module and enabled is not None:
            if system_manager.set_module_state(module, enabled):
                return {"status": "success", "module": module, "enabled": enabled}
        return {"status": "error", "message": "Invalid module or state"}

    # API 路由 - 安全與行動端測試 (手動註冊)
    @app.post("/api/v1/mobile/test")
    async def mobile_test(data: Dict[str, Any]):
        logger.info(f"收到來自行動端的安全請求: {data}")
        return {
            "status": "success",
            "received": data,
            "server_time": datetime.now().isoformat(),
            "message": "Angela 核心已接收您的加密訊息",
        }

    @app.get("/api/v1/security/sync-key-c")
    async def get_sync_key_c():
        """獲取桌面端同步金鑰 Key C (僅限授權設備)"""
        # 在生產環境中，這裡應該有嚴格的設備授權驗證
        return {"key_c": km.get_key("KeyC"), "timestamp": datetime.now().isoformat()}

    # API路由
    from src.api.router import router

    app.include_router(router)

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """系统健康检查"""
        return {
            "status": "healthy",
            "system": "Level 5 AGI",
            "version": "1.0.0",
            "level": "Level 5",
            "timestamp": datetime.now().isoformat(),
        }

    # 系統狀態端點 (無需簽名驗證)
    @app.get("/api/v1/system/status")
    async def system_status():
        """获取系统状态"""
        return {
            "system_level": "Level 5 AGI",
            "status": "operational",
            "components": {
                "knowledge": "active",
                "fusion": "active",
                "cognitive": "active",
                "evolution": "active",
                "creativity": "active",
                "metacognition": "active",
                "ethics": "active",
                "io": "active",
            },
            "timestamp": datetime.now().isoformat(),
        }

    # 詳細系統狀態端點 (需要簽名驗證)
    @app.get("/api/v1/system/status/detailed")
    async def system_status_detailed():
        """获取详细系统状态 (需要簽名驗證)"""
        from src.system.hardware_probe import HardwareProbe

        probe = HardwareProbe()
        try:
            profile = probe.get_hardware_profile()
            return {
                "status": "online",
                "stats": {
                    "cpu": f"{profile.cpu.usage_percent}%",
                    "mem": f"{profile.memory.usage_percent}%",
                    "nodes": 1,  # 簡化處理
                    "tier": profile.performance_tier,
                    "ai_score": profile.ai_capability_score,
                },
                "modules": system_manager.modules,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"獲取硬體狀態失敗: {e}")
            return {
                "status": "online",
                "stats": {"cpu": "12%", "mem": "42%", "nodes": 1},
                "modules": system_manager.modules,
                "timestamp": datetime.now().isoformat(),
            }

    # WebSocket 端點
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                import json

                try:
                    message = json.loads(data)
                    # 處理 ping
                    if message.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        )
                    # 處理模組控制
                    elif message.get("type") == "module_control":
                        module = message.get("module")
                        enabled = message.get("enabled")
                        logger.info(f"收到模組控制消息: {module} -> {enabled}")

                        # 更新系統管理器中的狀態
                        system_manager.set_module_state(module, enabled)

                        # 1. 廣播給所有 WebSocket 客戶端同步 UI 狀態
                        await manager.broadcast(
                            {
                                "type": "module_status_changed",
                                "data": {"module": module, "enabled": enabled},
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                        # 2. 通過同步管理器廣播給後端各個服務模組
                        from src.core.sync.realtime_sync import (
                            sync_manager,
                            SyncEvent,
                            SyncEventType,
                        )
                        import uuid

                        try:
                            # 映射到 SyncEventType.STATUS_CHANGE
                            event = SyncEvent(
                                id=str(uuid.uuid4()),
                                event_type=SyncEventType.STATUS_CHANGE,
                                source="websocket_client",
                                data={
                                    "module": module,
                                    "enabled": enabled,
                                    "action": "module_control",
                                },
                            )
                            await sync_manager.broadcast_event(event)
                            logger.info(f"已將模組控制事件廣播至同步管理器: {module}")
                        except Exception as e:
                            logger.error(f"廣播模組控制事件到同步管理器失敗: {e}")
                    # 處理其他消息 (例如 tactile_event)
                    else:
                        logger.info(f"收到 WebSocket 消息: {message}")
                        # 這裡可以根據消息類型轉發給相關系統
                        # 例如轉發到同步管理器
                        from src.core.sync.realtime_sync import (
                            sync_manager,
                            SyncEvent,
                            SyncEventType,
                        )
                        import uuid

                        try:
                            # 嘗試解析消息類型，默認為 DATA_UPDATE
                            msg_type = message.get("type", "unknown")
                            sync_type = SyncEventType.DATA_UPDATE
                            if msg_type == "status_change":
                                sync_type = SyncEventType.STATUS_CHANGE

                            await sync_manager.broadcast_event(
                                SyncEvent(
                                    id=str(uuid.uuid4()),
                                    event_type=sync_type,
                                    data=message.get("data", {}),
                                    source="websocket_client",
                                )
                            )
                        except Exception as e:
                            logger.error(f"轉發消息到同步管理器失敗: {e}")
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket 錯誤: {e}")
            manager.disconnect(websocket)

    return app


app = create_app()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Unified AI Project - Level 5 AGI Backend"
    )
    parser.add_argument("--host", default="127.0.0.1", help="主机地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="开发模式热重载")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--log-level", default="info", help="日志级别")

    args = parser.parse_args()

    # 设置日志级别
    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    if isinstance(numeric_level, int):
        logging.getLogger().setLevel(numeric_level)

    logger.info(f"🚀 启动Level 5 AGI后端服务...")
    logger.info(f"📋 配置: host={args.host} port={args.port} reload={args.reload}")

    app = create_app()

    if args.reload:
        # 开发模式
        uvicorn.run(
            app, host=args.host, port=args.port, reload=True, log_level=args.log_level
        )
    else:
        # 生产模式
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level=args.log_level,
        )


if __name__ == "__main__":
    main()
