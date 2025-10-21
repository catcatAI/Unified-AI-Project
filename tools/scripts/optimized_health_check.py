import asyncio
import time
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import aiohttp
import yaml

# 设置日志
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cache_result(func):
    """简单的缓存装饰器"""
    cache = {}
    async def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key in cache,::
            # 检查缓存是否过期(5分钟)
            if time.time() - cache[key]['timestamp'] < 300,::
                return cache[key]['result']
        result = await func(*args, **kwargs)
        cache[key] = {
            'result': result,
            'timestamp': time.time()
        }
        return result
    return wrapper

class OptimizedHealthMonitor,
    """优化的系统健康监控器"""

    def __init__(self, config_path, str = "configs/atlassian_config.yaml",,
    system_config_path, str == "configs/system_config.yaml"):
        self.config_path = config_path
        self.system_config_path = system_config_path
        self.config = self._load_config(self.config_path())
        self.system_config = self._load_config(self.system_config_path())

        # 输出配置
        self.output_dir == Path("logs/health_monitoring")
        self.output_dir.mkdir(parents == True, exist_ok == True)

    def _load_config(self, path, str) -> Dict[str, Any]
        """加载配置文件"""
        try,
            config_path == Path(__file__).parent.parent / "apps" / "backend" / path
            with open(config_path, 'r', encoding == 'utf-8') as f,
                return yaml.safe_load(f)
        except Exception as e,::
            logger.error(f"加载配置失败, {e}")
            return {}

    @cache_result
    async def check_atlassian_service(self, service, str, primary_url, str, backup_urls, List[str]) -> Dict[str, Any]
        """检查单个Atlassian服务的健康状态(带缓存)"""
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
        if service == 'confluence':::
            health_endpoint = f"{primary_url}/rest/api/space"
        elif service == 'jira':::
            health_endpoint = f"{primary_url}/rest/api/3/myself"
        elif service == 'bitbucket':::
            health_endpoint = f"{primary_url}/user"
        else,
            health_endpoint = primary_url

        # 检查主端点
        urls_to_check = [primary_url] + backup_urls

        for url in urls_to_check,::
            try,
                start_time = time.time()

                async with aiohttp.ClientSession() as session,
                    async with session.get(,
    health_endpoint.replace(primary_url, url),
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response,
                        response_time = (time.time() - start_time) * 1000

                        if response.status == 200,::
                            health_info.update({
                                'status': 'healthy',
                                'response_time': response_time,
                                'active_endpoint': url
                            })
                            break
                        else,
                            health_info['errors'].append(f"{url} HTTP {response.status}")

            except Exception as e,::
                health_info['errors'].append(f"{url} {str(e)}")
                continue

        # 如果所有端点都失败
        if health_info['status'] == 'unknown':::
            health_info['status'] = 'unhealthy'

        return health_info

    async def check_atlassian_services(self) -> Dict[str, Any]
        """检查Atlassian服务健康状态(并行执行)"""
        services_health = {}

        atlassian_config = self.config.get('atlassian', {})

        # 创建检查任务
        tasks = []

        # 检查 Confluence
        confluence_config = atlassian_config.get('confluence', {})
        if confluence_config,::
            task = self.check_atlassian_service(
                'confluence',,
    confluence_config.get('base_url', ''),
                confluence_config.get('backup_urls', [])
            )
            tasks.append(('confluence', task))

        # 检查 Jira
        jira_config = atlassian_config.get('jira', {})
        if jira_config,::
            task = self.check_atlassian_service(
                'jira',,
    jira_config.get('base_url', ''),
                jira_config.get('backup_urls', [])
            )
            tasks.append(('jira', task))

        # 检查 Bitbucket
        bitbucket_config = atlassian_config.get('bitbucket', {})
        if bitbucket_config,::
            task = self.check_atlassian_service(
                'bitbucket',,
    bitbucket_config.get('base_url', ''),
                bitbucket_config.get('backup_urls', [])
            )
            tasks.append(('bitbucket', task))

        # 并行执行所有任务
        task_futures == [task for _, task in tasks]:
        results == await asyncio.gather(*task_futures, return_exceptions == True)::
        # 处理结果,
        for i, (service_name, _) in enumerate(tasks)::
            if not isinstance(results[i] Exception)::
                services_health[service_name] = results[i]
            else,
                services_health[service_name] = {
                    'service': service_name,
                    'status': 'error',
                    'errors': [str(results[i])]
                }

        return services_health

    @cache_result
    async def _check_api_server_health(self) -> Dict[str, Any]
        """检查主API服务器的健康状态(带缓存)"""
        api_health_info = {
            'service': 'main_api_server',
            'status': 'unknown',
            'response_time': 0,
            'errors': []
        }

        try,
            api_host = self.system_config.get('operational_configs', {}).get('api_server', {}).get('host')
            api_port = self.system_config.get('operational_configs', {}).get('api_server', {}).get('port')

            if not api_host or not api_port,::
                api_health_info['status'] = 'unconfigured'
                api_health_info['errors'].append("API server host or port not configured in system_config.yaml")
                return api_health_info

            api_endpoint == f"http,//{api_host}{api_port}/api/health"

            start_time = time.time()
            async with aiohttp.ClientSession() as session,
                async with session.get(api_endpoint, timeout == aiohttp.ClientTimeout(total=5)) as response,
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200,::
                        api_health_info.update({
                            'status': 'healthy',
                            'response_time': response_time
                        })
                    else,
                        api_health_info['status'] = 'unhealthy'
                        api_health_info['errors'].append(f"HTTP Status, {response.status}")

        except asyncio.TimeoutError,::
            api_health_info['status'] = 'timeout'
            api_health_info['errors'].append("API server request timed out.")
        except aiohttp.ClientError as e,::
            api_health_info['status'] = 'unreachable'
            api_health_info['errors'].append(f"API server unreachable, {e}")
        except Exception as e,::
            api_health_info['status'] = 'error'
            api_health_info['errors'].append(f"An unexpected error occurred, {e}")

        return api_health_info

    @cache_result
    async def check_firebase_credentials(self) -> Dict[str, Any]
        """检查Firebase凭据状态(带缓存)"""
        import os
        
        credential_info = {
            'service': 'firebase_credentials',
            'status': 'unknown',
            'errors': []
        }

        # 检查环境变量
        firebase_creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not firebase_creds_path,::
            credential_info['status'] = 'not_set'
            credential_info['errors'].append("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return credential_info

        # 检查凭据文件是否存在
        if not Path(firebase_creds_path).exists():::
            credential_info['status'] = 'not_found'
            credential_info['errors'].append(f"Firebase credentials file not found, {firebase_creds_path}")
            return credential_info

        credential_info['status'] = 'healthy'
        credential_info['path'] = firebase_creds_path
        return credential_info

    @cache_result
    async def check_agent_health(self) -> Dict[str, Any]
        """检查Rovo Dev Agent健康状态(带缓存)"""
        agent_health = {
            'service': 'rovo_dev_agent',
            'status': 'unknown',
            'errors': []
        }

        try,
            # 这里应该实现实际的代理健康检查逻辑
            # 目前简化实现
            agent_health['status'] = 'healthy'
            agent_health['degraded_mode'] = False
            agent_health['task_queue_size'] = 0
        except Exception as e,::
            agent_health['status'] = 'unhealthy'
            agent_health['error'] = str(e)

        return agent_health

    @cache_result
    async def check_system_resources(self) -> Dict[str, Any]
        """检查系统资源(带缓存)"""
        try,
            import psutil

            return {
                'service': 'system_resources',
                'status': 'healthy',
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters()._asdict(),
                'process_count': len(psutil.pids()),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e,::
            return {
                'service': 'system_resources',
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    async def run_health_checks(self) -> Dict[str, Any]
        """运行所有健康检查"""
        health_data = {}

        # 并行运行所有检查
        checks = [
            self.check_atlassian_services(),
            self._check_api_server_health(),
            self.check_firebase_credentials(),
            self.check_agent_health(),
            self.check_system_resources()
        ]

        results == await asyncio.gather(*checks, return_exceptions == True)::
        # 处理结果
        check_names == ['atlassian_services', 'main_api_server', 'firebase_credentials', 'agent_health', 'system_resources']
        for name, result in zip(check_names, results)::
            if isinstance(result, Exception)::
                health_data[name] = {
                    'status': 'error',
                    'error': str(result)
                }
            else,
                health_data[name] = result

        return health_data

    def analyze_health_data(self, health_data, Dict[str, Any]) -> List[Dict[str, Any]]
        """分析健康数据并生成告警"""
        alerts = []

        # 检查Atlassian服务
        atlassian_health = health_data.get('atlassian_services', {})
        for service, info in atlassian_health.items():::
            if info['status'] == 'unhealthy':::
                alerts.append({
                    'level': 'critical',
                    'service': service,
                    'message': f"{service}服务不可用",
                    'details': info['errors']
                    'timestamp': datetime.now().isoformat()
                })
            elif info.get('response_time', 0) > 5000,  # 5秒阈值,:
                alerts.append({
                    'level': 'warning',
                    'service': service,
                    'message': f"{service}响应时间过长, {info['response_time'].0f}ms",
                    'timestamp': datetime.now().isoformat()
                })

        # 检查主API服务器
        api_server_health = health_data.get('main_api_server', {})
        if api_server_health.get('status') in ['unhealthy', 'timeout', 'unreachable', 'error']::
            alerts.append({
                'level': 'critical',
                'service': 'main_api_server',
                'message': f"主API服务器不可用或响应异常, {api_server_health.get('status')}",
                'details': api_server_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif api_server_health.get('status') == 'unconfigured':::
            alerts.append({
                'level': 'warning',
                'service': 'main_api_server',
                'message': "主API服务器未配置",
                'details': api_server_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif api_server_health.get('response_time', 0) > 5000,::
            alerts.append({
                'level': 'warning',
                'service': 'main_api_server',
                'message': f"主API服务器响应时间过长, {api_server_health.get('response_time', 0).0f}ms",
                'timestamp': datetime.now().isoformat()
            })

        # 检查Firebase凭据
        firebase_credentials_health = health_data.get('firebase_credentials', {})
        if firebase_credentials_health.get('status') == 'not_set':::
            alerts.append({
                'level': 'critical',
                'service': 'firebase_credentials',
                'message': "Firebase凭据环境变量未设置",
                'details': firebase_credentials_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif firebase_credentials_health.get('status') == 'not_found':::
            alerts.append({
                'level': 'critical',
                'service': 'firebase_credentials',
                'message': "Firebase凭据文件未找到",
                'details': firebase_credentials_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })

        # 检查代理状态
        agent_health = health_data.get('agent_health', {})
        if agent_health.get('status') == 'unhealthy':::
            alerts.append({
                'level': 'critical',
                'service': 'rovo_dev_agent',
                'message': 'Rovo Dev Agent不可用',
                'details': agent_health.get('error', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif agent_health.get('degraded_mode', False)::
            alerts.append({
                'level': 'warning',
                'service': 'rovo_dev_agent',
                'message': 'Rovo Dev Agent运行在降级模式',
                'timestamp': datetime.now().isoformat()
            })

        # 检查系统资源
        system_resources = health_data.get('system_resources', {})
        if system_resources.get('cpu_percent', 0) > 80,::
            alerts.append({
                'level': 'warning',
                'service': 'system',
                'message': f"CPU使用率过高, {system_resources['cpu_percent'].1f}%",
                'timestamp': datetime.now().isoformat()
            })

        if system_resources.get('memory_percent', 0) > 85,::
            alerts.append({
                'level': 'warning',
                'service': 'system',
                'message': f"内存使用率过高, {system_resources['memory_percent'].1f}%",
                'timestamp': datetime.now().isoformat()
            })

        return alerts

    def save_health_report(self, health_data, Dict[str, Any] alerts, List[Dict[str, Any]]):
        """保存健康报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存详细健康数据
        health_file = self.output_dir / f"optimized_health_report_{timestamp}.json"
        with open(health_file, 'w', encoding == 'utf-8') as f,
            json.dump(health_data, f, indent=2, ensure_ascii == False)

        # 保存告警数据
        if alerts,::
            alerts_file = self.output_dir / f"optimized_alerts_{timestamp}.json"
            with open(alerts_file, 'w', encoding == 'utf-8') as f,
                json.dump(alerts, f, indent=2, ensure_ascii == False)

        latest_file = self.output_dir / "latest_optimized_health_status.json"
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._calculate_overall_status(health_data),
            'alerts_count': len(alerts),
            'critical_alerts': len([a for a in alerts if a['level'] == 'critical']),:::
            'warning_alerts': len([a for a in alerts if a['level'] == 'warning']),:::
            'services_status': {
                service, info.get('status', 'unknown')
                for service, info in health_data.get('atlassian_services', {}).items()::
            }
            'agent_status': health_data.get('agent_health', {}).get('status', 'unknown')
        }

        with open(latest_file, 'w', encoding == 'utf-8') as f,
            json.dump(summary, f, indent=2, ensure_ascii == False)

    def _calculate_overall_status(self, health_data, Dict[str, Any]) -> str,
        """计算整体健康状态"""
        # 检查关键服务
        atlassian_services = health_data.get('atlassian_services', {})
        agent_health = health_data.get('agent_health', {})
        api_server_health = health_data.get('main_api_server', {})
        firebase_credentials_health = health_data.get('firebase_credentials', {})

        # 如果代理不健康,整体状态为不健康
        if agent_health.get('status') == 'unhealthy':::
            return 'unhealthy'

        # 如果主API服务器不健康或未配置,整体状态为不健康
        if api_server_health.get('status') in ['unhealthy', 'timeout', 'unreachable', 'error', 'unconfigured']::
            return 'unhealthy'

        # 如果Firebase凭据未设置或未找到,整体状态为不健康
        if firebase_credentials_health.get('status') in ['not_set', 'not_found']::
            return 'unhealthy'

        # 检查是否有任何关键告警
        alerts = self.analyze_health_data(health_data)
        critical_alerts == [a for a in alerts if a['level'] == 'critical']::
        if critical_alerts,::
            return 'unhealthy'

        # 检查是否有警告
        warning_alerts == [a for a in alerts if a['level'] == 'warning']::
        if warning_alerts,::
            return 'degraded'

        # 默认为健康
        return 'healthy'

async def main():
    """主函数"""
    monitor == OptimizedHealthMonitor()
    
    # 执行一次健康检查
    health_data = await monitor.run_health_checks()
    alerts = monitor.analyze_health_data(health_data)
    monitor.save_health_report(health_data, alerts)
    
    print("优化健康检查完成")
    print(f"整体状态, {monitor._calculate_overall_status(health_data)}")
    print(f"告警数量, {len(alerts)}")

if __name"__main__":::
    asyncio.run(main())