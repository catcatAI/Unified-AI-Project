# 🤖 多模型 LLM API 參考文檔

## 📋 概述

本文檔詳細描述多模型 LLM 服務的 API 接口，包括請求格式、響應結構、錯誤處理和使用示例。

---

## 🔗 基礎信息

### API 基礎 URL

```
http://localhost:8000/api/llm
```

### 認證方式

- **API Key**: 通過 `X-API-Key` 標頭傳遞
- **Bearer Token**: 通過 `Authorization: Bearer <token>` 標頭傳遞

### 內容類型

- **請求**: `application/json`
- **響應**: `application/json` 或 `text/event-stream` (流式)

---

## 🚀 核心 API 端點

### 1. 文本生成 API

#### POST `/generate`

生成文本響應的主要端點。

**請求格式**:

```json
{
  "model": "gemini-pro",
  "messages": [
    {
      "role": "user",
      "content": "你好，請介紹一下人工智能"
    }
  ],
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9,
    "stream": false
  }
}
```

**響應格式**:

```json
{
  "id": "req_12345",
  "model": "gemini-pro",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "人工智能（AI）是計算機科學的一個分支..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 150,
    "total_tokens": 165
  },
  "cost": {
    "input_cost": 0.0001,
    "output_cost": 0.0003,
    "total_cost": 0.0004
  }
}
```

### 2. 流式生成 API

#### POST `/generate/stream`

支持實時流式輸出的文本生成。

**請求格式**:

```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "寫一個關於春天的詩"
    }
  ],
  "parameters": {
    "temperature": 0.8,
    "max_tokens": 500,
    "stream": true
  }
}
```

**響應格式** (Server-Sent Events):

```
data: {"id":"stream_123","choices":[{"delta":{"content":"春"}}]}

data: {"id":"stream_123","choices":[{"delta":{"content":"天"}}]}

data: {"id":"stream_123","choices":[{"delta":{"content":"來"}}]}

data: [DONE]
```

### 3. 模型管理 API

#### GET `/models`

獲取可用模型列表。

**響應格式**:

```json
{
  "models": [
    {
      "id": "gemini-pro",
      "name": "Google Gemini Pro",
      "provider": "google",
      "type": "text",
      "status": "available",
      "capabilities": ["text-generation", "conversation"],
      "limits": {
        "max_tokens": 32768,
        "context_window": 32768
      },
      "pricing": {
        "input_per_1k_tokens": 0.0005,
        "output_per_1k_tokens": 0.0015
      }
    }
  ]
}
```

#### GET `/models/{model_id}/status`

檢查特定模型的狀態。

**響應格式**:

```json
{
  "model_id": "gpt-4",
  "status": "available",
  "health": "healthy",
  "response_time_ms": 1250,
  "last_check": "2025-01-01T12:00:00Z",
  "error_rate": 0.02
}
```

### 4. 健康檢查 API

#### GET `/health`

檢查服務整體健康狀況。

**響應格式**:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "services": {
    "llm_service": "healthy",
    "model_manager": "healthy",
    "cost_tracker": "healthy"
  },
  "models": {
    "available": 7,
    "healthy": 6,
    "degraded": 1,
    "unavailable": 0
  }
}
```

---

## 📊 統計和監控 API

### 1. 使用統計

#### GET `/stats/usage`

獲取使用統計信息。

**查詢參數**:

- `start_date`: 開始日期 (YYYY-MM-DD)
- `end_date`: 結束日期 (YYYY-MM-DD)
- `model`: 特定模型 (可選)

**響應格式**:

```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "total_requests": 15420,
  "total_tokens": 2847392,
  "total_cost": 45.67,
  "by_model": {
    "gemini-pro": {
      "requests": 8500,
      "tokens": 1547392,
      "cost": 23.45
    },
    "gpt-4": {
      "requests": 3200,
      "tokens": 847392,
      "cost": 18.92
    }
  }
}
```

### 2. 性能指標

#### GET `/stats/performance`

獲取性能指標。

**響應格式**:

```json
{
  "response_times": {
    "average_ms": 1850,
    "p50_ms": 1200,
    "p95_ms": 3500,
    "p99_ms": 5200
  },
  "success_rate": 0.987,
  "error_rate": 0.013,
  "throughput": {
    "requests_per_minute": 45,
    "tokens_per_minute": 12500
  }
}
```

---

## 🔧 配置 API

### 1. 模型配置

#### PUT `/config/models/{model_id}`

更新模型配置。

**請求格式**:

```json
{
  "enabled": true,
  "priority": 1,
  "rate_limit": {
    "requests_per_minute": 60,
    "tokens_per_minute": 10000
  },
  "fallback_models": ["gemini-pro", "gpt-3.5-turbo"],
  "parameters": {
    "default_temperature": 0.7,
    "max_tokens": 2000
  }
}
```

### 2. 負載均衡配置

#### PUT `/config/load-balancing`

配置負載均衡策略。

**請求格式**:

```json
{
  "strategy": "round_robin",
  "health_check_interval": 30,
  "failure_threshold": 3,
  "recovery_threshold": 2,
  "weights": {
    "gemini-pro": 0.4,
    "gpt-4": 0.3,
    "claude-3": 0.3
  }
}
```

---

## ❌ 錯誤處理

### 錯誤響應格式

```json
{
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "The requested model is currently unavailable",
    "details": {
      "model": "gpt-4",
      "reason": "rate_limit_exceeded",
      "retry_after": 60
    },
    "request_id": "req_12345"
  }
}
```

### 常見錯誤代碼

| 錯誤代碼              | HTTP 狀態 | 描述           |
| --------------------- | --------- | -------------- |
| `INVALID_REQUEST`     | 400       | 請求格式錯誤   |
| `UNAUTHORIZED`        | 401       | 認證失敗       |
| `MODEL_NOT_FOUND`     | 404       | 模型不存在     |
| `MODEL_UNAVAILABLE`   | 503       | 模型暫時不可用 |
| `RATE_LIMIT_EXCEEDED` | 429       | 超出速率限制   |
| `INTERNAL_ERROR`      | 500       | 內部服務錯誤   |

---

## 🔐 認證和授權

### API Key 認證

```bash
curl -X POST "http://localhost:8000/api/llm/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-pro",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Bearer Token 認證

```bash
curl -X POST "http://localhost:8000/api/llm/generate" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## 📝 使用示例

### Python 客戶端示例

```python
import requests
import json

class LLMClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }

    def generate(self, model, messages, **kwargs):
        payload = {
            'model': model,
            'messages': messages,
            'parameters': kwargs
        }

        response = requests.post(
            f"{self.base_url}/generate",
            headers=self.headers,
            json=payload
        )

        return response.json()

    def stream_generate(self, model, messages, **kwargs):
        payload = {
            'model': model,
            'messages': messages,
            'parameters': {**kwargs, 'stream': True}
        }

        response = requests.post(
            f"{self.base_url}/generate/stream",
            headers=self.headers,
            json=payload,
            stream=True
        )

        for line in response.iter_lines():
            if line.startswith(b'data: '):
                data = line[6:].decode('utf-8')
                if data != '[DONE]':
                    yield json.loads(data)

# 使用示例
client = LLMClient('http://localhost:8000/api/llm', 'your-api-key')

# 普通生成
result = client.generate(
    model='gemini-pro',
    messages=[{'role': 'user', 'content': '你好'}],
    temperature=0.7,
    max_tokens=100
)

print(result['choices'][0]['message']['content'])

# 流式生成
for chunk in client.stream_generate(
    model='gpt-4',
    messages=[{'role': 'user', 'content': '寫一首詩'}],
    temperature=0.8
):
    if 'choices' in chunk and chunk['choices']:
        delta = chunk['choices'][0].get('delta', {})
        if 'content' in delta:
            print(delta['content'], end='', flush=True)
```

### JavaScript 客戶端示例

```javascript
class LLMClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl
    this.apiKey = apiKey
  }

  async generate(model, messages, parameters = {}) {
    const response = await fetch(`${this.baseUrl}/generate`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages,
        parameters,
      }),
    })

    return await response.json()
  }

  async *streamGenerate(model, messages, parameters = {}) {
    const response = await fetch(`${this.baseUrl}/generate/stream`, {
      method: 'POST',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages,
        parameters: { ...parameters, stream: true },
      }),
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data !== '[DONE]') {
            yield JSON.parse(data)
          }
        }
      }
    }
  }
}

// 使用示例
const client = new LLMClient('http://localhost:8000/api/llm', 'your-api-key')

// 普通生成
const result = await client.generate(
  'gemini-pro',
  [{ role: 'user', content: '你好' }],
  { temperature: 0.7, max_tokens: 100 }
)

console.log(result.choices[0].message.content)

// 流式生成
for await (const chunk of client.streamGenerate(
  'gpt-4',
  [{ role: 'user', content: '寫一首詩' }],
  { temperature: 0.8 }
)) {
  if (chunk.choices && chunk.choices[0].delta.content) {
    process.stdout.write(chunk.choices[0].delta.content)
  }
}
```

---

## 🔄 版本控制

### API 版本

- **當前版本**: v1
- **版本格式**: `/api/v1/llm/...`
- **向後兼容**: 支持舊版本 API

### 版本更新策略

- **主版本**: 破壞性變更
- **次版本**: 新功能添加
- **修訂版本**: 錯誤修復

---

## 📚 相關文檔

- [多模型 LLM 服務概述](../ai-components/multi-llm-service.md)
- [配置指南](../ai-components/multi-llm-service.md)
- [部署指南](../../../README.md) <!-- 待更新为具体的部署文档 -->
- [故障排除](../../05-development/debugging/troubleshooting.md)

---

_文檔版本: 1.0_  
_最後更新: 2025年8月_  
_維護者: Unified AI Project 團隊_
