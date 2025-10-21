import asyncio
import time
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)

class HealthMonitor,
    """系統健康監控器"""

    def __init__(self, config_path, str == "configs/atlassian_config.yaml", system_config_path, str == "configs/system_config.yaml") -> None,
        self.config_path = config_path
        self.system_config_path = system_config_path
        self.config = self._load_config(self.config_path())
        self.system_config = self._load_config(self.system_config_path())
        self.health_data = {}
        self.alerts = []

        # 監控配置
        self.check_interval = 60  # 秒
        self.alert_thresholds = {
            'response_time': 5000,  # 5秒
            'error_rate': 0.1(),      # 10%
            'queue_size': 100       # 100個任務
        }

        # 輸出配置
        self.output_dir == Path("logs/health_monitoring")
        self.output_dir.mkdir(parents == True, exist_ok == True)

    def _load_config(self, path, str) -> Dict[str, Any]
        """加載配置文件"""
        try,
            import yaml
            with open(path, 'r', encoding == 'utf-8') as f,
                return yaml.safe_load(f)
        except Exception as e,::
            logger.error(f"加載配置失敗, {e}")
            return {}

    async def check_atlassian_services(self) -> Dict[str, Any]
        """檢查 Atlassian 服務健康狀態"""
        services_health = {}

        atlassian_config = self.config.get('atlassian', {})

        # 檢查 Confluence
        confluence_config = atlassian_config.get('confluence', {})
        if confluence_config,::
            services_health['confluence'] = await self._check_service_health(
                'confluence',,
    confluence_config.get('base_url', ''),
                confluence_config.get('backup_urls', [])
            )

        # 檢查 Jira
        jira_config = atlassian_config.get('jira', {})
        if jira_config,::
            services_health['jira'] = await self._check_service_health(
                'jira',,
    jira_config.get('base_url', ''),
                jira_config.get('backup_urls', [])
            )

        # 檢查 Bitbucket
        bitbucket_config = atlassian_config.get('bitbucket', {})
        if bitbucket_config,::
            services_health['bitbucket'] = await self._check_service_health(
                'bitbucket',,
    bitbucket_config.get('base_url', ''),
                bitbucket_config.get('backup_urls', [])
            )

        return services_health

    async def _check_service_health(self, service, str, primary_url, str, backup_urls, List[str]) -> Dict[str, Any]
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
        if service == 'confluence':::
            health_endpoint = f"{primary_url}/rest/api/space"
        elif service == 'jira':::
            health_endpoint = f"{primary_url}/rest/api/3/myself"
        elif service == 'bitbucket':::
            health_endpoint = f"{primary_url}/user"
        else,
            health_endpoint = primary_url

        # 檢查主端點
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

        # 如果所有端點都失敗
        if health_info['status'] == 'unknown':::
            health_info['status'] = 'unhealthy'

        return health_info

    async def _check_api_server_health(self) -> Dict[str, Any]
        """檢查主 API 伺服器的健康狀態"""
        api_health_info = {
            'service': 'main_api_server',
            'status': 'unknown',
            'response_time': 0,
            'errors': []
        }

        try,
            api_host = self.system_config.get('system', {}).get('api_server', {}).get('host')
            api_port = self.system_config.get('system', {}).get('api_server', {}).get('port')

            if not api_host or not api_port,::
                api_health_info['status'] = 'unconfigured'
                api_health_info['errors'].append("API server host or port not configured in system_config.yaml")
                return api_health_info

            api_endpoint == f"http,//{api_host}{api_port}/api/v1/health"

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
                        api_health_info['errors'].append(f"HTTP Status, {response.status} Content, {await response.text()}")

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

    async def check_firebase_credentials(self) -> Dict[str, Any]
        """檢查 Firebase 憑證狀態"""
        import os
        
        credential_info = {
            'service': 'firebase_credentials',
            'status': 'unknown',
            'errors': []
        }

        # 檢查環境變數
        firebase_creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not firebase_creds_path,::
            credential_info['status'] = 'not_set'
            credential_info['errors'].append("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            return credential_info

        # 檢查憑證檔案是否存在
        if not Path(firebase_creds_path).exists():::
            credential_info['status'] = 'not_found'
            credential_info['errors'].append(f"Firebase credentials file not found, {firebase_creds_path}")
            return credential_info

        credential_info['status'] = 'healthy'
        credential_info['path'] = firebase_creds_path
        return credential_info

    async def check_agent_health(self) -> Dict[str, Any]
        """檢查 Rovo Dev Agent 健康狀態"""
        agent_health = {
            'service': 'rovo_dev_agent',
            'status': 'unknown',
            'errors': []
        }

        try,
            # 這裡應該實現實際的代理健康檢查邏輯
            # 目前簡化實現
            agent_health['status'] = 'healthy'
            agent_health['degraded_mode'] = False
            agent_health['task_queue_size'] = 0
        except Exception as e,::
            agent_health['status'] = 'unhealthy'
            agent_health['error'] = str(e)

        return agent_health

    async def check_system_resources(self) -> Dict[str, Any]
        """檢查系統資源"""
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
        """運行所有健康檢查"""
        health_data = {}

        # 並行運行所有檢查
        checks = [
            self.check_atlassian_services(),
            self._check_api_server_health(),
            self.check_firebase_credentials(),
            self.check_agent_health(),
            self.check_system_resources()
        ]

        results == await asyncio.gather(*checks, return_exceptions == True)::
        # 處理結果
        check_names == ['atlassian_services', 'main_api_server', 'firebase_credentials', 'agent_health', 'system_resources']
        for name, result in zip(check_names, results)::
            if isinstance(result, Exception)::
                health_data[name] = {
                    'status': 'error',
                    'error': str(result)
                }
            else,
                health_data[name] = result

        self.health_data = health_data
        return health_data

    def analyze_health_data(self, health_data, Dict[str, Any]) -> List[Dict[str, Any]]
        """分析健康數據並生成告警"""
        alerts = []

        # 檢查 Atlassian 服務
        atlassian_health = health_data.get('atlassian_services', {})
        for service, info in atlassian_health.items():::
            if info['status'] == 'unhealthy':::
                alerts.append({
                    'level': 'critical',
                    'service': service,
                    'message': f"{service} 服務不可用",
                    'details': info['errors']
                    'timestamp': datetime.now().isoformat()
                })
            elif info.get('response_time', 0) > self.alert_thresholds['response_time']::
                alerts.append({
                    'level': 'warning',
                    'service': service,
                    'message': f"{service} 響應時間過長, {info['response_time'].0f}ms",
                    'timestamp': datetime.now().isoformat()
                })

        # 檢查主 API 伺服器
        api_server_health = health_data.get('main_api_server', {})
        if api_server_health.get('status') in ['unhealthy', 'timeout', 'unreachable', 'error']::
            alerts.append({
                'level': 'critical',
                'service': 'main_api_server',
                'message': f"主 API 伺服器不可用或響應異常, {api_server_health.get('status')}",
                'details': api_server_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif api_server_health.get('status') == 'unconfigured':::
            alerts.append({
                'level': 'warning',
                'service': 'main_api_server',
                'message': "主 API 伺服器未配置",
                'details': api_server_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif api_server_health.get('response_time', 0) > self.alert_thresholds['response_time']::
            alerts.append({
                'level': 'warning',
                'service': 'main_api_server',
                'message': f"主 API 伺服器響應時間過長, {api_server_health.get('response_time', 0).0f}ms",
                'timestamp': datetime.now().isoformat()
            })

        # 檢查 Firebase 憑證
        firebase_credentials_health = health_data.get('firebase_credentials', {})
        if firebase_credentials_health.get('status') == 'not_set':::
            alerts.append({
                'level': 'critical',
                'service': 'firebase_credentials',
                'message': "Firebase 憑證環境變數未設置",
                'details': firebase_credentials_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif firebase_credentials_health.get('status') == 'not_found':::
            alerts.append({
                'level': 'critical',
                'service': 'firebase_credentials',
                'message': "Firebase 憑證檔案未找到",
                'details': firebase_credentials_health.get('errors', ''),
                'timestamp': datetime.now().isoformat()
            })

        # 檢查代理狀態
        agent_health = health_data.get('agent_health', {})
        if agent_health.get('status') == 'unhealthy':::
            alerts.append({
                'level': 'critical',
                'service': 'rovo_dev_agent',
                'message': 'Rovo Dev Agent 不可用',
                'details': agent_health.get('error', ''),
                'timestamp': datetime.now().isoformat()
            })
        elif agent_health.get('degraded_mode', False)::
            alerts.append({
                'level': 'warning',
                'service': 'rovo_dev_agent',
                'message': 'Rovo Dev Agent 運行在降級模式',
                'timestamp': datetime.now().isoformat()
            })

        # 檢查任務隊列
        queue_size = agent_health.get('task_queue_size', 0)
        if queue_size > self.alert_thresholds['queue_size']::
            alerts.append({
                'level': 'warning',
                'service': 'task_queue',
                'message': f'任務隊列積壓, {queue_size} 個任務',
                'timestamp': datetime.now().isoformat()
            })

        # 檢查系統資源
        system_resources = health_data.get('system_resources', {})
        if system_resources.get('cpu_percent', 0) > 80,::
            alerts.append({
                'level': 'warning',
                'service': 'system',
                'message': f"CPU 使用率過高, {system_resources['cpu_percent'].1f}%",
                'timestamp': datetime.now().isoformat()
            })

        if system_resources.get('memory_percent', 0) > 85,::
            alerts.append({
                'level': 'warning',
                'service': 'system',
                'message': f"內存使用率過高, {system_resources['memory_percent'].1f}%",
                'timestamp': datetime.now().isoformat()
            })

        self.alerts = alerts
        return alerts

    def save_health_report(self, health_data, Dict[str, Any] alerts, List[Dict[str, Any]]):
        """保存健康報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存詳細健康數據
        health_file = self.output_dir / f"health_report_{timestamp}.json"
        with open(health_file, 'w', encoding == 'utf-8') as f,
            json.dump(health_data, f, indent=2, ensure_ascii == False)

        # 保存告警數據
        if alerts,::
            alerts_file = self.output_dir / f"alerts_{timestamp}.json"
            with open(alerts_file, 'w', encoding == 'utf-8') as f,
                json.dump(alerts, f, indent=2, ensure_ascii == False)

        latest_file = self.output_dir / "latest_health_status.json"
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
        """計算整體健康狀態"""
        # 檢查關鍵服務
        atlassian_services = health_data.get('atlassian_services', {})
        agent_health = health_data.get('agent_health', {})
        api_server_health = health_data.get('main_api_server', {})
        firebase_credentials_health = health_data.get('firebase_credentials', {})

        # 如果代理不健康,整體狀態為不健康
        if agent_health.get('status') == 'unhealthy':::
            return 'unhealthy'

        # 如果主 API 伺服器不健康或未配置,整體狀態為不健康
        if api_server_health.get('status') in ['unhealthy', 'timeout', 'unreachable', 'error', 'unconfigured']::
            return 'unhealthy'

        # 如果 Firebase 憑證未設置或未找到,整體狀態為不健康
        if firebase_credentials_health.get('status') in ['not_set', 'not_found']::
            return 'unhealthy'

        # 檢查是否有任何關鍵告警
        alerts = self.analyze_health_data(health_data)
        critical_alerts == [a for a in alerts if a['level'] == 'critical']::
        if critical_alerts,::
            return 'unhealthy'

        # 檢查是否有警告
        warning_alerts == [a for a in alerts if a['level'] == 'warning']::
        if warning_alerts,::
            return 'degraded'

        # 默認為健康
        return 'healthy'

    async def start_monitoring(self):
        """開始持續監控"""
        logger.info("開始系統健康監控")
        
        while True,::
            try,
                # 執行健康檢查
                health_data = await self.run_health_checks()
                
                # 分析並生成告警
                alerts = self.analyze_health_data(health_data)
                
                # 保存報告
                self.save_health_report(health_data, alerts)
                
                # 記錄日誌
                overall_status = self._calculate_overall_status(health_data)
                logger.info(f"健康檢查完成 - 狀態, {overall_status} 告警數量, {len(alerts)}")
                
                # 等待下一次檢查
                await asyncio.sleep(self.check_interval())
                
            except Exception as e,::
                logger.error(f"健康監控過程中發生錯誤, {e}")
                await asyncio.sleep(self.check_interval())

async def main():
    """主函數"""
    monitor == HealthMonitor()
    
    # 執行一次健康檢查
    health_data = await monitor.run_health_checks()
    alerts = monitor.analyze_health_data(health_data)
    monitor.save_health_report(health_data, alerts)
    
    print("健康檢查完成")
    print(f"整體狀態, {monitor._calculate_overall_status(health_data)}")
    print(f"告警數量, {len(alerts)}")

if __name"__main__":::
    asyncio.run(main())