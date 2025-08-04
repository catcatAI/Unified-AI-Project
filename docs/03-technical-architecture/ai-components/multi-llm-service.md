# 多模型 LLM 服务

## 概述

多模型 LLM 服务是一个统一的接口，支持多种主流 AI 大模型，包括：

- **OpenAI GPT** (GPT-4, GPT-3.5-turbo)
- **Google Gemini** (Gemini Pro, Gemini Pro Vision)
- **Anthropic Claude** (Claude-3 Opus, Sonnet, Haiku)
- **Ollama** (本地模型：Llama2, CodeLlama, Mistral 等)
- **Azure OpenAI** (企业级 GPT 服务)
- **Cohere** (Command 系列)
- **Hugging Face** (开源模型)

## 核心职责与功能

1.  **统一的 LLM 接口**:
    *   为所有支持的 LLM 提供商提供一致的 `chat_completion` 和 `stream_completion` 方法。
    *   抽象化了提供商特定的 API 调用、消息格式和响应结构。

2.  **多提供商支持**:
    *   集成了广泛的商业和开源 LLM 提供商，使 AI 能够为特定任务或上下文选择最合适的模型。
    *   支持的提供商包括 OpenAI、Google Gemini、Anthropic Claude、Ollama (本地模型)、Azure OpenAI、Cohere 和 Hugging Face。

3.  **灵活的模型配置**:
    *   从外部 JSON 文件 (例如 `configs/multi_llm_config.json`) 加载模型配置。
    *   配置包括 `model_name`、`api_key` (从环境变量加载)、`max_tokens`、`temperature`、`top_p`、`cost_per_1k_tokens` 和 `enabled` 状态。

4.  **使用统计和成本追踪**:
    *   跟踪每个模型的详细使用统计，包括 `total_requests`、`total_tokens` (提示和完成)、`total_cost`、`average_latency` 和 `error_count`。
    *   实现不同 LLM 之间的成本优化和性能监控。

5.  **健康检查**:
    *   提供 `health_check` 方法，通过发送简单的测试消息来验证已配置 LLM 的可用性和响应能力。

6.  **异步操作**:
    *   与 LLM 的所有交互都是异步的，确保非阻塞操作和并发请求的高效处理。

7.  **全局实例管理**:
    *   管理 `MultiLLMService` 的全局单例实例，以确保应用程序中一致的访问和资源管理。

## 📊 监控和统计

- **使用统计**: 详细的 token 使用和成本统计
- **性能监控**: 延迟、错误率等性能指标
- **使用历史**: 完整的使用历史记录

## 🔧 配置管理

- **灵活配置**: JSON 配置文件支持
- **环境变量**: 安全的 API 密钥管理
- **动态配置**: 运行时配置更新

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的 API 密钥：
```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Google Gemini
GEMINI_API_KEY=your-gemini-key

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# 其他服务...
```

### 3. 使用 CLI 工具

#### 列出可用模型
```bash
python scripts/ai_models.py list
```

#### 单次查询
```bash
python scripts/ai_models.py query "你好，请介绍一下自己" --model gpt-4
```

#### 进入聊天模式
```bash
python scripts/ai_models.py chat --model gemini-pro --stream
```

#### 健康检查
```bash
python scripts/ai_models.py health
```

#### 比较模型
```bash
python scripts/ai_models.py compare "解释量子计算" --models gpt-4 claude-3-sonnet gemini-pro
```

## 编程接口

### 基本用法

```python
import asyncio
from src.services.multi_llm_service import MultiLLMService, ChatMessage

async def main():
    # 初始化服务
    service = MultiLLMService('configs/multi_llm_config.json')
    
    # 创建消息
    messages = [
        ChatMessage(role="system", content="你是一个有用的AI助手"),
        ChatMessage(role="user", content="你好！")
    ]
    
    # 发送请求
    response = await service.chat_completion(messages, model_id="gpt-4")
    print(response.content)
    
    # 关闭服务
    await service.close()

asyncio.run(main())
```

### 流式响应

```python
async def stream_example():
    service = MultiLLMService('configs/multi_llm_config.json')
    
    messages = [ChatMessage(role="user", content="写一首关于AI的诗")]
    
    async for chunk in service.stream_completion(messages, model_id="claude-3-sonnet"):
        print(chunk, end="", flush=True)
    
    await service.close()
```

### 模型比较

```python
async def compare_models():
    service = MultiLLMService('configs/multi_llm_config.json')
    
    query = "解释机器学习的基本概念"
    models = ["gpt-4", "claude-3-sonnet", "gemini-pro"]
    
    for model in models:
        messages = [ChatMessage(role="user", content=query)]
        response = await service.chat_completion(messages, model_id=model)
        
        print(f"\n{model}:")
        print(response.content)
        print(f"成本: ${response.cost:.4f}, 延迟: {response.latency:.2f}s")
    
    await service.close()
```

## 配置文件

### 模型配置 (configs/multi_llm_config.json)

```json
{
  "default_model": "gpt-4",
  "models": {
    "gpt-4": {
      "provider": "openai",
      "model_name": "gpt-4",
      "api_key_env": "OPENAI_API_KEY",
      "max_tokens": 8192,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.03,
      "enabled": true
    },
    "gemini-pro": {
      "provider": "google",
      "model_name": "gemini-pro",
      "api_key_env": "GEMINI_API_KEY",
      "max_tokens": 8192,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.0005,
      "enabled": true
    }
  }
}
```

## 支持的模型

### OpenAI
- `gpt-4`: 最强大的 GPT 模型
- `gpt-3.5-turbo`: 快速且经济的选择

### Google Gemini
- `gemini-pro`: 多模态大模型
- `gemini-pro-vision`: 支持图像理解

### Anthropic Claude
- `claude-3-opus`: 最强大的 Claude 模型
- `claude-3-sonnet`: 平衡性能和成本
- `claude-3-haiku`: 快速响应

### Ollama (本地模型)
- `llama2-7b/13b`: Meta 的开源模型
- `codellama`: 专门用于代码生成
- `mistral-7b`: 高效的开源模型

### 其他
- `azure-gpt-4`: Azure OpenAI 服务
- `cohere-command`: Cohere 的对话模型
- `huggingface-llama`: Hugging Face 托管模型

## 最佳实践

### 1. 模型选择
- **创意写作**: Claude-3 Opus, GPT-4
- **代码生成**: CodeLlama, GPT-4
- **快速问答**: GPT-3.5-turbo, Claude-3 Haiku
- **多语言**: Gemini Pro
- **本地部署**: Ollama 模型

### 2. 成本优化
- 使用更便宜的模型进行简单任务
- 设置合理的 max_tokens 限制
- 监控使用统计，优化模型选择

### 3. 性能优化
- 使用流式响应提升用户体验
- 实施缓存机制减少重复请求
- 配置负载均衡分散请求

### 4. 错误处理
- 配置备用模型链
- 实施重试机制
- 监控模型健康状态

## 故障排除

### 常见问题

1. **API 密钥错误**
   - 检查 `.env` 文件中的密钥是否正确
   - 确认密钥有足够的权限和余额

2. **模型不可用**
   - 运行健康检查: `python scripts/ai_models.py health`
   - 检查网络连接和防火墙设置

3. **Ollama 连接失败**
   - 确认 Ollama 服务正在运行
   - 检查 `OLLAMA_BASE_URL` 配置

4. **依赖安装问题**
   - 使用虚拟环境: `python -m venv venv`
   - 更新 pip: `pip install --upgrade pip`

### 日志和调试

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看使用统计：
```bash
python scripts/ai_models.py stats
```

## 扩展开发

### 添加新的模型提供商

1. 继承 `BaseLLMProvider` 类
2. 实现 `chat_completion` 和 `stream_completion` 方法
3. 在 `MultiLLMService._create_provider` 中注册
4. 更新配置文件和文档

### 自定义功能

- 实现自定义的消息预处理
- 添加特定领域的提示模板
- 集成外部工具和插件

## 相关文档

- [API 参考](../api/multi-llm-api.md)
- [配置指南](../configuration/llm-config.md)
- [部署指南](../deployment/llm-deployment.md)