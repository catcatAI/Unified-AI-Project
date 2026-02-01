#!/usr/bin/env python3
"""
格式一致性检查工具
验证所有API端点是否返回统一的JSON格式
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# 添加项目路径
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FormatConsistencyChecker:
    """格式一致性检查器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.issues = []
        self.test_count = 0
        self.pass_count = 0
        self.warning_count = 0
        self.fail_count = 0
        
    def check_response_format(self, response_data: Dict[str, Any], test_name: str, expected_fields: List[str] = None) -> Dict[str, Any]:
        """检查响应格式一致性"""
        self.test_count += 1
        
        issues = []
        
        # 检查基本响应结构
        if not isinstance(response_data, dict):
            issues.append(f"Response is not a dictionary object")
            self.fail_count += 1
            return {"status": "FAIL", "issues": issues}
        
        # 检查必需字段
        if expected_fields:
            for field in expected_fields:
                if field not in response_data:
                    issues.append(f"Missing required field: {field}")
        
        # 检查数据类型一致性
        for key, value in response_data.items():
            if value is None:
                issues.append(f"Field '{key}' has null value")
        
        if issues:
            self.fail_count += 1
            return {"status": "FAIL", "issues": issues}
        else:
            self.pass_count += 1
            return {"status": "PASS", "issues": []}
    
    def test_api_endpoint(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None, expected_fields: List[str] = None) -> Dict[str, Any]:
        """测试API端点格式一致性"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                return {"status": "FAIL", "issues": [f"Unsupported method: {method}"]}
            
            # 检查HTTP状态码
            if response.status_code != 200:
                return {
                    "status": "FAIL", 
                    "issues": [f"HTTP {response.status_code}: {response.text}"]
                }
            
            # 检查JSON格式
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                return {"status": "FAIL", "issues": ["Invalid JSON response"]}
            
            # 检查响应格式一致性
            format_check = self.check_response_format(response_data, endpoint, expected_fields)
            return format_check
            
        except requests.RequestException as e:
            return {"status": "FAIL", "issues": [f"Request failed: {str(e)}"]}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行综合格式一致性测试"""
        logger.info("开始格式一致性检查...")
        
        test_cases = [
            {
                "endpoint": "/api/v1/chat/conversation",
                "method": "POST",
                "data": {"message": "Hello", "user_id": "test_user"},
                "expected_fields": ["response", "session_id"]
            },
            {
                "endpoint": "/api/v1/memory/store",
                "method": "POST", 
                "data": {"content": "Test memory", "user_id": "test_user"},
                "expected_fields": ["status", "memory_id"]
            },
            {
                "endpoint": "/api/v1/agents",
                "method": "GET",
                "expected_fields": ["agents"]
            },
            {
                "endpoint": "/api/v1/pet/status",
                "method": "GET",
                "expected_fields": ["pet_name", "needs", "emotions"]
            },
            {
                "endpoint": "/api/v1/economy/balance",
                "method": "POST",
                "data": {"user_id": "test_user"},
                "expected_fields": ["balance"]
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            logger.info(f"Testing {test_case['endpoint']}...")
            result = self.test_api_endpoint(**test_case)
            results.append({
                "endpoint": test_case["endpoint"],
                "result": result
            })
        
        # 生成报告
        report = {
            "total_tests": self.test_count,
            "passed": self.pass_count,
            "failed": self.fail_count,
            "warnings": self.warning_count,
            "success_rate": (self.pass_count / self.test_count * 100) if self.test_count > 0 else 0,
            "results": results
        }
        
        logger.info(f"格式一致性检查完成: {self.pass_count}/{self.test_count} 通过 ({report['success_rate']:.1f}%)")
        
        return report

def main():
    """主函数"""
    checker = FormatConsistencyChecker()
    report = checker.run_comprehensive_test()
    
    print("\n" + "="*60)
    print("🔍 FORMAT CONSISTENCY REPORT")
    print("="*60)
    print(f"总测试数: {report['total_tests']}")
    print(f"通过: {report['passed']}")
    print(f"失败: {report['failed']}")
    print(f"成功率: {report['success_rate']:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    for result in report["results"]:
        endpoint = result["endpoint"]
        status = result["result"]["status"]
        issues = result["result"]["issues"]
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {endpoint}")
        
        if issues:
            for issue in issues:
                print(f"   - {issue}")
    
    print("\n" + "="*60)
    
    if report["success_rate"] == 100:
        print("🎉 所有API端点格式一致性检查通过！")
        return 0
    else:
        print("⚠️ 发现格式一致性问题，需要修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())