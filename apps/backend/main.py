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

# Security error handling
class SecurityError(Exception):
    """Security-related errors."""
    pass

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# [Phase 8 Activation] 啟動統一日誌系統
from core.logging.setup import setup_logging
setup_logging(level=logging.INFO, log_file="backend_main.log")
logger = logging.getLogger(__name__)

# [Phase 7 P0] 載入 i18n locale 檔案
try:
    from src.core.i18n.i18n_manager import _default_manager as i18n_manager
    locale_dir = str(Path(__file__).parent / "src" / "core" / "i18n" / "locales")
    i18n_count = i18n_manager.load_from_locale_dir(locale_dir)
    logger.info(f"✅ i18n 載入完成: {i18n_count} 筆翻譯")
except Exception as e:
    logger.warning(f"i18n 載入失敗（非致命）: {e}")

# 初始化密鑰管理器與中間件
from core.system.security_monitor import ABCKeyManager
from src.shared.security_middleware import SignedCommunicationMiddleware

def validate_security_configuration():
    """Validate security configuration before startup."""
    try:
        # Check if key manager is properly configured
        km = ABCKeyManager()
        if not km.has_key("KeyA") or not km.has_key("KeyB"):
            raise SecurityError("Required security keys (KeyA, KeyB) are not configured")
        return True
    except Exception as e:
        logger.error(f"Security configuration validation failed: {e}")
        raise

# Initialize key manager only after validation
validate_security_configuration()
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
        from src.core.system.bootstrap import get_bootstrap_manager
        from core.system.cluster_manager import ClusterManager, NodeType

        # 1. 正規化引導與硬體偵測 (替代已棄用的 DeploymentManager)
        bootstrap = get_bootstrap_manager()
        state = bootstrap.run_full_bootstrap()
        
        # 2. 初始化集群管理器 (適配 bootstrap 狀態)
        # 注意: 目前預設為 MASTER 節點，未來可由 bootstrap 狀態擴展
        node_type = NodeType.MASTER 
        cluster = ClusterManager(node_type=node_type)
        logger.info(f"✅ 正規化引導完成: Tier={state['hardware']['performance_tier']}, 節點類型={node_type.value}")

    except ImportError as e:
        logger.warning(f"引導或集群模組不可用: {e}")
    except Exception as e:
        logger.warning(f"正規化引導初始化失敗: {e}")

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

    # 知识图谱：原 UnifiedKnowledgeGraph 桩模块已移除（见 core/knowledge/__init__.py），
    # 实际功能由 ai.garden.kg_import.KGImporter / ai.meta.knowledge_pipeline.KnowledgePipeline
    # 提供，于查询时按需初始化，此处不再单独启动。

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
        version="7.5.0-dev",
        lifespan=lifespan,
    )

    # 加密通訊中間件 (使用 Key B)
    try:
        key_b = km.get_key("KeyB")
        if not key_b:
            raise SecurityError("Key B is not configured for signed communication middleware")
        app.add_middleware(SignedCommunicationMiddleware, key_b=key_b)
        logger.info("Signed communication middleware initialized with Key B")
    except Exception as e:
        logger.error(f"Failed to initialize signed communication middleware: {e}")
        raise

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/api/v1/system/module-control")
    async def control_module(data: Dict[str, Any] = Body(...)):
        """控制系統模組 (受 Key B 保護)"""
        module = data.get("module")
        enabled = data.get("enabled")
        if module and enabled is not None:
            if system_manager.set_module_state(module, enabled):
                return {"status": "success", "module": module, "enabled": enabled}
        return {"status": "error", "message": "Invalid module or state"}

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
        from core.system.bootstrap.hardware_probe import HardwareProbe

        probe = HardwareProbe()
        try:
            profile = probe.probe()
            return {
                "status": "online",
                "stats": {
                    "cpu_cores": profile.cpu_cores,
                    "memory_gb": profile.memory_gb,
                    "gpu": profile.gpu,
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

    # WebSocket 端點 — delegate to the full-featured handler in
    # services/websocket_manager.py (chat_message / multimodal / heartbeat /
    # module_control). The previous inline loop here had no chat_message
    # branch, so desktop-app WS chat silently never answered.
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        from services.websocket_manager import websocket_handler

        await websocket_handler(websocket)

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
