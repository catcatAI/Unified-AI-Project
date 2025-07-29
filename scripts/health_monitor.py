#!/usr/bin/env python3
"""
系統健康監控腳本
監控 Rovo Dev Agents 和 Atlassian 集成的健康狀態
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import aiohttp
import argparse

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """系統健康監控器"""
    
    def __init__(self, config_path: str = "configs/atlassian_config.yaml", system_config_path: str = "configs/system_config.yaml"):
        self.config_path = config_path
        self.system_config_path = system_config_path
        self.config = self._load_config(self.config_path)
        self.system_config = self._load_config(self.system_config_path)
        self.health_data = {}
        self.alerts = []
        
        # 監控配置
        self.check_interval = 60  # 秒
        self.alert_thresholds = {
            'response_time': 5000,  # 5秒
            'error_rate': 0.1,      # 10%
            'queue_size': 100       # 100個任務
        }
        
        # 輸出配置
        self.output_dir = Path("logs/health_monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """加載配置文件"""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加載配置失敗: {e}")
            return {}
    
    async def check_atlassian_services(self) -> Dict[str, Any]:
        """檢查 Atlassian 服務健康狀態"""
        services_health = {}
        
        atlassian_config = self.config.get('atlassian', {})
        
        # 檢查 Confluence
        confluence_config = atlassian_config.get('confluence', {})
        if confluence_config:
            services_health['confluence'] = await self._check_service_health(
                'confluence',
                confluence_config.get('base_url', ''),
                confluence_config.get('backup_urls', [])
            )
        
        # 檢查 Jira
        jira_config = atlassian_config.get('jira', {})
        if jira_config:
            services_health['jira'] = await self._check_service_health(
                'jira',
                jira_config.get('base_url', ''),
                jira_config.get('backup_urls', [])
            )
        
        # 檢查 Bitbucket
        bitbucket_config = atlassian_config.get('bitbucket', {})
        if bitbucket_config:
            services_health['bitbucket'] = await self._check_service_health(
                'bitbucket',
                bitbucket_config.get('base_url', ''),
                bitbucket_config.get('backup_urls', [])
            )
        
        return services_health
    
    async def _check_service_health(self, service: str, primary_url: str, backup_urls: List[str]) -> Dict[str, Any]:
        """檢查單個服務的健康狀態"""
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
        
        # 構建健康檢查端點
        if service == 'confluence':
            health_endpoint = f"{primary_url}/rest/api/space"
        elif service == 'jira':
            health_endpoint = f"{primary_url}/rest/api/3/myself"
        elif service == 'bitbucket':
            health_endpoint = f"{primary_url}/user"
        else:
            health_endpoint = primary_url
        
        # 檢查主端點
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
        
        # 如果所有端點都失敗
        if health_info['status'] == 'unknown':
            health_info['status'] = 'unhealthy'
        
        return health_info
    
    return health_info
    
    async def _check_api_server_health(self) -> Dict[str, Any]:
        """檢查主 API 伺服器的健康狀態"""
        api_health_info = {
            'service': 'main_api_server',
            'status': 'unknown',
            'response_time': 0,
            'errors': []
        }
        
        try:
            api_host = self.system_config.get('system', {}).get('api_server', {}).get('host')
            api_port = self.system_config.get('system', {}).get('api_server', {}).get('port')
            
            if not api_host or not api_port:
                api_health_info['status'] = 'unconfigured'
                api_health_info['errors'].append("API server host or port not configured in system_config.yaml")
                return api_health_info

            api_endpoint = f"http://{api_host}:{api_port}/api/v1/health"
            
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
                        api_health_info['errors'].append(f"HTTP Status: {response.status}, Content: {await response.text()}")
                        
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
    
    async def check_agent_health(self) -> Dict[str, Any]:
        """檢查代理健康狀態"""
        agent_health = {
            'status': 'unknown',
            'is_active': False,
            'degraded_mode': False,
            'task_queue_size': 0,
            'active_tasks': 0,
            'metrics': {},
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # 嘗試連接代理狀態端點
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://localhost:8000/api/agent/status',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        agent_health.update(data)
                        agent_health['status'] = 'healthy'
                    else:
                        agent_health['status'] = 'unhealthy'
                        
        except Exception as e:
            agent_health['status'] = 'unhealthy'
            agent_health['error'] = str(e)
        
        return agent_health
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """檢查系統資源"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'process_count': len(psutil.pids()),
            'last_check': datetime.now().isoformat()
        }
    
    def analyze_health_data(self, health_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析健康數據並生成告警"""
        alerts = []
        
        # 檢查 Atlassian 服務
        atlassian_health = health_data.get('atlassian_services', {})
        for service, info in atlassian_health.items():
            if info['status'] == 'unhealthy':
                alerts.append({
                    'level': 'critical',
                    'service': service,
                    'message': f"{service} 服務不可用",
                    'details': info['errors'],
                    'timestamp': datetime.now().isoformat()
                })
            elif info['response_time'] > self.alert_thresholds['response_time']:
                alerts.append({
                    'level': 'warning',
                    'service': service,
                    'message': f"{service} 響應時間過長: {info['response_time']:.0f}ms",
                    'timestamp': datetime.now().isoformat()
                })
        
        # 檢查主 API 伺服器
        api_server_health = health_data.get('main_api_server', {})
        if api_server_health.get('status') in ['unhealthy', 'timeout', 'unreachable', 'error']:
            alerts.append({
                'level': 'critical',
                'service': 'main_api_server',
                'message': f"主 API 伺服器不可用或響應異常: {api_server_health.get('status')}",
                'details': api_server_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif api_server_health.get('status') == 'unconfigured':
            alerts.append({
                'level': 'warning',
                'service': 'main_api_server',
                'message': "主 API 伺服器未配置",
                'details': api_server_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif api_server_health.get('response_time', 0) > self.alert_thresholds['response_time']:
            alerts.append({
                'level': 'warning',
                'service': 'main_api_server',
                'message': f"主 API 伺服器響應時間過長: {api_server_health.get('response_time', 0):.0f}ms",
                'timestamp': datetime.now().isoformat()
            })

        # 檢查 Firebase 憑證
        firebase_credentials_health = health_data.get('firebase_credentials', {})
        if firebase_credentials_health.get('status') == 'not_set':
            alerts.append({
                'level': 'critical',
                'service': 'firebase_credentials',
                'message': "Firebase 憑證環境變數未設置",
                'details': firebase_credentials_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif firebase_credentials_health.get('status') == 'not_found':
            alerts.append({
                'level': 'critical',
                'service': 'firebase_credentials',
                'message': "Firebase 憑證檔案未找到",
                'details': firebase_credentials_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })

        # 檢查代理狀態
        agent_health = health_data.get('agent_health', {})
        if agent_health.get('status') == 'unhealthy':
            alerts.append({
                'level': 'critical',
                'service': 'rovo_dev_agent',
                'message': 'Rovo Dev Agent 不可用',
                'details': agent_health.get('error', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif agent_health.get('degraded_mode'):
            alerts.append({
                'level': 'warning',
                'service': 'rovo_dev_agent',
                'message': 'Rovo Dev Agent 運行在降級模式',
                'timestamp': datetime.now().isoformat()
            })
        
        # 檢查任務隊列
        queue_size = agent_health.get('task_queue_size', 0)
        if queue_size > self.alert_thresholds['queue_size']:
            alerts.append({
                'level': 'warning',
                'service': 'task_queue',
                'message': f'任務隊列積壓: {queue_size} 個任務',
                'timestamp': datetime.now().isoformat()
            })
        
        # 檢查系統資源
        system_resources = health_data.get('system_resources', {})
        if system_resources.get('cpu_percent', 0) > 80:
            alerts.append({
                'level': 'warning',
                'service': 'system',
                'message': f"CPU 使用率過高: {system_resources['cpu_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if system_resources.get('memory_percent', 0) > 85:
            alerts.append({
                'level': 'warning',
                'service': 'system',
                'message': f"內存使用率過高: {system_resources['memory_percent']:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def save_health_report(self, health_data: Dict[str, Any], alerts: List[Dict[str, Any]]):
        """保存健康報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存詳細健康數據
        health_file = self.output_dir / f"health_report_{timestamp}.json"
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2, ensure_ascii=False)
        
        # 保存告警數據
        if alerts:
            alerts_file = self.output_dir / f"alerts_{timestamp}.json"
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
        
        # 更新最新狀態文件
        latest_file = self.output_dir / "latest_health_status.json"
        summary = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._calculate_overall_status(health_data),
            'alerts_count': len(alerts),
            'critical_alerts': len([a for a in alerts if a['level'] == 'critical']),
            'warning_alerts': len([a for a in alerts if a['level'] == 'warning']),
            'services_status': {
                service: info.get('status', 'unknown')
                for service, info in health_data.get('atlassian_services', {}).items()
            },
            'agent_status': health_data.get('agent_health', {}).get('status', 'unknown')
        }
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> str:
        """計算整體健康狀態"""
        # 檢查關鍵服務
        atlassian_services = health_data.get('atlassian_services', {})
        agent_health = health_data.get('agent_health', {})
        api_server_health = health_data.get('main_api_server', {})
        firebase_credentials_health = health_data.get('firebase_credentials', {})

        # 如果代理不健康，整體狀態為不健康
        if agent_health.get('status') == 'unhealthy':
            return 'unhealthy'

        # 如果主 API 伺服器不健康或未配置，整體狀態為不健康
        if api_server_health.get('status') in ['unhealthy', 'timeout', 'unreachable', 'error', 'unconfigured']:
            return 'unhealthy'

        # 如果 Firebase 憑證未設置或未找到，整體狀態為不健康
        if firebase_credentials_health.get('status') in ['not_set', 'not_found']:
            return 'unhealthy'

        # 檢查 Atlassian 服務
        unhealthy_services = [
            service for service, info in atlassian_services.items()
            if info.get('status') == 'unhealthy'
        ]
        
        if len(unhealthy_services) > 0:
            return 'degraded' if len(unhealthy_services) < len(atlassian_services) else 'unhealthy'
        
        # 檢查是否有降級模式
        if agent_health.get('degraded_mode'):
            return 'degraded'
        
        return 'healthy'
    
    def print_health_summary(self, health_data: Dict[str, Any], alerts: List[Dict[str, Any]]):
        """打印健康狀態摘要"""
        print("\n" + "="*60)
        print(f"系統健康監控報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 整體狀態
        overall_status = self._calculate_overall_status(health_data)
        status_color = {
            'healthy': '\033[92m',    # 綠色
            'degraded': '\033[93m',   # 黃色
            'unhealthy': '\033[91m'   # 紅色
        }.get(overall_status, '\033[0m')
        
        print(f"整體狀態: {status_color}{overall_status.upper()}\033[0m")
        
        # 主 API 伺服器狀態
        api_server_health = health_data.get('main_api_server', {})
        print(f"\n主 API 伺服器: {api_server_health.get('status', 'unknown')} ({api_server_health.get('response_time', 0):.0f}ms)")

        # Firebase 憑證狀態
        firebase_credentials_health = health_data.get('firebase_credentials', {})
        print(f"Firebase 憑證: {firebase_credentials_health.get('status', 'unknown')}")

        # Atlassian 服務狀態
        print("\nAtlassian 服務:")
        atlassian_services = health_data.get('atlassian_services', {})
        for service, info in atlassian_services.items():
            status = info.get('status', 'unknown')
            response_time = info.get('response_time', 0)
            print(f"  {service.capitalize()}: {status} ({response_time:.0f}ms)")
        
        # 代理狀態
        agent_health = health_data.get('agent_health', {})
        print(f"\nRovo Dev Agent: {agent_health.get('status', 'unknown')}")
        if agent_health.get('degraded_mode'):
            print("  ⚠️  運行在降級模式")
        
        # 系統資源
        system_resources = health_data.get('system_resources', {})
        print(f"\n系統資源:")
        print(f"  CPU: {system_resources.get('cpu_percent', 0):.1f}%")
        print(f"  內存: {system_resources.get('memory_percent', 0):.1f}%")
        print(f"  磁盤: {system_resources.get('disk_percent', 0):.1f}%")
        
        # 告警
        if alerts:
            print(f"\n告警 ({len(alerts)}):")
            for alert in alerts:
                level_color = {
                    'critical': '\033[91m',  # 紅色
                    'warning': '\033[93m'    # 黃色
                }.get(alert['level'], '\033[0m')
                print(f"  {level_color}[{alert['level'].upper()}]\033[0m {alert['message']}")
        else:
            print("\n✅ 無告警")
        
        print("="*60)
    
    async def run_single_check(self):
        """執行單次健康檢查"""
        logger.info("開始健康檢查...")
        
        # 收集健康數據
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'atlassian_services': await self.check_atlassian_services(),
            'main_api_server': await self._check_api_server_health(),
            'firebase_credentials': await self._check_firebase_credentials_existence(),
            'agent_health': await self.check_agent_health(),
            'system_resources': await self.check_system_resources()
        }
        
        # 分析並生成告警
        alerts = self.analyze_health_data(health_data)
        
        # 保存報告
        self.save_health_report(health_data, alerts)
        
        # 打印摘要
        self.print_health_summary(health_data, alerts)
        
        logger.info("健康檢查完成")
        return health_data, alerts
    
    async def run_continuous_monitoring(self):
        """運行持續監控"""
        logger.info(f"開始持續監控，檢查間隔: {self.check_interval}秒")
        
        while True:
            try:
                await self.run_single_check()
                await asyncio.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("監控已停止")
                break
            except Exception as e:
                logger.error(f"監控錯誤: {e}")
                await asyncio.sleep(self.check_interval)


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Rovo Dev 系統健康監控')
    parser.add_argument('--config', default='configs/atlassian_config.yaml', help='配置文件路徑')
    parser.add_argument('--interval', type=int, default=60, help='檢查間隔（秒）')
    parser.add_argument('--once', action='store_true', help='只執行一次檢查')
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(args.config)
    monitor.check_interval = args.interval
    
    if args.once:
        await monitor.run_single_check()
    else:
        await monitor.run_continuous_monitoring()


if __name__ == '__main__':
    asyncio.run(main())