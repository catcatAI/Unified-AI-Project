#!/usr/bin/env python3
"""
Angela AI - 完整系统验证测试
测试所有组件和功能
"""

import asyncio
import aiohttp
import json
import subprocess
import os
import sys
from datetime import datetime

class AngelaAISystemTest:
    def __init__(self):
        self.results = []
        self.backend_url = "http://127.0.0.1:8000"
        self.ws_url = "ws://127.0.0.1:8000/ws"
    
    def add_result(self, category, status, message):
        icon = "✅" if status else "❌"
        self.results.append((category, status, f"{icon} {message}"))
        print(f"{icon} [{category}] {message}")
    
    async def test_backend_api(self):
        print("\n" + "=" * 60)
        print("         测试 1: 后端 API 服务")
        print("=" * 60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # 健康检查
                async with session.get(f"{self.backend_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.add_result("API", True, f"健康检查: {data['status']}")
                    else:
                        self.add_result("API", False, f"健康检查失败: {resp.status}")
                
                # 宠物状态
                async with session.get(f"{self.backend_url}/api/v1/pet/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pet_id = data.get("pet_id", "unknown")
                        state = data.get("state", {})
                        self.add_result("API", True, f"宠物 API: {pet_id} - 动画:{state.get('current_animation')}")
                    else:
                        self.add_result("API", False, f"宠物 API 失败: {resp.status}")
                
                # 经济系统
                async with session.get(f"{self.backend_url}/api/v1/economy/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.add_result("API", True, f"经济系统: {data.get('coins', 0)} 金币")
                    else:
                        self.add_result("API", False, f"经济 API 失败: {resp.status}")
                
                # 对话测试 - 使用正确的 API 路径
                async with session.post(f"{self.backend_url}/angela/chat",
                                       json={"message": "你好"}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data.get("response", "")[:50]
                        self.add_result("API", True, f"对话功能: {response}...")
                    elif resp.status == 404:
                        self.add_result("API", False, f"对话 API 返回 404，请检查 /angela/chat 端点")
                    else:
                        self.add_result("API", False, f"对话 API 失败: {resp.status}")
                        
        except Exception as e:
            self.add_result("API", False, f"错误: {str(e)[:60]}")
    
    async def test_websocket(self):
        print("\n" + "=" * 60)
        print("         测试 2: WebSocket 连接")
        print("=" * 60)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.ws_url) as ws:
                    # 等待连接确认
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self.add_result("WebSocket", True, f"连接建立成功")
                            
                            # 发送 ping
                            await ws.send_json({"type": "ping", "timestamp": int(datetime.now().timestamp())})
                            msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                self.add_result("WebSocket", True, f"消息收发正常")
                    except asyncio.TimeoutError:
                        self.add_result("WebSocket", False, "连接超时")
                        
        except Exception as e:
            self.add_result("WebSocket", False, f"错误: {str(e)[:60]}")
    
    def test_frontend_code(self):
        print("\n" + "=" * 60)
        print("         测试 3: 前端代码完整性")
        print("=" * 60)
        
        base_path = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app"
        
        # 检查关键文件
        key_files = {
            "index.html": "主页面",
            "main.js": "Electron 主进程",
            "preload.js": "IPC 预加载",
            "js/app.js": "主应用逻辑",
            "js/live2d-manager.js": "Live2D 管理器",
            "js/input-handler.js": "输入处理器",
            "js/backend-websocket.js": "WebSocket 客户端",
            "js/dialogue-ui.js": "对话框 UI",
            "js/audio-handler.js": "音频处理",
            "js/haptic-handler.js": "触觉反馈",
        }
        
        for filename, desc in key_files.items():
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                self.add_result("代码", True, f"{desc} ({filename}): {size:,} bytes")
            else:
                self.add_result("代码", False, f"缺少 {filename}")
        
        # 检查 index.html 中的关键元素
        index_path = os.path.join(base_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = [
                ('id="live2d-canvas"', "Live2D 画布"),
                ('id="click-layer"', "点击层"),
                ('id="loading-overlay"', "加载遮罩"),
                ('backend-websocket.js', "WebSocket 脚本"),
                ('dialogue-ui.js', "对话框脚本"),
                ('input-handler.js', "输入处理脚本"),
            ]
            
            for pattern, desc in checks:
                if pattern in content:
                    self.add_result("HTML", True, f"包含 {desc}")
                else:
                    self.add_result("HTML", False, f"缺少 {desc}")
    
    def test_dialogue_system(self):
        print("\n" + "=" * 60)
        print("         测试 4: 对话系统")
        print("=" * 60)
        
        dialogue_path = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/dialogue-ui.js"
        
        if not os.path.exists(dialogue_path):
            self.add_result("对话", False, "文件不存在")
            return
        
        with open(dialogue_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = {
            "class DialogueUI": "DialogueUI 类",
            "sendMessage": "发送消息方法",
            "addMessage": "添加消息方法",
            "addSystemMessage": "系统消息方法",
            "dialogue-input": "输入框元素",
            "dialogue-messages": "消息容器元素",
            "addMessage('user'": "用户消息样式",
            "addMessage('angela'": "Angela 消息样式",
        }
        
        for pattern, desc in required_elements.items():
            if pattern in content:
                self.add_result("对话", True, f"{desc}")
            else:
                self.add_result("对话", False, f"缺少 {desc}")
    
    def test_live2d_system(self):
        print("\n" + "=" * 60)
        print("         测试 5: Live2D 系统")
        print("=" * 60)
        
        live2d_path = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/live2d-manager.js"
        
        if not os.path.exists(live2d_path):
            self.add_result("Live2D", False, "文件不存在")
            return
        
        with open(live2d_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = {
            "class Live2DManager": "Live2D 管理器类",
            "loadModel": "模型加载方法",
            "setExpression": "表情设置方法",
            "triggerMotionByPart": "身体部位响应",
            "startAnimation": "动画启动",
            "getClickableRegions": "可点击区域",
            "lookAt": "视线追踪",
            "ParamEyeLOpen": "眼睛参数",
            "ParamMouthOpenY": "嘴巴参数",
            "ParamBrowLY": "眉毛参数",
        }
        
        for pattern, desc in required_elements.items():
            if pattern in content:
                self.add_result("Live2D", True, f"{desc}")
            else:
                self.add_result("Live2D", False, f"缺少 {desc}")
        
        # 检查支持的表达式
        expressions = ["neutral", "happy", "sad", "angry", "surprised", "shy", "love"]
        found_expr = []
        for e in expressions:
            # 检测 "neutral: {" 这样的格式
            if f"'{e}':" in content or f'"{e}":' in content or f"{e}: {{" in content:
                found_expr.append(e)
        self.add_result("Live2D", len(found_expr) >= 5, f"支持 {len(found_expr)} 种表情: {', '.join(found_expr)}")
    
    def test_main_process(self):
        print("\n" + "=" * 60)
        print("         测试 6: Electron 主进程")
        print("=" * 60)
        
        main_path = "/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/main.js"
        
        if not os.path.exists(main_path):
            self.add_result("主进程", False, "文件不存在")
            return
        
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = {
            "requestSingleInstanceLock": "单实例锁",
            "WebSocket": "WebSocket 支持",
            "connectWebSocket": "WebSocket 连接",
            "createMainWindow": "主窗口创建",
            "createTray": "系统托盘",
            "ipcMain": "IPC 通信",
            "live2d-load-model": "Live2D 模型加载",
            "setIgnoreMouseEvents": "鼠标事件处理",
        }
        
        for pattern, desc in required_elements.items():
            if pattern in content:
                self.add_result("主进程", True, f"{desc}")
            else:
                self.add_result("主进程", False, f"缺少 {desc}")
    
    async def run_all_tests(self):
        print("\n" + "=" * 70)
        print("        Angela AI 完整系统验证测试")
        print(f"        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        await self.test_backend_api()
        await self.test_websocket()
        self.test_frontend_code()
        self.test_dialogue_system()
        self.test_live2d_system()
        self.test_main_process()
        
        self.print_summary()
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("                    测试结果汇总")
        print("=" * 70)
        
        categories = {}
        for cat, status, msg in self.results:
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0, "details": []}
            if status:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
            categories[cat]["details"].append((status, msg))
        
        total_passed = sum(c["passed"] for c in categories.values())
        total_failed = sum(c["failed"] for c in categories.values())
        total = total_passed + total_failed
        
        for cat, data in categories.items():
            cat_total = data["passed"] + data["failed"]
            rate = (data["passed"] / cat_total * 100) if cat_total > 0 else 0
            icon = "✅" if data["failed"] == 0 else "⚠️" if data["failed"] < cat_total else "❌"
            print(f"{icon} {cat}: {data['passed']}/{cat_total} 通过 ({rate:.0f}%)")
        
        print("=" * 70)
        print(f"总计: {total_passed}/{total} 测试通过 ({total_passed/total*100:.1f}%)")
        print("=" * 70)
        
        if total_failed > 0:
            print("\n⚠️  发现的失败项目:")
            for cat, data in categories.items():
                for status, msg in data["details"]:
                    if not status:
                        print(f"   - [{cat}] {msg}")
        
        return total_failed == 0

if __name__ == "__main__":
    test = AngelaAISystemTest()
    success = asyncio.run(test.run_all_tests())
    sys.exit(0 if success else 1)
