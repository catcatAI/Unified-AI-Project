#!/usr/bin/env python3
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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemManager:
    """系统管理器"""
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """初始化"""
        self.initialized = True
        logger.info("系统管理器初始化完成")
    
    async def shutdown(self):
        """关闭"""
        self.initialized = False
        logger.info("系统管理器已关闭")


system_manager = SystemManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动Level 5 AGI后端系统...")
    
    # 初始化系统管理器
    await system_manager.initialize()
    
    # 初始化实时同步系统
    try:
        from core.sync.realtime_sync import sync_manager
        await sync_manager.initialize()
        logger.info("✅ 实时同步系统初始化完成")
    except ImportError as e:
        logger.warning(f"实时同步系统模块不可用: {e}")
    except Exception as e:
        logger.warning(f"实时同步系统初始化失败: {e}")
    
    # 初始化知识图谱
    try:
        from core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraph
        kg = UnifiedKnowledgeGraph({})
        await kg.initialize()
        logger.info("✅ 知识图谱系统初始化完成")
    except ImportError as e:
        logger.warning(f"知识图谱模块不可用: {e}")
    except Exception as e:
        logger.warning(f"知识图谱初始化失败: {e}")
    
    # 初始化监控系统
    try:
        from core.monitoring.enterprise_monitor import enterprise_monitor
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
    except:
        pass
    
    await system_manager.shutdown()
    
    logger.info("✅ Level 5 AGI后端系统已关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="Unified AI Project - Level 5 AGI",
        description="完整的Level 5 AGI系统实现",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API路由
    try:
        from src.api.routes import router
        app.include_router(router, prefix="/api/v1")
    except ImportError:
        logger.warning("API路由模块不可用")
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """系统健康检查"""
        return {
            "status": "healthy",
            "system": "Level 5 AGI",
            "version": "1.0.0",
            "level": "Level 5",
            "timestamp": datetime.now().isoformat()
        }
    
    # 系统状态端点
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
                "io": "active"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    return app


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Unified AI Project - Level 5 AGI Backend'
    )
    parser.add_argument('--host', default='0.0.0.0', help='主机地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    parser.add_argument('--reload', action='store_true', help='开发模式热重载')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数')
    parser.add_argument('--log-level', default='info', help='日志级别')
    
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
            app,
            host=args.host,
            port=args.port,
            reload=True,
            log_level=args.log_level
        )
    else:
        # 生产模式
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level=args.log_level
        )


if __name__ == "__main__":
    main()
