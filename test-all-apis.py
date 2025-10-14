#!/usr/bin/env python3
"""
测试所有API端点
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_api_endpoints():
    """测试所有API端点"""
    base_url = "http://localhost:8000"
    results = []
    
    async with httpx.AsyncClient() as client:
        # 测试健康检查
        try:
            response = await client.get(f"{base_url}/health")
            results.append({
                "endpoint": "/health",
                "status": response.status_code,
                "success": response.status_code == 200
            })
        except Exception as e:
            results.append({
                "endpoint": "/health",
                "status": "ERROR",
                "success": False,
                "error": str(e)
            })
        
        # 测试API路由
        endpoints = [
            "/api/v1/agents",
            "/api/v1/models",
            "/api/v1/system/metrics/detailed",
            "/api/v1/system/health",
            "/api/v1/images/history",
            "/api/v1/images/statistics"
        ]
        
        for endpoint in endpoints:
            try:
                response = await client.get(f"{base_url}{endpoint}")
                results.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "status": "ERROR",
                    "success": False,
                    "error": str(e)
                })
        
        # 测试POST端点
        post_endpoints = [
            ("/api/v1/chat/completions", {"messages": [{"role": "user", "content": "Hello"}]}),
            ("/api/v1/image", {"prompt": "A beautiful landscape"}),
            ("/api/v1/images/generations", {"prompt": "A cat", "size": "512x512"}),
            ("/api/v1/web/search", {"query": "Python programming"})
        ]
        
        for endpoint, data in post_endpoints:
            try:
                response = await client.post(f"{base_url}{endpoint}", json=data)
                results.append({
                    "endpoint": endpoint,
                    "method": "POST",
                    "status": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "method": "POST",
                    "status": "ERROR",
                    "success": False,
                    "error": str(e)
                })
    
    # 打印结果
    print("\n" + "="*60)
    print("API测试结果")
    print("="*60)
    
    success_count = 0
    for result in results:
        status_icon = "✅" if result["success"] else "❌"
        method = result.get("method", "GET")
        print(f"{status_icon} {method} {result['endpoint']} - {result['status']}")
        if result["success"]:
            success_count += 1
        elif "error" in result:
            print(f"   错误: {result['error']}")
    
    print("\n" + "="*60)
    print(f"总计: {success_count}/{len(results)} 成功")
    print(f"成功率: {(success_count/len(results)*100):.1f}%")
    print("="*60)
    
    # 保存结果
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "success_count": success_count,
            "success_rate": success_count/len(results),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print("\n结果已保存到 api_test_results.json")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())