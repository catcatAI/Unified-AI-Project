"""Core Service Manager Demo - 核心服务管理器演示

This module demonstrates the usage of the CoreServiceManager.

此模块演示核心服务管理器的使用方法。
"""

import asyncio
import logging
from apps.backend.src.core.managers.core_service_manager import (
    CoreServiceManager, 
    ServiceConfig, 
    ServiceStatus, 
    ServiceHealth
)
from apps.backend.src.core.managers.service_monitor import ServiceMonitor


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("Starting Core Service Manager Demo")
    
    # 创建核心服务管理器
    manager = CoreServiceManager()
    
    # 创建服务监控器
    monitor = ServiceMonitor(manager, "service_demo.log")
    
    # 启动监控
    async with monitor:
        # 注册服务配置
        # 1. 模拟LLM服务
        llm_config = ServiceConfig(
            name="llm_service",
            module_path="core_services",
            class_name="MultiLLMService",
            dependencies=[],
            lazy_load=True,
            auto_restart=True,
            health_check_interval=30.0,
            config={}
        )
        manager.register_service(llm_config)
        
        # 2. 模拟HAM内存管理器
        ham_config = ServiceConfig(
            name="ham_manager",
            module_path="core_services",
            class_name="HAMMemoryManager",
            dependencies=[],
            lazy_load=True,
            auto_restart=True,
            health_check_interval=60.0,
            config={}
        )
        manager.register_service(ham_config)
        
        # 3. 模拟HSP连接器
        hsp_config = ServiceConfig(
            name="hsp_connector",
            module_path="core_services",
            class_name="HSPConnector",
            dependencies=[],
            lazy_load=True,
            auto_restart=True,
            health_check_interval=15.0,
            config={
                "ai_id": "did:hsp:test_ai_001",
                "broker_address": "localhost",
                "broker_port": 1883
            }
        )
        manager.register_service(hsp_config)
        
        # 4. 模拟对话管理器（依赖LLM服务和HSP连接器）
        dialogue_config = ServiceConfig(
            name="dialogue_manager",
            module_path="core_services",
            class_name="DialogueManager",
            dependencies=["llm_service", "hsp_connector"],
            lazy_load=True,
            auto_restart=True,
            health_check_interval=30.0,
            config={}
        )
        manager.register_service(dialogue_config)
        
        # 5. 模拟学习管理器（依赖多个服务）
        learning_config = ServiceConfig(
            name="learning_manager",
            module_path="core_services",
            class_name="LearningManager",
            dependencies=["llm_service", "ham_manager", "hsp_connector"],
            lazy_load=True,
            auto_restart=True,
            health_check_interval=60.0,
            config={}
        )
        manager.register_service(learning_config)
        
        logger.info("Services registered")
        
        # 演示懒加载
        logger.info("=== Demonstrating Lazy Loading ===")
        
        # 加载单个服务
        logger.info("Loading LLM service...")
        success = await manager.load_service("llm_service")
        logger.info(f"LLM service load result: {success}")
        
        # 检查状态
        llm_status = manager.get_service_status("llm_service")
        logger.info(f"LLM service status: {llm_status}")
        
        # 尝试加载依赖服务
        logger.info("Loading dialogue manager (should fail due to missing dependencies)...")
        success = await manager.load_service("dialogue_manager")
        logger.info(f"Dialogue manager load result: {success}")
        
        # 加载依赖服务
        logger.info("Loading HSP connector...")
        success = await manager.load_service("hsp_connector")
        logger.info(f"HSP connector load result: {success}")
        
        # 现在再尝试加载对话管理器
        logger.info("Loading dialogue manager again (should succeed now)...")
        success = await manager.load_service("dialogue_manager")
        logger.info(f"Dialogue manager load result: {success}")
        
        # 检查所有服务状态
        status = manager.get_all_services_status()
        logger.info(f"Service status: {status}")
        
        # 演示服务重启
        logger.info("=== Demonstrating Service Restart ===")
        success = await manager.restart_service("llm_service")
        logger.info(f"LLM service restart result: {success}")
        
        # 演示批量加载
        logger.info("=== Demonstrating Batch Loading ===")
        
        # 卸载所有服务
        for service_name in ["llm_service", "hsp_connector", "dialogue_manager"]:
            await manager.unload_service(service_name, force=True)
        
        # 批量加载服务（包括依赖）
        logger.info("Batch loading services...")
        results = await manager.load_services(["dialogue_manager", "learning_manager"])
        logger.info(f"Batch load results: {results}")
        
        # 检查状态
        status = manager.get_all_services_status()
        logger.info(f"Service status after batch load: {status}")
        
        # 等待一段时间以观察健康检查
        logger.info("Waiting for health checks...")
        await asyncio.sleep(20)
        
        # 获取监控报告
        report = monitor.get_service_report()
        logger.info(f"Service report: {report}")
        
        logger.info("Demo completed successfully")


if __name__ == "__main__":
    asyncio.run(main())