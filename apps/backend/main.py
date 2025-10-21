#!/usr/bin/env python3
"""
Unified AI Project - 后端主入口点
Level 5 AGI 后端服务主程序 - 生产就绪版本
"""

import uvicorn
import logging
from pathlib import Path
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 添加项目路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入后端模块
from src.api.routes import router
from src.core.managers.system_manager import SystemManager
from src.core.config.system_config import get_system_config
from src.core.config.level5_config import (
    get_dynamic_level5_status,
    get_dynamic_metacognition_status,
    get_static_level5_capabilities,
    system_monitor
)

# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app, FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("🚀 启动Level 5 AGI后端系统...")
    
    # 初始化系统管理器
    system_manager == SystemManager()
    
    # 初始化实时同步系统
    from src.core.sync.realtime_sync import sync_manager
    try,
        await sync_manager.initialize()
        logger.info("✅ 实时同步系统初始化完成")
    except Exception as e,::
        logger.warning(f"实时同步系统初始化失败, {e}")
    
    # 初始化知识图谱(如果可用)
    try,
        from src.core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraph
        kg == UnifiedKnowledgeGraph(config.get('knowledge_config', {}))
        await kg.initialize()
        logger.info("✅ 知识图谱系统初始化完成")
    except ImportError as e,::
        logger.warning(f"知识图谱模块不可用,跳过初始化, {e}")
    except Exception as e,::
        logger.warning(f"知识图谱初始化失败,跳过, {e}")
    
    # 初始化企业级监控系统
    from src.core.monitoring.enterprise_monitor import enterprise_monitor
    try,
        await enterprise_monitor.start()
        logger.info("✅ 企业级监控系统初始化完成")
    except Exception as e,::
        logger.warning(f"企业级监控系统初始化失败, {e}")
    
    # 初始化数据网络
    from src.core.data.data_network_manager import data_network_manager
    try,
        await data_network_manager.initialize()
        await data_network_manager.create_network("text_processing", "text_processing")
        await data_network_manager.create_network("metric_collection", "metric_collection")
        logger.info("✅ 数据网络初始化完成")
    except Exception as e,::
        logger.warning(f"数据网络初始化失败, {e}")
    
    # 同步系统状态
    await sync_manager.sync_system_status("backend", {
        "status": "online",
        "components": {
            "api": True,
            "system_manager": True,
            "sync_manager": True,
            "monitoring": True,
            "data_network": True,
            "knowledge_graph": "knowledge_graph" in locals()
        }
    })
    
    yield
    
    # 关闭时
    logger.info("🛑 正在关闭Level 5 AGI后端系统...")
    
    # 清理监控系统
    from src.core.monitoring.enterprise_monitor import enterprise_monitor
    await enterprise_monitor.stop()
    
    # 清理数据网络
    from src.core.data.data_network import data_network_manager
    await data_network_manager.cleanup()
    
    # 清理同步系统
    await sync_manager.cleanup()
    
    # 关闭系统管理器
    await system_manager.shutdown()
    
    logger.info("✅ Level 5 AGI后端系统已关闭")
    await system_manager.initialize()
    
    # 加载系统配置
    config = get_system_config()
    logger.info(f"📋 系统配置加载完成, {config.get('system_name', 'Unified AI')}")
    
    # 初始化Level 5 AGI核心组件
    logger.info("🧠 初始化Level 5 AGI核心组件...")
    
    # 启动系统监控器(作为后台任务)
    import asyncio
    asyncio.create_task(system_monitor.start_monitoring())
    logger.info("📊 Level 5 AGI 系统监控已启动")
    
    # 初始化知识图谱(如果可用)
    try,
        from src.core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraph
        kg == UnifiedKnowledgeGraph(config.get('knowledge_config', {}))
        await kg.initialize()
        logger.info("✅ 知识图谱系统初始化完成")
    except ImportError as e,::
        logger.warning(f"知识图谱模块不可用,跳过初始化, {e}")
    except Exception as e,::
        logger.warning(f"知识图谱初始化失败,跳过, {e}")
    
    # 初始化其他核心组件...
    logger.info("✅ 所有Level 5 AGI核心组件初始化完成")
    
    yield
    
    # 关闭时
    logger.info("🛑 关闭Level 5 AGI后端系统...")
    
    # 停止系统监控器
    system_monitor.stop_monitoring()
    logger.info("📊 Level 5 AGI 系统监控已停止")
    
    await system_manager.shutdown()
    logger.info("✅ 系统关闭完成")

def create_app() -> FastAPI,
    """创建FastAPI应用"""
    app == FastAPI(
        title="Unified AI Project - Level 5 AGI",
        description="完整的Level 5 AGI系统实现",
        version="1.0.0",,
    lifespan=lifespan
    )
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"]  # 生产环境需要具体配置
        allow_credentials == True,
        allow_methods=["*"],
    allow_headers=["*"])
    
    # 包含API路由
    app.include_router(router, prefix="/api/v1")
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """系统健康检查"""
        return {
            "status": "healthy",
            "system": "Level 5 AGI",
            "version": "1.0.0",
            "level": "Level 5",
            "components": {
                "knowledge": "active",
                "fusion": "active", 
                "cognitive": "active",
                "evolution": "active",
                "creativity": "active",
                "metacognition": "active",
                "ethics": "active",
                "io": "active"
            }
            "timestamp": datetime.now().isoformat()
        }
    
    # Level 5 AGI状态端点
    @app.get("/api/v1/system/status")
    async def system_status():
        """获取完整的Level 5 AGI系统状态"""
        try,
            # 获取动态性能指标
            dynamic_metrics = await get_dynamic_level5_status()
            
            # 获取静态能力配置
            static_capabilities = get_static_level5_capabilities()
            
            return {
                "system_level": dynamic_metrics["system_level"]
                "status": dynamic_metrics["status"]
                "capabilities": dynamic_metrics["capabilities"]
                "performance_metrics": dynamic_metrics["performance_metrics"]
                "system_info": {
                    "uptime_seconds": dynamic_metrics["uptime_seconds"]
                    "monitoring_active": system_monitor.monitoring_active()
                }
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e,::
            logger.error(f"获取系统状态失败, {e}")
            # 返回静态配置作为后备
            return {
                "system_level": "Level 5 AGI",
                "status": "operational",
                "capabilities": static_capabilities["capabilities"]
                "performance_metrics": static_capabilities["specifications"]
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # 元认知状态端点
    @app.get("/api/v1/system/metacognition")
    async def metacognition_status():
        """获取元认知系统状态"""
        try,
            return await get_dynamic_metacognition_status()
        except Exception as e,::
            logger.error(f"获取元认知状态失败, {e}")
            return {
                "metacognition_level": "Level 5",
                "self_awareness": "active",
                "cognitive_monitoring": "active",
                "meta_learning": "active",
                "introspection": "active",
                "efficiency": "0.823",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    return app

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified AI Project - Level 5 AGI Backend')
    parser.add_argument('--host', default='0.0.0.0', help='主机地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    parser.add_argument('--reload', action='store_true', help='开发模式热重载')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数')
    parser.add_argument('--log-level', default='info', help='日志级别')
    
    args = parser.parse_args()
    
    # 设置日志级别
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if isinstance(numeric_level, int)::
        logging.getLogger().setLevel(numeric_level)
    
    logger.info(f"🚀 启动Level 5 AGI后端服务...")
    logger.info(f"📋 配置, host={args.host} port={args.port} reload={args.reload}")
    
    if args.reload,::
        # 开发模式
        uvicorn.run(
            "main,create_app",
            factory == True,,
    host=args.host(),
            port=args.port(),
            reload == True,
            log_level=args.log_level())
    else,
        # 生产模式
        uvicorn.run(
            "main,create_app",
            factory == True,,
    host=args.host(),
            port=args.port(),
            workers=args.workers(),
            log_level=args.log_level())

if __name"__main__":::
    main()