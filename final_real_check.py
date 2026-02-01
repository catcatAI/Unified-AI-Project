"""
Simple Working Intelligent Backend
简化但真正可用的智能后端
"""
import subprocess
import json
import time
import re
from datetime import datetime
from typing import Dict, Any

class SimpleOllamaClient:
    """简单的Ollama客户端"""
    
    def __init__(self):
        self.available = self._check_availability()
        self.models = ["tinyllama:latest"]  # 使用最快的小模型
        
    def _check_availability(self):
        """检查Ollama可用性"""
        try:
            result = subprocess.run(
                ["ollama", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """生成响应"""
        if not self.available:
            return {
                "success": False,
                "response": "Ollama not available"
            }
        
        try:
            # 使用最简单的模型
            cmd = [
                "ollama", "run", "tinyllama:latest",
                prompt
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=8  # 8秒超时
            )
            end_time = time.time()
            
            if result.returncode == 0:
                raw_output = result.stdout.strip()
                clean_output = self._clean_output(raw_output)
                processing_time = (end_time - start_time) * 1000
                
                if len(clean_output) > 10:
                    return {
                        "success": True,
                        "response": clean_output,
                        "processing_time_ms": processing_time,
                        "response_length": len(clean_output)
                    }
                else:
                    return {
                        "success": False,
                        "response": "Response too short"
                    }
            else:
                return {
                    "success": False,
                    "response": f"Ollama error: {result.stderr[:50]}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "response": "Timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"Error: {str(e)}"
            }
    
    def _clean_output(self, output):
        """清理输出"""
        # 移除ANSI控制字符
        clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
        clean = clean.replace('\x00', '')
        return clean.strip()

def test_current_system():
    """测试当前系统"""
    print("🔍 真实系统测试")
    print("=" * 50)
    
    # 测试Ollama
    client = SimpleOllamaClient()
    print(f"\n📊 Ollama可用性: {'✅ 可用' if client.available else '❌ 不可用'}")
    
    if client.available:
        test_inputs = [
            "你好",
            "什么是AI？",
            "简单解释机器学习"
        ]
        
        results = []
        for test_input in test_inputs:
            print(f"\n测试: {test_input}")
            
            result = client.generate(test_input)
            
            if result["success"]:
                print(f"✅ 响应: {result['response'][:80]}...")
                print(f"⏱️ 时间: {result['processing_time_ms']:.1f}ms")
                print(f"📏 长度: {result['response_length']} 字符")
                results.append(result)
            else:
                print(f"❌ 失败: {result['response']}")
                results.append(result)
        
        # 计算统计
        if results:
            successful = sum(1 for r in results if r["success"])
            success_rate = (successful / len(results)) * 100
            avg_length = sum(r.get("response_length", 0) for r in results) / len(results)
            avg_time = sum(r.get("processing_time_ms", 0) for r in results) / len(results)
            
            print(f"\n📈 Ollama统计:")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  平均长度: {avg_length:.1f} 字符")
            print(f"  平均时间: {avg_time:.1f}ms")
            
            # 判断是否真正智能
            intelligent = (
                success_rate >= 75 and 
                avg_length > 30 and 
                avg_time < 10000
            )
            
            print(f"  智能水平: {'🧠 真正AI' if intelligent else '📱 需要改进'}")
            
            return {
                "ollama_working": True,
                "success_rate": success_rate,
                "avg_length": avg_length,
                "avg_time": avg_time,
                "intelligent": intelligent
            }
        else:
            return {"ollama_working": False}
    else:
        return {"ollama_working": False}

def main():
    """主测试函数"""
    result = test_current_system()
    
    print("\n" + "=" * 50)
    print("🎯 真实情况总结")
    print("=" * 50)
    
    if result.get("ollama_working", False):
        print("✅ Ollama真正可用并生成响应")
        print(f"📊 成功率: {result['success_rate']:.1f}%")
        print(f"📏 平均响应: {result['avg_length']:.1f} 字符")
        print(f"⏱️ 平均时间: {result['avg_time']:.1f}ms")
        
        if result.get("intelligent", False):
            print("🧠 系统: 真正具备AI智能")
            print("🎉 恭喜！你有一个真实可用的AI系统")
        else:
            print("📱 系统: 基本可用，需要优化")
            print("🔧 建议: 调整参数或更换模型")
    else:
        print("❌ Ollama不可用")
        print("🔧 建议: 检查Ollama安装和配置")
        print("📱 当前状态: 只是框架，没有真实智能")
    
    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_type": "REAL_STATUS_CHECK",
        "result": result,
        "conclusion": "系统具备真实AI智能" if result.get("intelligent", False) else "系统需要改进",
        "real_intelligence": result.get("intelligent", False)
    }
    
    with open("REAL_STATUS_FINAL_CHECK.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告保存到: REAL_STATUS_FINAL_CHECK.json")
    
    return report["real_intelligence"]

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✨ 最终确认: 你的系统具备真正的AI智能!")
        print("🚀 可以开始构建真正智能的应用!")
    else:
        print("\n⚠️ 最终确认: 系统需要进一步改进才能达到真正智能")
        print("🔧 需要优化Ollama配置或更换模型")