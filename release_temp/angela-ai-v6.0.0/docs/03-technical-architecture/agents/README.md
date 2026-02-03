# AI Agent System Overview

## 概述

Unified AI Project的AI代理系统是一个模块化的多代理架构，基于[BaseAgent](base-agent.md)类构建。每个代理都是专门化的子代理，负责处理特定类型的任务，通过HSP（异构服务协议）进行通信和协作。

## 代理架构

### BaseAgent 基础类

所有专门化代理都继承自[BaseAgent](base-agent.md)类，该类提供了：

- HSP网络连接和能力广告
- 任务处理和生命周期管理
- 代理协作、监控和注册功能
- 任务队列和重试机制

### 专门化代理

#### 1. Creative Writing Agent
- **文件**: [creative_writing_agent.py](../../../apps/backend/src/agents/creative_writing_agent.py)
- **文档**: [creative-writing-agent.md](creative-writing-agent.md)
- **功能**: 创意写作任务，如生成营销文案、润色文本

#### 2. Image Generation Agent
- **文件**: [image_generation_agent.py](../../../apps/backend/src/agents/image_generation_agent.py)
- **文档**: [image-generation-agent.md](image-generation-agent.md)
- **功能**: 根据文本提示生成图像

#### 3. Web Search Agent
- **文件**: [web_search_agent.py](../../../apps/backend/src/agents/web_search_agent.py)
- **文档**: [web-search-agent.md](web-search-agent.md)
- **功能**: 网络搜索和信息检索

#### 4. Data Analysis Agent
- **文件**: [data_analysis_agent.py](../../../apps/backend/src/agents/data_analysis_agent.py)
- **功能**: 数据统计分析和处理

#### 5. Code Understanding Agent
- **文件**: [code_understanding_agent.py](../../../apps/backend/src/agents/code_understanding_agent.py)
- **功能**: 代码分析、文档生成和代码审查

#### 6. Audio Processing Agent
- **文件**: [audio_processing_agent.py](../../../apps/backend/src/agents/audio_processing_agent.py)
- **功能**: 语音识别、音频分类和音频增强

#### 7. Vision Processing Agent
- **文件**: [vision_processing_agent.py](../../../apps/backend/src/agents/vision_processing_agent.py)
- **功能**: 图像分类、物体检测和图像增强

#### 8. Knowledge Graph Agent
- **文件**: [knowledge_graph_agent.py](../../../apps/backend/src/agents/knowledge_graph_agent.py)
- **功能**: 实体链接、关系提取和知识图谱查询

## 代理协作

代理系统支持以下协作模式：

1. **任务委托**: 一个代理可以将任务委托给具有相应能力的其他代理
2. **能力发现**: 通过HSP网络自动发现和调用其他代理的能力
3. **状态监控**: 实时监控代理的健康状态和性能指标
4. **动态注册**: 支持代理的动态注册和发现

## 使用示例

### 启动代理

```python
from agents.creative_writing_agent import CreativeWritingAgent
import asyncio

async def main():
    agent = CreativeWritingAgent(agent_id="creative_writer_1")
    await agent.start()

asyncio.run(main())
```

### 调用代理能力

通过HSP网络调用代理能力：

```python
# 发送任务请求到Creative Writing Agent
task_payload = {
    "request_id": "req_123",
    "capability_id_filter": "creative_writer_1_generate_marketing_copy_v1.0",
    "parameters": {
        "product_description": "智能AI助手",
        "target_audience": "开发者",
        "style": "专业"
    }
}
```

## 扩展代理

要创建新的专门化代理：

1. 继承[BaseAgent](base-agent.md)类
2. 定义代理的能力
3. 实现`handle_task_request`方法
4. 注册代理到HSP网络

## 性能和监控

代理系统包含以下监控功能：

- 实时健康检查
- 性能指标收集
- 任务处理统计
- 错误日志记录

---
*最后更新: 2025年9月21日*
*维护者: Unified AI Project Team*