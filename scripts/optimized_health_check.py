#!/usr/bin/env python3
"""
优化的系统健康检查脚本
利用性能优化模块提升检查效率
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
import psutil
import yaml
from pathlib import Path

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))

from optimization import get_performance_optimizer, cache_result

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedHealthMonitor:
    """优化的系统健康监控器"""
    
    def __init__(self, config_path: str = "configs/atlassian_config.yaml", 
                 system_config_path: str = "configs/system_config.yaml"):
        self.config_path = config_path
        self.system_config_path = system_config_path
        self.config = self._load_config(self.config_path)
        self.system_config = self._load_config(self.system_config_path)
        self.performance_optimizer = get_performance_optimizer()
        
        # 输出配置
        self.output_dir = Path("logs/health_monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_path = Path(__file__).parent.parent / "apps" / "backend" / path
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    
    @cache_result
    async def check_atlassian_service(self, service: str, primary_url: str, backup_urls: List[str]) -> Dict[str, Any]:
        """检查单个Atlassian服务的健康状态（带缓存）"""
        health_info = {
            'service': service,
            'primary_url': primary_url,
            'backup_urls': backup_urls,
            'status': 'unknown',
            'response_time': 0,
            'active_endpoint': None,
            'last_check': datetime.now().isoformat(),
            'errors': []
        }
        
        # 构建健康检查端点
        if service == 'confluence':
            health_endpoint = f"{primary_url}/rest/api/space"
        elif service == 'jira':
            health_endpoint = f"{primary_url}/rest/api/3/myself"
        elif service == 'bitbucket':
            health_endpoint = f"{primary_url}/user"
        else:
            health_endpoint = primary_url
        
        # 检查主端点
        urls_to_check = [primary_url] + backup_urls
        
        for url in urls_to_check:
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        health_endpoint.replace(primary_url, url),
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            health_info.update({
                                'status': 'healthy',
                                'response_time': response_time,
                                'active_endpoint': url
                            })
                            break
                        else:
                            health_info['errors'].append(f"{url}: HTTP {response.status}")
                            
            except Exception as e:
                health_info['errors'].append(f"{url}: {str(e)}")
                continue
        
        # 如果所有端点都失败
        if health_info['status'] == 'unknown':
            health_info['status'] = 'unhealthy'
        
        return health_info
    
    async def check_atlassian_services(self) -> Dict[str, Any]:
        """检查Atlassian服务健康状态（并行执行）"""
        services_health = {}
        
        atlassian_config = self.config.get('atlassian', {})
        
        # 创建检查任务
        tasks = []
        
        # 检查 Confluence
        confluence_config = atlassian_config.get('confluence', {})
        if confluence_config:
            task = self.check_atlassian_service(
                'confluence',
                confluence_config.get('base_url', ''),
                confluence_config.get('backup_urls', [])
            )
            tasks.append(('confluence', task))
        
        # 检查 Jira
        jira_config = atlassian_config.get('jira', {})
        if jira_config:
            task = self.check_atlassian_service(
                'jira',
                jira_config.get('base_url', ''),
                jira_config.get('backup_urls', [])
            )
            tasks.append(('jira', task))
        
        # 检查 Bitbucket
        bitbucket_config = atlassian_config.get('bitbucket', {})
        if bitbucket_config:
            task = self.check_atlassian_service(
                'bitbucket',
                bitbucket_config.get('base_url', ''),
                bitbucket_config.get('backup_urls', [])
            )
            tasks.append(('bitbucket', task))
        
        # 并行执行所有任务
        results = await self.performance_optimizer.run_parallel_tasks([task for _, task in tasks])
        
        # 处理结果
        for i, (service_name, _) in enumerate(tasks):
            if not isinstance(results[i], Exception):
                services_health[service_name] = results[i]
            else:
                services_health[service_name] = {
                    'service': service_name,
                    'status': 'error',
                    'errors': [str(results[i])]
                }
        
        return services_health
    
    @cache_result
    async def _check_api_server_health(self) -> Dict[str, Any]:
        """检查主API服务器的健康状态（带缓存）"""
        api_health_info = {
            'service': 'main_api_server',
            'status': 'unknown',
            'response_time': 0,
            'errors': []
        }
        
        try:
            api_host = self.system_config.get('operational_configs', {}).get('api_server', {}).get('host')
            api_port = self.system_config.get('operational_configs', {}).get('api_server', {}).get('port')
            
            if not api_host or not api_port:
                api_health_info['status'] = 'unconfigured'
                api_health_info['errors'].append("API server host or port not configured in system_config.yaml")
                return api_health_info

            api_endpoint = f"http://{api_host}:{api_port}/api/health"
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(api_endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        api_health_info.update({
                            'status': 'healthy',
                            'response_time': response_time
                        })
                    else:
                        api_health_info['status'] = 'unhealthy'
                        api_health_info['errors'].append(f"HTTP Status: {response.status}")
                        
        except asyncio.TimeoutError:
            api_health_info['status'] = 'timeout'
            api_health_info['errors'].append("API server request timed out.")
        except aiohttp.ClientError as e:
            api_health_info['status'] = 'unreachable'
            api_health_info['errors'].append(f"API server unreachable: {e}")
        except Exception as e:
            api_health_info['status'] = 'error'
            api_health_info['errors'].append(f"An unexpected error occurred: {e}")
            
        return api_health_info
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        # 利用性能优化器收集指标
        metrics = self.performance_optimizer.collect_metrics()
        
        return {
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'disk_io_read': metrics.disk_io_read,
            'disk_io_write': metrics.disk_io_write,
            'network_bytes_sent': metrics.network_bytes_sent,
            'network_bytes_recv': metrics.network_bytes_recv,
            'last_check': datetime.now().isoformat()
        }
    
    async def run_single_check(self):
        """执行单次健康检查"""
        logger.info("开始优化的健康检查...")
        
        start_time = time.time()
        
        # 并行收集健康数据
        tasks = [
            self.check_atlassian_services(),
            self._check_api_server_health(),
            self.check_system_resources()
        ]
        
        results = await self.performance_optimizer.run_parallel_tasks(tasks)
        
        # 处理结果
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'atlassian_services': results[0] if not isinstance(results[0], Exception) else {},
            'main_api_server': results[1] if not isinstance(results[1], Exception) else {},
            'system_resources': results[2] if not isinstance(results[2], Exception) else {}
        }
        
        end_time = time.time()
        logger.info(f"健康检查完成，耗时: {(end_time - start_time)*1000:.2f}ms")
        
        return health_data

async def main():
    """主函数"""
    monitor = OptimizedHealthMonitor()
    
    # 启动性能监控
    await start_performance_monitoring()
    
    try:
        # 执行健康检查
        health_data = await monitor.run_single_check()
        
        # 打印摘要
        print("\n" + "="*60)
        print(f"优化健康检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # API服务器状态
        api_server_health = health_data.get('main_api_server', {})
        print(f"主API服务器: {api_server_health.get('status', 'unknown')} ({api_server_health.get('response_time', 0):.0f}ms)")

        # Atlassian服务状态
        print("\nAtlassian服务:")
        atlassian_services = health_data.get('atlassian_services', {})
        for service, info in atlassian_services.items():
            status = info.get('status', 'unknown')
            response_time = info.get('response_time', 0)
            print(f"  {service.capitalize()}: {status} ({response_time:.0f}ms)")
        
        # 系统资源
        system_resources = health_data.get('system_resources', {})
        print(f"\n系统资源:")
        print(f"  CPU: {system_resources.get('cpu_percent', 0):.1f}%")
        print(f"  内存: {system_resources.get('memory_percent', 0):.1f}%")
        
        print("="*60)
        
    finally:
        # 停止性能监控
        await stop_performance_monitoring()

if __name__ == '__main__':
    asyncio.run(main())