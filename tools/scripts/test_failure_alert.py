#!/usr/bin/env python3
"""
测试失败告警器 - 当测试失败率过高时发送告警
"""

import json
import smtplib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class TestFailureAlert:
    """测试失败告警器"""

    def __init__(self, config_file: str = None) -> None:
        """初始化告警器"""
        self.config_file = Path(config_file) if config_file else Path(__file__).parent / "alert_config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_addr": "",
                "to_addrs": []
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "headers": {}
            },
            "slack": {
                "enabled": False,
                "webhook_url": ""
            },
            "thresholds": {
                "failure_rate": 0.05,  # 5%失败率阈值
                "consecutive_failures": 3  # 连续失败次数阈值
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和用户配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"⚠️ 加载配置文件失败，使用默认配置: {e}")

        return default_config

    def analyze_test_results(self, test_report_file: str) -> Dict[str, Any]:
        """
        分析测试结果

        Args:
            test_report_file: 测试报告文件路径

        Returns:
            分析结果字典
        """
        try:
            with open(test_report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)

            test_results = report_data.get("test_results", [])
            total_tests = len(test_results)
            failed_tests = [r for r in test_results if not r.get("success", True)]
            failed_count = len(failed_tests)

            failure_rate = failed_count / total_tests if total_tests > 0 else 0

            # 检查连续失败
            consecutive_failures = 0
            for result in reversed(test_results):
                if result.get("success", True):
                    break
                consecutive_failures += 1

            analysis = {
                "total_tests": total_tests,
                "failed_tests": failed_count,
                "failure_rate": failure_rate,
                "consecutive_failures": consecutive_failures,
                "should_alert": False,
                "alert_reasons": []
            }

            # 检查是否需要告警
            if failure_rate > self.config["thresholds"]["failure_rate"]:
                analysis["should_alert"] = True
                analysis["alert_reasons"].append(f"失败率过高: {failure_rate:.2%} > {self.config['thresholds']['failure_rate']:.2%}")

            if consecutive_failures >= self.config["thresholds"]["consecutive_failures"]:
                analysis["should_alert"] = True
                analysis["alert_reasons"].append(f"连续失败次数过多: {consecutive_failures} >= {self.config['thresholds']['consecutive_failures']}")

            return analysis

        except Exception as e:
            print(f"❌ 分析测试结果失败: {e}")
            return {
                "error": str(e),
                "should_alert": True,
                "alert_reasons": ["测试结果分析失败"]
            }

    def send_email_alert(self, analysis: Dict[str, Any], test_report_file: str) -> None:
        """
        发送邮件告警

        Args:
            analysis: 分析结果
            test_report_file: 测试报告文件路径
        """
        if not self.config["email"]["enabled"]:
            return

        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["from_addr"]
            msg['To'] = ", ".join(self.config["email"]["to_addrs"])
            msg['Subject'] = f"🚨 测试失败告警 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # 邮件正文
            body = f"""
测试失败告警通知

分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总测试数: {analysis.get('total_tests', 0)}
失败测试数: {analysis.get('failed_tests', 0)}
失败率: {analysis.get('failure_rate', 0):.2%}
连续失败次数: {analysis.get('consecutive_failures', 0)}

告警原因:
{'\n'.join(analysis.get('alert_reasons', []))}

详细报告请查看附件: {test_report_file}

---
此邮件由自动化测试系统自动发送
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 连接SMTP服务器并发送邮件
            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["username"], self.config["email"]["password"])
            server.send_message(msg)
            server.quit()

            print("📧 邮件告警已发送")

        except Exception as e:
            print(f"❌ 发送邮件告警失败: {e}")

    def send_webhook_alert(self, analysis: Dict[str, Any], test_report_file: str) -> None:
        """
        发送Webhook告警

        Args:
            analysis: 分析结果
            test_report_file: 测试报告文件路径
        """
        if not self.config["webhook"]["enabled"]:
            return

        try:
            # 构造Webhook数据
            payload = {
                "timestamp": datetime.now().isoformat(),
                "event": "test_failure",
                "analysis": analysis,
                "report_file": test_report_file
            }

            # 发送Webhook请求
            response = requests.post(
                self.config["webhook"]["url"],
                json=payload,
                headers=self.config["webhook"]["headers"],
                timeout=30
            )
            
            if response.status_code == 200:
                print("🔗 Webhook告警已发送")
            else:
                print(f"❌ Webhook发送失败: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ 发送Webhook告警失败: {e}")

    def send_slack_alert(self, analysis: Dict[str, Any], test_report_file: str) -> None:
        """
        发送Slack告警

        Args:
            analysis: 分析结果
            test_report_file: 测试报告文件路径
        """
        if not self.config["slack"]["enabled"]:
            return

        try:
            # 构造Slack消息
            payload = {
                "text": "🚨 测试失败告警",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "分析时间",
                                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            },
                            {
                                "title": "总测试数",
                                "value": str(analysis.get('total_tests', 0)),
                                "short": True
                            },
                            {
                                "title": "失败测试数",
                                "value": str(analysis.get('failed_tests', 0)),
                                "short": True
                            },
                            {
                                "title": "失败率",
                                "value": f"{analysis.get('failure_rate', 0):.2%}",
                                "short": True
                            },
                            {
                                "title": "连续失败次数",
                                "value": str(analysis.get('consecutive_failures', 0)),
                                "short": True
                            },
                            {
                                "title": "告警原因",
                                "value": '\n'.join(analysis.get('alert_reasons', [])),
                                "short": False
                            }
                        ]
                    }
                ]
            }

            # 发送Slack消息
            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print("💬 Slack告警已发送")
            else:
                print(f"❌ Slack发送失败: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ 发送Slack告警失败: {e}")

    def process_test_results(self, test_report_file: str) -> bool:
        """
        处理测试结果并根据需要发送告警

        Args:
            test_report_file: 测试报告文件路径

        Returns:
            是否发送了告警
        """
        print("🔍 分析测试结果...")
        
        # 分析测试结果
        analysis = self.analyze_test_results(test_report_file)
        
        if "error" in analysis:
            print("❌ 测试结果分析出错")
            return False
            
        print(f"📊 分析完成 - 总测试: {analysis['total_tests']}, 失败: {analysis['failed_tests']}, 失败率: {analysis['failure_rate']:.2%}")
        
        # 检查是否需要告警
        if analysis["should_alert"]:
            print("🚨 检测到需要告警的情况")
            print("告警原因:")
            for reason in analysis["alert_reasons"]:
                print(f"  - {reason}")
            
            # 发送各种告警
            self.send_email_alert(analysis, test_report_file)
            self.send_webhook_alert(analysis, test_report_file)
            self.send_slack_alert(analysis, test_report_file)
            
            return True
        else:
            print("✅ 测试结果正常，无需告警")
            return False

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="测试失败告警器")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--report", required=True, help="测试报告文件路径")
    
    args = parser.parse_args()
    
    # 创建告警器
    alert = TestFailureAlert(args.config)
    
    # 处理测试结果
    alerted = alert.process_test_results(args.report)
    
    if alerted:
        print("⚠️ 已发送告警通知")
        return 1
    else:
        print("✅ 无告警")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())