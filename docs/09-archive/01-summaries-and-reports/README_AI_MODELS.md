# 🤖 AI 大模型集成指南

## 概述

本项目现已集成多种主流 AI 大模型服务，提供统一的接口和便捷的命令行工具。

## 🚀 支持的 AI 模型

### 商业模型

- **OpenAI GPT-4/3.5** - 最强大的通用语言模型
- **Google Gemini Pro** - 多模态大模型，支持文本和图像
- **Anthropic Claude-3** - 安全可靠的对话模型
- **Azure OpenAI** - 企业级 GPT 服务
- **Cohere Command** - 专业的企业级模型

### 开源/本地模型

- **Ollama** - 本地运行的开源模型
  - Llama2 (7B/13B)
  - CodeLlama (代码生成)
  - Mistral 7B
  - 更多模型...
- **Hugging Face** - 开源模型托管平台

## 📦 快速安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加你的 API 密钥
# OPENAI_API_KEY=sk-your-openai-key
# GEMINI_API_KEY=your-gemini-key
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

## 🔧 使用方法

### 命令行工具

#### 列出所有可用模型

```bash
python scripts/ai_models.py list
```

#### 单次查询

```bash
# 使用 GPT-4
python scripts/ai_models.py query "你好，请介绍一下自己" --model gpt-4

# 使用 Gemini Pro
python scripts/ai_models.py query "解释量子计算" --model gemini-pro --verbose
```

#### 进入聊天模式

```bash
# 流式聊天
python scripts/ai_models.py chat --model claude-3-sonnet --stream

# 带系统提示的聊天
python scripts/ai_models.py chat --model gpt-4 --system "你是一个专业的编程助手"
```

#### 比较多个模型

```bash
python scripts/ai_models.py compare "写一首关于AI的诗" --models gpt-4 claude-3-sonnet gemini-pro
```

#### 健康检查

```bash
python scripts/ai_models.py health
```

#### 查看使用统计

```bash
python scripts/ai_models.py stats
```

### 编程接口

```python
import asyncio
from src.services.multi_llm_service import MultiLLMService, ChatMessage

async def example():
    # 初始化服务
    service = MultiLLMService('configs/multi_llm_config.json')

    # 创建消息
    messages = [
        ChatMessage(role="system", content="你是一个有用的AI助手"),
        ChatMessage(role="user", content="你好！")
    ]

    # 发送请求
    response = await service.chat_completion(messages, model_id="gpt-4")
    print(f"回复: {response.content}")
    print(f"成本: ${response.cost:.4f}")
    print(f"延迟: {response.latency:.2f}s")

    # 流式响应
    async for chunk in service.stream_completion(messages, model_id="claude-3-sonnet"):
        print(chunk, end="", flush=True)

    await service.close()

asyncio.run(example())
```

## 🎯 模型选择建议

### 按用途选择

- **创意写作**: Claude-3 Opus, GPT-4
- **代码生成**: CodeLlama, GPT-4
- **快速问答**: GPT-3.5-turbo, Claude-3 Haiku
- **多语言支持**: Gemini Pro
- **本地部署**: Ollama 模型
- **企业应用**: Azure OpenAI

### 按成本选择

- **最经济**: Ollama 本地模型 (免费)
- **性价比高**: GPT-3.5-turbo, Claude-3 Haiku
- **高质量**: GPT-4, Claude-3 Opus

## 🔐 安全配置

### API 密钥管理

- 使用 `.env` 文件存储密钥
- 不要将密钥提交到版本控制
- 定期轮换 API 密钥

### 成本控制

- 设置合理的 `max_tokens` 限制
- 监控使用统计
- 使用便宜的模型进行测试

## 🛠️ 高级功能

### 负载均衡

```json
{
  "fallback_chain": ["gpt-4", "claude-3-sonnet", "gemini-pro", "llama2-7b"]
}
```

### 速率限制

```json
{
  "rate_limiting": {
    "enabled": true,
    "requests_per_minute": {
      "openai": 60,
      "anthropic": 50
    }
  }
}
```

### 自定义配置

编辑 `configs/multi_llm_config.json` 来：

- 添加新模型
- 调整参数
- 启用/禁用模型

## 🔧 故障排除

### 常见问题

1. **API 密钥错误**

   ```bash
   # 检查密钥配置
   python scripts/ai_models.py health
   ```

2. **Ollama 连接失败**

   ```bash
   # 启动 Ollama 服务
   ollama serve

   # 拉取模型
   ollama pull llama2:7b
   ```

3. **依赖安装问题**
   ```bash
   # 使用虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows

   pip install -r requirements.txt
   ```

### 调试模式

```bash
# 启用详细日志
python scripts/ai_models.py query "test" --model gpt-4 --verbose
```

## 📚 更多资源

- [详细文档](../03-technical-architecture/ai-components/multi-llm-service.md)
- [API 参考](../03-technical-architecture/api/multi-llm-api.md)
- [配置指南](../03-technical-architecture/ai-components/multi-llm-service.md)

## 🤝 贡献

欢迎贡献新的模型提供商或功能改进！

### 添加新模型

1. 继承 `BaseLLMProvider` 类
2. 实现必要的方法
3. 更新配置文件
4. 添加测试

## 📄 许可证

MIT License - 详见 LICENSE 文件
